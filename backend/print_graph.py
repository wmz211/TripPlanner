"""打印 LangGraph 图结构，用于调试验证节点执行顺序"""
import sys
sys.path.insert(0, '.')

from app.agents.graph import build_trip_planner_graph

g = build_trip_planner_graph()
graph = g.get_graph()

print("=== Mermaid ===")
print(graph.draw_mermaid())

print("=== ASCII ===")
print(graph.draw_ascii())
