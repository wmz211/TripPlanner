import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# 景点名关键词 → 英文补充词（景点名本身会直接加入查询）
_NAME_SUPPLEMENTS: dict[str, str] = {
    "故宫": "Forbidden City Beijing imperial palace",
    "长城": "Great Wall China ancient",
    "西湖": "West Lake Hangzhou reflection",
    "外滩": "Shanghai Bund waterfront night",
    "颐和园": "Summer Palace Beijing garden lake",
    "天坛": "Temple of Heaven Beijing",
    "兵马俑": "Terracotta Warriors Xian ancient",
    "黄山": "Huangshan Yellow Mountain misty",
    "张家界": "Zhangjiajie Avatar mountains",
    "九寨沟": "Jiuzhaigou colorful lake valley",
    "豫园": "Yuyuan Garden Shanghai classical",
    "东方明珠": "Oriental Pearl Tower Shanghai skyline",
    "南京路": "Nanjing Road Shanghai shopping",
    "田子坊": "Tianzifang Shanghai art lane",
    "新天地": "Xintiandi Shanghai modern",
}

# 类别关键词 → 英文补充词
_CATEGORY_SUPPLEMENTS: dict[str, str] = {
    "历史": "historic ancient Chinese architecture",
    "文化": "Chinese cultural heritage",
    "自然": "China scenic nature landscape",
    "公园": "Chinese garden park",
    "博物": "museum exhibition",
    "寺": "Chinese temple pagoda",
    "庙": "Chinese temple shrine",
    "购物": "shopping street market",
    "美食": "Chinese food cuisine",
    "海滩": "beach seaside",
    "山": "mountain hiking scenic",
    "湖": "lake reflection",
    "景区": "tourist attraction scenic",
    "景点": "China tourist landmark",
}

# 无 API key 时的兜底图池（按类别关键词匹配）
_FALLBACK_POOL: list[tuple[str, str]] = [
    ("历史",   "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800"),
    ("文化",   "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800"),
    ("自然",   "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800"),
    ("公园",   "https://images.unsplash.com/photo-1537531383618-9d1ac65f3c97?w=800"),
    ("博物",   "https://images.unsplash.com/photo-1555921015-5532091f6026?w=800"),
    ("寺",     "https://images.unsplash.com/photo-1526711657229-e7e080ed7aa1?w=800"),
    ("庙",     "https://images.unsplash.com/photo-1526711657229-e7e080ed7aa1?w=800"),
    ("购物",   "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=800"),
    ("山",     "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800"),
    ("湖",     "https://images.unsplash.com/photo-1504870712357-65ea720bf078?w=800"),
]

# 城市兜底图（无匹配时按城市变化，避免全部同一张）
_CITY_FALLBACKS: list[str] = [
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800",
    "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=800",
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800",
    "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=800",
]


def _build_query(name: str, category: str, city: str) -> str:
    """始终把景点名放进查询，保证每个景点搜到不同的图"""
    supplements = []

    # 名称补充词
    for keyword, en in _NAME_SUPPLEMENTS.items():
        if keyword in name:
            supplements.append(en)
            break

    # 类别补充词
    for keyword, en in _CATEGORY_SUPPLEMENTS.items():
        if keyword in (category or ""):
            supplements.append(en)
            break

    # 景点名 + 城市始终包含，保证唯一性
    parts = [name, city] + supplements
    return " ".join(parts)


def _fallback(name: str, category: str, city: str) -> str:
    """无 API key 时：按类别返回对应图，实在没匹配按城市名 hash 从池中取一张"""
    cat = (category or "") + (name or "")
    for keyword, url in _FALLBACK_POOL:
        if keyword in cat:
            return url
    # 用城市名做分散，同一城市内不同景点用同一张，不同城市用不同张
    idx = abs(hash(city)) % len(_CITY_FALLBACKS)
    return _CITY_FALLBACKS[idx]


class UnsplashService:
    def __init__(self, access_key: str):
        self.access_key = access_key
        self.base_url = "https://api.unsplash.com"
        self._enabled = bool(access_key and access_key != "your-unsplash-key")

    def get_photo_url(self, name: str, city: str = "", category: str = "", image_keywords: str = "") -> Optional[str]:
        if not self._enabled:
            return _fallback(name, category, city)

        try:
            # LLM 生成的英文关键词直接用，否则退回本地规则
            query = image_keywords.strip() if image_keywords.strip() else _build_query(name, category, city)
            logger.debug(f"Unsplash 查询: {query!r}")
            resp = requests.get(
                f"{self.base_url}/search/photos",
                params={
                    "query": query,
                    "per_page": 3,
                    "orientation": "landscape",
                    "client_id": self.access_key,
                },
                timeout=8,
            )
            if resp.status_code == 401:
                logger.warning("Unsplash key 无效，降级为占位图")
                self._enabled = False
                return _fallback(name, category, city)

            results = resp.json().get("results", [])
            if results:
                return results[0]["urls"]["regular"]
        except Exception as e:
            logger.warning(f"Unsplash 查询失败 ({name}): {e}")

        return _fallback(name, category, city)
