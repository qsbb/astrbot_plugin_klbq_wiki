from __future__ import annotations

import re
from html import unescape
from typing import Optional
from urllib.parse import quote, urlencode

import aiohttp

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


PLUGIN_NAME = "astrbot_plugin_klbq_wiki"
API_URL = "https://wiki.biligame.com/klbq/api.php"
PAGE_URL = "https://wiki.biligame.com/klbq/{}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


@register(
    PLUGIN_NAME,
    "凌溪",
    "通过 /卡拉彼丘 角色名/武器 查询卡拉彼丘 Biligame Wiki 信息",
    "1.0.0",
    "https://github.com/qsbb/astrbot_plugin_klbq_wiki",
)
class KlbqWikiPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self._session: Optional[aiohttp.ClientSession] = None

    async def terminate(self):
        if self._session and not self._session.closed:
            await self._session.close()
        logger.info("[KlbqWiki] 插件已卸载")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": "https://wiki.biligame.com/klbq/%E9%A6%96%E9%A1%B5",
                },
                timeout=aiohttp.ClientTimeout(total=15),
            )
        return self._session

    async def _api_get(self, params: dict) -> Optional[dict]:
        session = await self._get_session()
        try:
            async with session.get(API_URL, params=params) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"[KlbqWiki] API HTTP {resp.status}: {text[:200]}")
                    return None
                return await resp.json(content_type=None)
        except Exception as e:
            logger.warning(f"[KlbqWiki] API 请求失败: {e}")
            return None

    async def _search_title(self, keyword: str) -> Optional[str]:
        data = await self._api_get(
            {
                "action": "opensearch",
                "format": "json",
                "formatversion": "2",
                "search": keyword,
                "namespace": "0",
                "limit": "1",
            }
        )
        if isinstance(data, list) and len(data) >= 2 and data[1]:
            return str(data[1][0])
        return None

    async def _query_page(self, title: str) -> Optional[dict]:
        data = await self._api_get(
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "redirects": "1",
                "prop": "extracts|pageimages",
                "titles": title,
                "explaintext": "1",
                "pithumbsize": "600",
            }
        )
        pages = (data or {}).get("query", {}).get("pages", [])
        if not pages:
            return None
        page = pages[0]
        if page.get("missing"):
            return None
        return page

    async def _lookup(self, keyword: str) -> Optional[dict]:
        page = await self._query_page(keyword)
        if page:
            return page
        title = await self._search_title(keyword)
        if not title:
            return None
        return await self._query_page(title)

    def _extract_keyword(self, event: AstrMessageEvent, keyword: str = "") -> str:
        if keyword:
            return keyword.strip()
        try:
            msg = event.get_message_str() or ""
        except Exception:
            return ""
        msg = msg.strip()
        msg = re.sub(r"^/卡拉彼丘\s*", "", msg)
        return msg.strip()

    def _clean_extract(self, text: str) -> str:
        text = unescape(text or "")
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text) > 900:
            text = text[:900].rstrip() + "..."
        return text

    def _format_page(self, page: dict) -> str:
        title = page.get("title") or "未知条目"
        extract = self._clean_extract(page.get("extract") or "暂无简介。")
        url = PAGE_URL.format(quote(str(title), safe=""))
        thumb = (page.get("thumbnail") or {}).get("source")

        lines = [f"卡拉彼丘 Wiki：{title}", "", extract, "", f"详情：{url}"]
        if thumb:
            lines.append(f"图片：{thumb}")
        return "\n".join(lines)

    @filter.command("卡拉彼丘")
    async def query_klbq(self, event: AstrMessageEvent, keyword: str = ""):
        query = self._extract_keyword(event, keyword)
        if not query:
            yield event.plain_result("用法：/卡拉彼丘 角色名/武器\n例如：/卡拉彼丘 米雪儿")
            return

        page = await self._lookup(query)
        if not page:
            search_url = PAGE_URL.format("Special:%E6%90%9C%E7%B4%A2?") + urlencode({"search": query})
            yield event.plain_result(f"未找到“{query}”的卡拉彼丘 Wiki 条目。\n可手动搜索：{search_url}")
            return

        yield event.plain_result(self._format_page(page))
