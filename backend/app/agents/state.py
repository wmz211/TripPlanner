from typing import Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from app.models.schemas import TripPlanRequest, TripPlan


class TripPlanState(TypedDict):
    # 用户原始请求
    request: TripPlanRequest

    # 三个并行 Agent 的输出
    attraction_results: str
    weather_results: str
    hotel_results: str

    # 最终规划结果
    trip_plan: Optional[TripPlan]

    # 错误信息（任一步骤失败时记录）
    error: Optional[str]
