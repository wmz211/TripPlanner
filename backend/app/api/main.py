import logging
import os
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# 控制台
logging.basicConfig(level=logging.INFO, format=_fmt)

# 文件（每个文件最大 10MB，保留 5 个）
_log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(_log_dir, exist_ok=True)
_file_handler = RotatingFileHandler(
    os.path.join(_log_dir, "app.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setFormatter(logging.Formatter(_fmt))
logging.getLogger().addHandler(_file_handler)

app = FastAPI(
    title="智能旅行助手 API",
    description="基于 LangGraph 多智能体的旅行规划服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
