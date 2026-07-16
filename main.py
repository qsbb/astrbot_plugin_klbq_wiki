from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
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
FIELD_TEMPLATE = [
    "名称",
    "英文名",
    "日文名",
    "别名",
    "性别",
    "身份",
    "定位",
    "阵营",
    "声优",
    "画师",
    "生日",
    "星座",
    "年龄",
    "身高",
    "体重",
    "活动区域",
    "超弦体特性",
    "兴趣爱好",
    "饮食习惯",
    "个性语录",
    "简介",
    "观测语录",
    "武器",
    "武器类型",
    "稀有度",
    "原型",
    "伤害",
    "弹匣容量",
    "射速",
    "装填",
    "开火模式",
]


class _InfoboxParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.table_depth = 0
        self.in_row = False
        self.in_cell = False
        self.current_cell_tag = ""
        self.current_cell_parts: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if not self.in_table:
                self.in_table = True
                self.table_depth = 1
                return
            self.table_depth += 1
            return
        if not self.in_table:
            return
        if tag == "tr":
            self.in_row = True
            self.current_row = []
        elif tag in {"td", "th"} and self.in_row:
            self.in_cell = True
            self.current_cell_tag = tag
            self.current_cell_parts = []
        elif tag == "br" and self.in_cell:
            self.current_cell_parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.table_depth -= 1
            if self.table_depth <= 0:
                self.in_table = False
            return
        if not self.in_table:
            return
        if tag in {"td", "th"} and self.in_cell:
            text = self._clean_text("".join(self.current_cell_parts))
            self.current_row.append(text)
            self.in_cell = False
            self.current_cell_tag = ""
            self.current_cell_parts = []
        elif tag == "tr" and self.in_row:
            row = [cell for cell in self.current_row if cell]
            if row:
                self.rows.append(row)
            self.in_row = False
            self.current_row = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell_parts.append(data)

    def _clean_text(self, text: str) -> str:
        text = unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


@register(
    PLUGIN_NAME,
    "凌溪",
    "通过 /卡拉彼丘 角色名/武器 查询卡拉彼丘 Biligame Wiki 信息",
    "1.0.1",
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
                timeout=aiohttp.ClientTimeout(total=20),
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

    async def _query_page_html(self, title: str) -> Optional[dict]:
        data = await self._api_get(
            {
                "action": "parse",
                "format": "json",
                "formatversion": "2",
                "page": title,
                "prop": "text|displaytitle",
                "redirects": "1",
            }
        )
        if not isinstance(data, dict):
            return None
        return data if "parse" in data else None

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

    def _clean_text(self, text: str) -> str:
        text = unescape(text or "")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _page_url(self, title: str) -> str:
        return PAGE_URL.format(quote(str(title), safe=""))

    def _extract_infobox(self, html: str) -> dict[str, str]:
        parser = _InfoboxParser()
        parser.feed(html or "")
        parser.close()

        fields: dict[str, str] = {}
        page_title = ""
        for row in parser.rows:
            if not row:
                continue
            if len(row) == 1 and not page_title:
                page_title = self._clean_text(row[0])
                continue
            if len(row) >= 2:
                label = self._clean_text(row[0]).rstrip("：")
                value = self._clean_text(" ".join(row[1:]))
                if label and value and label not in fields:
                    fields[label] = value
        if page_title and "名称" not in fields:
            fields["名称"] = page_title
        return fields

    def _format_fields(self, title: str, fields: dict[str, str], page_url: str, thumb: Optional[str]) -> str:
        lines = [f"卡拉彼丘 Wiki：{title}", ""]
        for label in FIELD_TEMPLATE:
            value = fields.get(label)
            if value:
                lines.append(f"{label}：{value}")
        if len(lines) == 2:
            lines.append("暂无可提取的结构化信息。")
        lines.extend(["", f"详情：{page_url}"])
        if thumb:
            lines.append(f"图片：{thumb}")
        return "\n".join(lines)

    def _format_fallback(self, page: dict, page_url: str) -> str:
        title = page.get("title") or "未知条目"
        extract = self._clean_text(page.get("extract") or "")
        if not extract:
            extract = "暂无简介。"
        lines = [f"卡拉彼丘 Wiki：{title}", "", extract, "", f"详情：{page_url}"]
        thumb = (page.get("thumbnail") or {}).get("source")
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

        title = page.get("title") or query
        page_url = self._page_url(title)

        html_page = await self._query_page_html(title)
        if html_page and html_page.get("parse", {}).get("text"):
            html = html_page["parse"]["text"]
            fields = self._extract_infobox(html)
            if fields:
                thumb = None
                thumbs = page.get("thumbnail") or {}
                if isinstance(thumbs, dict):
                    thumb = thumbs.get("source")
                yield event.plain_result(self._format_fields(title, fields, page_url, thumb))
                return

        yield event.plain_result(self._format_fallback(page, page_url))
