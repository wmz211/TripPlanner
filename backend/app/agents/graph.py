"""
LangGraph 多智能体旅行规划图

架构：
  ┌─────────────────────────────┐
  │         START               │
  └──────────────┬──────────────┘
                 │ fan_out
     ┌───────────┼───────────┐
     ▼           ▼           ▼
[attraction] [weather]  [hotel]   ← 三个Agent并行执行
     └───────────┼───────────┘
                 │ fan_in (join)
                 ▼
           [planner]              ← 整合所有结果生成行程
                 │
                 ▼
              END
"""

import json
import asyncio
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START

from app.agents.state import TripPlanState
from app.agents.prompts import (
    ATTRACTION_AGENT_SYSTEM, ATTRACTION_AGENT_USER,
    WEATHER_AGENT_SYSTEM, WEATHER_AGENT_USER,
    HOTEL_AGENT_SYSTEM, HOTEL_AGENT_USER,
    PLANNER_AGENT_SYSTEM, PLANNER_AGENT_USER,
)
from app.models.schemas import TripPlan, TripPlanRequest
from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_llm(fast: bool = False) -> ChatOpenAI:
    settings = get_settings()
    model = settings.llm_fast_model if fast else settings.llm_model
    return ChatOpenAI(
        model=model,
        api_key=settings.dashscope_api_key,
        base_url=settings.llm_base_url,
        temperature=0.7,
        max_tokens=4096,
    )


def _get_llm_with_tools(tools: list) -> Any:
    return _get_llm().bind_tools(tools)


# ─────────────────────────── 工具定义 ───────────────────────────

def _build_amap_tools(settings):
    """构建高德地图工具（直接HTTP调用，避免MCP进程管理问题）"""
    import requests
    from langchain_core.tools import tool

    @tool
    def maps_text_search(keywords: str, city: str, types: str = "") -> str:
        """搜索POI（景点、酒店等）。keywords为关键词，city为城市，types为可选的POI类型"""
        try:
            params = {
                "key": settings.amap_api_key,
                "keywords": keywords,
                "city": city,
                "citylimit": "true",
                "offset": 20,
                "output": "json",
            }
            if types:
                params["types"] = types
            resp = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=params,
                timeout=10,
            )
            data = resp.json()
            if data.get("status") != "1":
                info = data.get("info", "unknown error")
                logger.warning(f"高德API返回错误: {info}，将由LLM使用自有知识补充")
                return f"API暂不可用({info})，请基于你的知识提供{city}的{keywords}信息"

            pois = data.get("pois", [])
            if not pois:
                return f"未找到{city}的{keywords}相关结果，请基于你的知识补充"

            results = []
            for p in pois[:15]:
                loc = p.get("location", "")
                lng, lat = (loc.split(",") if "," in loc else ("", ""))
                results.append(
                    f"名称: {p.get('name', '')}\n"
                    f"地址: {p.get('address', '')}\n"
                    f"经度: {lng}  纬度: {lat}\n"
                    f"评分: {p.get('biz_ext', {}).get('rating', 'N/A')}\n"
                    f"类型: {p.get('type', '')}\n"
                )
            return "\n---\n".join(results)
        except Exception as e:
            logger.error(f"maps_text_search error: {e}")
            return f"搜索出错: {str(e)}"

    @tool
    def maps_weather(city: str) -> str:
        """查询城市天气预报，返回未来几天的天气信息"""
        try:
            # 先获取城市adcode
            geo_resp = requests.get(
                "https://restapi.amap.com/v3/geocode/geo",
                params={"key": settings.amap_api_key, "address": city, "output": "json"},
                timeout=10,
            )
            geo_data = geo_resp.json()
            geocodes = geo_data.get("geocodes", [])
            adcode = geocodes[0].get("adcode", city) if geocodes else city

            # 查询天气
            weather_resp = requests.get(
                "https://restapi.amap.com/v3/weather/weatherInfo",
                params={
                    "key": settings.amap_api_key,
                    "city": adcode,
                    "extensions": "all",
                    "output": "json",
                },
                timeout=10,
            )
            weather_data = weather_resp.json()
            if weather_data.get("status") != "1":
                info = weather_data.get("info", "unknown")
                logger.warning(f"天气API返回错误: {info}")
                return f"天气API暂不可用，请基于{city}的季节特征提供典型天气描述"

            forecasts = weather_data.get("forecasts", [])
            if not forecasts:
                return "未获取到天气数据"

            casts = forecasts[0].get("casts", [])
            results = []
            for c in casts:
                results.append(
                    f"日期: {c.get('date', '')}\n"
                    f"白天天气: {c.get('dayweather', '')}\n"
                    f"夜间天气: {c.get('nightweather', '')}\n"
                    f"最高温度: {c.get('daytemp', '')}℃\n"
                    f"最低温度: {c.get('nighttemp', '')}℃\n"
                    f"风向: {c.get('daywind', '')}\n"
                    f"风力: {c.get('daypower', '')}级\n"
                )
            return "\n---\n".join(results)
        except Exception as e:
            logger.error(f"maps_weather error: {e}")
            return f"天气查询出错: {str(e)}"

    return [maps_text_search, maps_weather]


