"""图片本地缓存模块。

查询过的角色立绘、皮肤图会缓存到本地 data/images/ 目录，
下次查询同一图片直接读取本地文件，避免重复网络下载。

适用于：
- html_render 渲染卡片时的 <img src="...">（本地路径需转 file:// URL）
- Comp.Image.fromURL(url) 发送图片（astrbot 支持本地文件路径）
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

import aiohttp

PLUGIN_NAME = "astrbot_plugin_klbq_wiki"

# 文件扩展名映射
_EXT_MAP = {
    "jpg": "jpg",
    "jpeg": "jpg",
    "png": "png",
    "gif": "gif",
    "webp": "webp",
    "bmp": "bmp",
}


def _ext_from_url(url: str) -> str:
    """从 URL 推断文件扩展名。"""
    try:
        path = urlparse(url).path.lower()
        for ext in ("jpg", "jpeg", "png", "gif", "webp", "bmp"):
            if path.endswith(f".{ext}"):
                return _EXT_MAP[ext]
    except Exception:
        pass
    return "jpg"


def to_file_url(path: str) -> str:
    """将本地路径转换为 file:// URL，供 html_render 的 <img src> 使用。

    - 本地绝对路径 → file:// URL
    - 远程 URL（http/https）→ 原样返回
    - file:// URL → 原样返回
    - 空值 → 原样返回
    """
    if not path:
        return path
    if path.startswith(("http://", "https://", "file://")):
        return path
    try:
        # Path.as_uri() 会把 Windows 路径转为 file:///d:/... 格式
        return Path(path).resolve().as_uri()
    except Exception:
        return path


class ImageCache:
    """图片本地缓存。

    Args:
        enabled: 是否启用缓存（默认 True）
        ttl: 缓存有效期（秒），0 表示永不过期
        cache_dir: 缓存目录路径。推荐使用 StarTools.get_data_dir() / "images"
                   遵循 AstrBot 规范：持久化数据存到 data/plugin_data/<插件名>/ 下
    """

    def __init__(
        self,
        enabled: bool = True,
        ttl: int = 30 * 86400,
        cache_dir: Path | None = None,
    ):
        self.enabled = enabled
        self.ttl = max(0, int(ttl))
        # 缓存目录：优先使用外部传入（如 StarTools.get_data_dir()），遵循 AstrBot 规范
        self._dir = Path(cache_dir) if cache_dir else Path("data/images")
        self._ensure_dir()
        self._semaphore = asyncio.Semaphore(4)

    def _ensure_dir(self) -> None:
        """确保缓存目录存在。"""
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            from astrbot.api import logger

            logger.warning(f"[KlbqWiki] 缓存目录创建失败: {e}")
            self.enabled = False

    def _path_for(self, url: str) -> Path:
        """计算 URL 的本地缓存路径。"""
        hash_str = hashlib.md5(url.encode("utf-8")).hexdigest()
        ext = _ext_from_url(url)
        return self._dir / f"{hash_str}.{ext}"

    def _is_valid(self, local_path: Path) -> bool:
        """检查本地缓存是否有效（存在且未过期）。"""
        try:
            if not local_path.is_file() or local_path.stat().st_size == 0:
                return False
            if self.ttl == 0:
                return True  # 永不过期
            age_sec = time.time() - local_path.stat().st_mtime
            return age_sec < self.ttl
        except Exception:
            return False

    async def get(self, url: str) -> str:
        """获取图片，优先从本地缓存读取，否则下载到本地。

        Returns:
            本地文件路径（缓存启用且成功时）或原始 URL（缓存禁用或下载失败时）
        """
        if not url:
            return url
        if not self.enabled:
            return url

        local_path = self._path_for(url)

        # 1. 本地有效缓存，直接返回
        if self._is_valid(local_path):
            return str(local_path)

        # 2. 下载到本地
        try:
            async with self._semaphore:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            from astrbot.api import logger

                            logger.warning(
                                f"[KlbqWiki] 缓存图片下载失败 HTTP {resp.status}: {url[:100]}"
                            )
                            return url
                        data = await resp.read()
                        if not data:
                            return url
                        local_path.write_bytes(data)
                        return str(local_path)
        except Exception as e:
            from astrbot.api import logger

            logger.warning(f"[KlbqWiki] 缓存图片下载异常: {e}")
            return url

    async def get_many(self, urls: list[str], concurrency: int = 4) -> list[str]:
        """批量获取图片（并发控制）。

        Returns:
            与 urls 顺序对应的结果数组
        """
        if not self.enabled:
            return list(urls)
        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_one(url: str) -> str:
            async with semaphore:
                return await self.get(url)

        return await asyncio.gather(*(fetch_one(u) for u in urls))

    def stats(self) -> dict:
        """统计缓存情况。

        Returns:
            {"count": int, "size_bytes": int, "dir": str}
        """
        count = 0
        size_bytes = 0
        try:
            for file in self._dir.iterdir():
                if file.is_file():
                    count += 1
                    size_bytes += file.stat().st_size
        except Exception:
            pass
        return {"count": count, "size_bytes": size_bytes, "dir": str(self._dir)}

    def cleanup(self) -> int:
        """清理过期缓存文件，返回清理数量。"""
        if not self.enabled or self.ttl == 0:
            return 0
        cleaned = 0
        now = time.time()
        try:
            for file in self._dir.iterdir():
                try:
                    if file.is_file() and (now - file.stat().st_mtime) > self.ttl:
                        file.unlink()
                        cleaned += 1
                except Exception:
                    pass
        except Exception:
            pass
        return cleaned
