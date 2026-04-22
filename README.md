# TripPlanner - AI 智能旅行规划助手

基于 LangGraph 多智能体架构的旅行规划应用，输入目的地和偏好，自动生成包含景点、酒店、天气、餐饮的完整行程。

## 架构

```
用户请求
    │
    ├──► 景点搜索 Agent ──┐
    │                     ├──► 同步节点 ──► 酒店搜索 Agent ──► 规划 Agent ──► 完整行程
    └──► 天气查询 Agent ──┘
```

景点搜索与天气查询并行执行，酒店搜索依据景点坐标就近推荐，最终由规划 Agent 整合生成按地理聚类排序的行程 JSON，前端解析渲染。

## 技术栈

**后端**
- FastAPI + LangGraph + LangChain
- 通义千问（DashScope）作为 LLM
- 高德地图 API：POI 搜索 + 天气预报
- Unsplash API：景点配图
- SSE 流式推送进度

**前端**
- Vue 3 + TypeScript + Vite
- TailwindCSS + Pinia + Vue Router

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # 填入各 API Key
python run.py
```

服务启动于 `http://localhost:8000`

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

## 环境变量

复制 `backend/.env.example` 为 `backend/.env` 并填写：

| 变量 | 说明 | 获取地址 |
|------|------|----------|
| `DASHSCOPE_API_KEY` | 通义千问 API Key | [阿里云百炼](https://bailian.console.aliyun.com/) |
| `AMAP_API_KEY` | 高德地图服务端 Key | [高德开放平台](https://lbs.amap.com/) |
| `AMAP_WEB_KEY` | 高德地图 Web 端 Key | 同上 |
| `UNSPLASH_ACCESS_KEY` | Unsplash Access Key | [Unsplash Developers](https://unsplash.com/developers) |

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/trip/plan/stream` | 流式生成旅行计划（SSE） |
| `GET` | `/api/trip/health` | 健康检查 |

请求体示例：
```json
{
  "city": "成都",
  "start_date": "2025-05-01",
  "end_date": "2025-05-03",
  "preferences": "历史文化,美食",
  "budget": "中等",
  "transportation": "公共交通",
  "accommodation": "经济型",
  "extra_requirements": ""
}
```