# ─────────────────────────── Agent节点 ───────────────────────────

async def _run_react_agent(
    system_prompt: str,
    user_message: str,
    tools: list,
    fast: bool = False,
) -> str:
    """运行一个带工具调用的ReAct Agent，返回最终文本结果"""
    from langchain_core.messages import AIMessage, ToolMessage  # noqa: F401

    llm = _get_llm(fast=fast).bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    max_rounds = 6
    for _ in range(max_rounds):
        response = await llm.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content or ""

        # 执行所有工具调用（捕获 lambda 闭包变量）
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = dict(tc["args"])
            if tool_name in tool_map:
                try:
                    _tool = tool_map[tool_name]
                    _args = tool_args
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda t=_tool, a=_args: t.invoke(a)
                    )
                except Exception as e:
                    result = f"工具执行出错: {str(e)}"
            else:
                result = f"未找到工具: {tool_name}"

            messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )

    # 超出轮次，让LLM总结
    final_response: AIMessage = await llm.ainvoke(messages)
    return final_response.content or "未能获取结果"


async def sync_node(state: TripPlanState) -> dict:
    """同步节点：等待 attraction + weather 都完成后再触发 hotel，解决 LangGraph 不等长路径 fan-in 提前触发问题"""
    logger.info("🔀  同步节点：景点与天气均已就绪，开始酒店搜索")
    return {}


async def attraction_search_node(state: TripPlanState) -> dict:
    """景点搜索Agent"""
    logger.info("🏛️  景点搜索Agent 开始运行")
    settings = get_settings()
    tools = _build_amap_tools(settings)
    req: TripPlanRequest = state["request"]

    user_msg = ATTRACTION_AGENT_USER.format(
        city=req.city,
        preferences=req.preferences,
        days=req.days,
        budget=req.budget,
    )

    try:
        result = await _run_react_agent(ATTRACTION_AGENT_SYSTEM, user_msg, tools, fast=True)
        logger.info("✅ 景点搜索完成")
        return {"attraction_results": result}
    except Exception as e:
        logger.error(f"景点搜索失败: {e}")
        return {"attraction_results": f"景点搜索失败: {str(e)}"}


async def weather_query_node(state: TripPlanState) -> dict:
    """天气查询Agent"""
    logger.info("🌤️  天气查询Agent 开始运行")
    settings = get_settings()
    tools = _build_amap_tools(settings)
    req: TripPlanRequest = state["request"]

    user_msg = WEATHER_AGENT_USER.format(
        city=req.city,
        start_date=req.start_date,
        end_date=req.end_date,
        days=req.days,
    )

    try:
        result = await _run_react_agent(WEATHER_AGENT_SYSTEM, user_msg, tools, fast=True)
        logger.info("✅ 天气查询完成")
        return {"weather_results": result}
    except Exception as e:
        logger.error(f"天气查询失败: {e}")
        return {"weather_results": f"天气查询失败: {str(e)}"}


