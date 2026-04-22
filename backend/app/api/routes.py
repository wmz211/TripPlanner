import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import TripPlanRequest, TripPlan
from app.agents.graph import get_trip_planner_graph
from app.services.unsplash_service import UnsplashService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trip", tags=["trip"])


def _get_unsplash() -> UnsplashService:
    return UnsplashService(get_settings().unsplash_access_key)


async def _enrich_with_images(trip_plan: TripPlan, city: str) -> None:
    """并发为所有景点获取图片"""
    unsplash = _get_unsplash()

    async def fetch_one(attr):
        if attr.image_url:
            return
        url = await asyncio.get_event_loop().run_in_executor(
            None, lambda a=attr: unsplash.get_photo_url(a.name, city, a.category or "", a.image_keywords or "")
        )
        attr.image_url = url

    tasks = [fetch_one(attr) for day in trip_plan.days for attr in day.attractions]
    await asyncio.gather(*tasks, return_exceptions=True)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/plan/stream")
async def stream_trip_plan(request: TripPlanRequest):
    """SSE 流式接口：每完成一个 Agent 节点就推一条进度消息，最后推完整结果"""
    logger.info(f"收到流式规划请求: {request.city} {request.days}天")

    async def generate():
        graph = get_trip_planner_graph()
        initial_state = {
            "request": request,
            "attraction_results": "",
            "weather_results": "",
            "hotel_results": "",
            "trip_plan": None,
            "error": None,
        }

        # 内部节点，不向前端暴露
        _HIDDEN_NODES = {"sync", "__start__", "__end__"}

        final_output: dict = {}
        try:
            async for chunk in graph.astream(initial_state):
                for node_name, node_output in chunk.items():
                    if node_name in _HIDDEN_NODES:
                        continue
                    final_output.update(node_output)
                    logger.info(f"节点完成: {node_name}")
                    yield _sse({"type": "progress", "node": node_name})
        except Exception as e:
            logger.error(f"图执行失败: {e}")
            yield _sse({"type": "error", "message": str(e)})
            return

        if final_output.get("error"):
            yield _sse({"type": "error", "message": final_output["error"]})
            return

        trip_plan: TripPlan = final_output.get("trip_plan")
        if not trip_plan:
            yield _sse({"type": "error", "message": "未能生成旅行计划"})
            return

        try:
            await _enrich_with_images(trip_plan, request.city)
        except Exception as e:
            logger.warning(f"图片获取失败，忽略: {e}")

        logger.info(f"流式规划完成: {trip_plan.city} {len(trip_plan.days)}天")
        yield _sse({"type": "result", "data": trip_plan.model_dump()})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "trip-planner-langgraph"}