async def hotel_search_node(state: TripPlanState) -> dict:
    """酒店推荐Agent"""
    logger.info("🏨  酒店搜索Agent 开始运行")
    settings = get_settings()
    tools = _build_amap_tools(settings)
    req: TripPlanRequest = state["request"]

    user_msg = HOTEL_AGENT_USER.format(
        city=req.city,
        accommodation=req.accommodation,
        budget=req.budget,
        days=req.days,
        attraction_results=state.get("attraction_results", "暂无景点数据"),
    )

    try:
        result = await _run_react_agent(HOTEL_AGENT_SYSTEM, user_msg, tools, fast=True)
        logger.info("✅ 酒店搜索完成")
        return {"hotel_results": result}
    except Exception as e:
        logger.error(f"酒店搜索失败: {e}")
        return {"hotel_results": f"酒店搜索失败: {str(e)}"}


async def planner_node(state: TripPlanState) -> dict:
    """行程规划Agent：整合三个并行Agent的结果，生成完整行程"""
    logger.info("📋  行程规划Agent 开始运行")
    req: TripPlanRequest = state["request"]

    extra = getattr(req, "extra_requirements", "").strip()
    extra_section = f"- 额外要求：{extra}" if extra else ""

    user_msg = PLANNER_AGENT_USER.format(
        city=req.city,
        days=req.days,
        start_date=req.start_date,
        end_date=req.end_date,
        preferences=req.preferences,
        budget=req.budget,
        transportation=req.transportation,
        accommodation=req.accommodation,
        extra_requirements_section=extra_section,
        attraction_results=state.get("attraction_results", "无数据"),
        weather_results=state.get("weather_results", "无数据"),
        hotel_results=state.get("hotel_results", "无数据"),
    )

    llm = _get_llm()
    # 规划Agent使用更低temperature，确保JSON稳定输出
    llm.temperature = 0.3

    messages = [
        SystemMessage(content=PLANNER_AGENT_SYSTEM),
        HumanMessage(content=user_msg),
    ]

    content = ""
    try:
        response = await llm.ainvoke(messages)
        content = (response.content or "").strip()

        # 清理可能的markdown代码块包裹
        if content.startswith("```"):
            lines = content.split("\n")
            # 去掉首行 ```json 和末行 ```
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            content = "\n".join(lines[start:end])

        trip_data = json.loads(content)
        trip_plan = TripPlan(**trip_data)
        logger.info(f"✅ 行程规划完成，共{len(trip_plan.days)}天")
        return {"trip_plan": trip_plan}
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}\n原始内容前500字: {content[:500]}")
        return {"error": f"行程规划JSON解析失败: {str(e)}", "trip_plan": None}
    except Exception as e:
        logger.error(f"行程规划失败: {e}")
        return {"error": str(e), "trip_plan": None}


# ─────────────────────────── 构建图 ───────────────────────────

def build_trip_planner_graph():
    """构建并编译旅行规划LangGraph"""
    workflow = StateGraph(TripPlanState)

    # 注册节点
    workflow.add_node("attraction_search", attraction_search_node)
    workflow.add_node("weather_query", weather_query_node)
    workflow.add_node("sync", sync_node)
    workflow.add_node("hotel_search", hotel_search_node)
    workflow.add_node("planner", planner_node)

    # START → attraction 和 weather 并行（节省时间）
    workflow.add_edge(START, "attraction_search")
    workflow.add_edge(START, "weather_query")

    # 两者都完成后汇入 sync_node（等长路径 fan-in，不会提前触发下游）
    workflow.add_edge("attraction_search", "sync")
    workflow.add_edge("weather_query", "sync")

    # sync → hotel（hotel 拿到景点坐标后搜索附近酒店）
    workflow.add_edge("sync", "hotel_search")

    # hotel → planner（单一入边，不存在 fan-in 歧义）
    workflow.add_edge("hotel_search", "planner")

    # planner → END
    workflow.add_edge("planner", END)

    return workflow.compile()


# 单例图实例
_graph = None

def get_trip_planner_graph():
    global _graph
    if _graph is None:
        _graph = build_trip_planner_graph()
    return _graph
