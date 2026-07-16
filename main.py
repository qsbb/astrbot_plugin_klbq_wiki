from __future__ import annotations

import asyncio
import re
import traceback
from html import escape, unescape
from html.parser import HTMLParser
from typing import Any, Optional
from urllib.parse import quote, unquote, urlencode

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

BUILTIN_ALIASES = {
    # 欧泊
    "米雪儿·李": "米雪儿", "米雪儿": "米雪儿", "猫猫": "米雪儿",
    "糖猫": "米雪儿", "哈基米": "米雪儿", "哈基米雪儿": "米雪儿",
    "信": "信", "信前辈": "信", "信哥": "信", "虾头男": "信", "下头男": "信",
    "心夏": "心夏", "奶妈": "心夏", "奶狙": "心夏", "心夏妈妈": "心夏",
    "心夏麻麻": "心夏", "妈妈": "心夏", "麻麻": "心夏", "志木心夏": "心夏",
    "伊薇特": "伊薇特", "熊妹": "伊薇特", "小熊": "伊薇特", "熊熊": "伊薇特",
    "河伊薇": "伊薇特", "伊维特": "伊薇特",
    "芙拉薇娅": "芙拉薇娅", "芙拉": "芙拉薇娅", "蝴蝶": "芙拉薇娅", "蝴蝶姐": "芙拉薇娅",
    "忧雾": "忧雾", "蜗牛": "忧雾", "蜗牛妹": "忧雾", "小蜗": "忧雾", "蜗蜗": "忧雾",
    "蕾欧娜": "蕾欧娜", "土木": "蕾欧娜", "工程师": "蕾欧娜", "土木姐": "蕾欧娜",
    "千代": "千代", "千代姐": "千代",
    # 剪刀手
    "明": "明", "牢明": "明", "明爷": "明", "明老大": "明",
    "拉薇": "拉薇", "辣味": "拉薇", "拉维": "拉薇", "lv": "拉薇",
    "梅瑞狄斯": "梅瑞狄斯", "沙猫": "梅瑞狄斯", "埃及猫": "梅瑞狄斯",
    "梅瑞迪斯": "梅瑞狄斯", "卖沙子的": "梅瑞狄斯", "沙狗": "梅瑞狄斯",
    "令": "令", "抽奖哥": "令", "令哥": "令", "牢令": "令",
    "香奈美": "香奈美", "奈美": "香奈美", "香奈": "香奈美", "偶像": "香奈美",
    "歌姬": "香奈美", "臭奈美": "香奈美",
    "艾卡": "艾卡", "炎帝": "艾卡", "唐卡": "艾卡", "火妹": "艾卡", "姓艾大王": "艾卡",
    "珐格兰丝": "珐格兰丝", "调香师": "珐格兰丝", "香水": "珐格兰丝",
    "香水姐": "珐格兰丝", "调香": "珐格兰丝", "小珐": "珐格兰丝",
    "玛拉": "玛拉", "玛拉大人": "玛拉", "麻辣大人": "玛拉", "麻辣": "玛拉",
    # 乌尔比诺
    "奥黛丽·格罗夫": "奥黛丽", "奥黛丽": "奥黛丽", "机枪": "奥黛丽",
    "机枪姐": "奥黛丽", "奥大力": "奥黛丽", "大黄": "奥黛丽",
    "玛德蕾娜·利里": "玛德蕾娜·利里", "玛德蕾娜": "玛德蕾娜·利里",
    "小画家": "玛德蕾娜·利里", "画家": "玛德蕾娜·利里", "颜料妹": "玛德蕾娜·利里",
    "小玛": "玛德蕾娜·利里", "玛头": "玛德蕾娜·利里", "打胶妹": "玛德蕾娜·利里",
    "绯莎": "绯莎", "鲨鱼": "绯莎", "飞鲨": "绯莎", "鲨鲨": "绯莎",
    "星绘": "星绘", "星辉": "星绘", "小绘": "星绘", "星绘精灵": "星绘", "小绘精灵": "星绘",
    "白墨": "白墨", "墨狗": "白墨", "蟑螂": "白墨", "绿色蟑螂": "白墨",
    "加拉蒂亚·利里": "加拉蒂亚·利里", "加拉蒂亚": "加拉蒂亚·利里",
    "卡牌": "加拉蒂亚·利里", "大画家": "加拉蒂亚·利里", "魔术师": "加拉蒂亚·利里",
    "汐": "汐", "盾汐": "汐", "汐姐": "汐", "盾狗": "汐", "盾构": "汐",
    # “角色武器 / 角色的武器”会动态解析到该角色的武器页面
}

ROLE_FIELDS = [
    "名称", "英文名", "日文名", "别名", "性别", "身份", "定位", "阵营", "声优",
    "生日", "星座", "年龄", "身高", "体重", "活动区域", "超弦体特性", "兴趣爱好",
    "饮食习惯", "个性语录", "简介", "观测语录", "武器", "武器类型",
]
WEAPON_FIELDS = [
    "名称", "使用者", "归属角色", "角色", "类型", "武器类型", "介绍", "开火模式", "辅助攻击",
    "放大倍率", "射速", "射速（移动端）", "瞄准速度", "瞄准速度（移动端）", "散射控制",
    "后坐力控制", "弹匣容量", "装填速度", "蓄力速度", "弦化伤害", "10米伤害", "20米伤害",
    "30米伤害", "40米伤害", "50米伤害", "基础伤害", "部位系数", "拉栓时间", "换弹动作时间",
    "后坐力恢复时间", "蓄力时间", "等待开镜时间", "初段蓄力时间", "完成蓄力时间",
    "移动速度", "持枪移速", "开镜移速", "跑步速度", "举枪速度",
    "精准度", "后坐力", "穿透", "原型", "简介",
]
FIELD_ALIASES = {
    "移动速度": ["移速", "持枪移速", "持枪移动速度", "移动速度", "超弦体移速"],
    "开镜移速": ["开镜移动速度", "开镜移速", "ADS移速", "瞄准移动速度"],
    "弹匣容量": ["弹匣", "载弹量", "弹夹容量", "弹匣容量"],
    "装填速度": ["换弹", "换弹速度", "换弹时间", "装填时间", "装填速度"],
    "头部伤害": ["爆头伤害", "头部伤害", "头部"],
    "身体伤害": ["躯干伤害", "身体伤害", "上肢", "身体"],
    "腿部伤害": ["腿部伤害", "下肢", "腿部"],
    "使用者": ["使用者", "归属角色", "角色"],
}

CARD_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; width: 100%; min-width: 0; min-height: 0; background: #10182f; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; overflow: hidden; }
body { display: block; }
.klbq-card { width: 100%; min-width: {{ card_width }}px; position: relative; overflow: hidden; padding: 34px; color: #edf7ff; background: linear-gradient(135deg, #10182f 0%, #182a55 48%, #5d3ca0 100%); }
.glow { position: absolute; right: -100px; top: -120px; width: 360px; height: 360px; border-radius: 50%; background: radial-gradient(circle, rgba(118, 221, 255, .48), rgba(118, 221, 255, 0) 68%); }
.header { position: relative; display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; }
.tag { display: inline-block; padding: 7px 14px; border-radius: 999px; background: rgba(255, 255, 255, .14); color: #aee9ff; font-size: 20px; letter-spacing: 1px; }
.title { margin-top: 12px; font-size: 46px; font-weight: 800; text-shadow: 0 4px 16px rgba(0, 0, 0, .28); }
.subtitle { margin-top: 8px; color: #c6d5ff; font-size: 22px; }
.cover { width: 100%; max-height: 320px; object-fit: cover; border-radius: 20px; margin: 4px 0 24px; box-shadow: inset 0 0 0 1px rgba(255,255,255,.2), 0 12px 38px rgba(0,0,0,.25); }
.grid { position: relative; display: grid; grid-template-columns: repeat({{ grid_columns }}, minmax(0, 1fr)); gap: 12px; width: 100%; }
.row { min-width: 0; padding: 14px 16px; border-radius: 16px; background: rgba(255, 255, 255, .12); border: 1px solid rgba(255, 255, 255, .12); }
.label { color: #90dfff; font-size: 18px; margin-bottom: 6px; }
.value { color: #ffffff; font-size: 21px; line-height: 1.42; word-break: break-all; overflow-wrap: anywhere; }
.tip { position: relative; margin-top: 22px; padding: 16px 18px; border-radius: 16px; background: rgba(255, 230, 125, .16); border: 1px solid rgba(255, 230, 125, .28); color: #fff2a8; font-size: 22px; }
.footer { position: relative; margin-top: 22px; color: rgba(237, 247, 255, .62); font-size: 16px; text-align: right; }
</style>
</head>
<body>
<div class="klbq-card">
  <div class="glow"></div>
  <div class="header">
    <div>
      <div class="tag">卡拉彼丘 Wiki</div>
      <div class="title">{{ title }}</div>
      <div class="subtitle">{{ kind }}</div>
    </div>
  </div>
  {% if thumb %}<img class="cover" src="{{ thumb }}" />{% endif %}
  <div class="grid">
    {% for item in items %}
    <div class="row">
      <div class="label">{{ item.label }}</div>
      <div class="value">{{ item.value }}</div>
    </div>
    {% endfor %}
  </div>
  {% if tip %}<div class="tip">{{ tip }}</div>{% endif %}
  <div class="footer">Generated by astrbot_plugin_klbq_wiki</div>
</div>
</body>
</html>
"""


class _WikiTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.table_depth = 0
        self.in_row = False
        self.in_cell = False
        self.current_cell_parts: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []
        self.tables: list[list[list[str]]] = []
        self.current_table_rows: list[list[str]] = []
        self.links: list[tuple[str, str]] = []
        self.current_href = ""
        self.current_link_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table":
            self.table_depth += 1
            if self.table_depth == 1:
                self.current_table_rows = []
        elif tag == "tr" and self.table_depth > 0:
            self.in_row = True
            self.current_row = []
        elif tag in {"td", "th"} and self.in_row:
            self.in_cell = True
            self.current_cell_parts = []
        elif tag == "br" and self.in_cell:
            self.current_cell_parts.append("\n")
        elif tag == "a":
            self.current_href = attrs_dict.get("href", "")
            self.current_link_parts = []

    def handle_endtag(self, tag):
        if tag == "table" and self.table_depth > 0:
            if self.table_depth == 1 and self.current_table_rows:
                self.tables.append(self.current_table_rows)
                self.current_table_rows = []
            self.table_depth -= 1
        elif tag in {"td", "th"} and self.in_cell:
            text = self._clean("".join(self.current_cell_parts))
            if text:
                self.current_row.append(text)
            self.in_cell = False
            self.current_cell_parts = []
        elif tag == "tr" and self.in_row:
            if self.current_row:
                self.rows.append(self.current_row)
                if self.table_depth == 1:
                    self.current_table_rows.append(self.current_row)
            self.in_row = False
            self.current_row = []
        elif tag == "a" and self.current_href:
            text = self._clean("".join(self.current_link_parts))
            if text:
                self.links.append((text, self.current_href))
            self.current_href = ""
            self.current_link_parts = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell_parts.append(data)
        if self.current_href:
            self.current_link_parts.append(data)

    def _clean(self, text: str) -> str:
        text = unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


@register(
    PLUGIN_NAME,
    "凌溪",
    "通过 /卡拉彼丘 角色名/武器 查询卡拉彼丘 Biligame Wiki 信息",
    "1.3.1",
    "https://github.com/qsbb/astrbot_plugin_klbq_wiki",
)
class KlbqWikiPlugin(Star):
    def __init__(self, context: Context, config: Any = None):
        super().__init__(context)
        self.config = config or {}
        self._session: Optional[aiohttp.ClientSession] = None
        self.aliases = self._load_aliases()

    async def terminate(self):
        if self._session and not self._session.closed:
            await self._session.close()
        logger.info("[KlbqWiki] 插件已卸载")

    def _load_aliases(self) -> dict[str, str]:
        aliases = dict(BUILTIN_ALIASES)
        raw = str(self.config.get("custom_aliases", "") or "").strip()
        for line in raw.splitlines():
            if "=" not in line:
                continue
            alias, title = line.split("=", 1)
            alias = alias.strip()
            title = title.strip()
            if alias and title:
                aliases[alias] = title
        return aliases

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
        data = await self._api_get({
            "action": "opensearch", "format": "json", "formatversion": "2",
            "search": keyword, "namespace": "0", "limit": "1",
        })
        if isinstance(data, list) and len(data) >= 2 and data[1]:
            return str(data[1][0])
        return None

    async def _query_page(self, title: str) -> Optional[dict]:
        data = await self._api_get({
            "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
            "prop": "extracts|pageimages", "titles": title, "explaintext": "1", "pithumbsize": "800",
        })
        pages = (data or {}).get("query", {}).get("pages", [])
        if not pages:
            logger.info(f"[KlbqWiki] 页面查询无结果: {title}")
            return None
        if pages[0].get("missing"):
            logger.info(f"[KlbqWiki] 页面不存在: {title}")
            return None
        return pages[0]

    async def _query_page_html(self, title: str) -> Optional[str]:
        data = await self._api_get({
            "action": "parse", "format": "json", "formatversion": "2", "page": title,
            "prop": "text|displaytitle", "redirects": "1",
        })
        if isinstance(data, dict):
            return (data.get("parse") or {}).get("text")
        return None

    async def _lookup(self, keyword: str) -> Optional[dict]:
        logger.info(f"[KlbqWiki] 开始查询: keyword={keyword}")
        weapon_page = await self._lookup_role_weapon(keyword)
        if weapon_page:
            logger.info(f"[KlbqWiki] 命中角色武器页: {weapon_page.get('title')}")
            return weapon_page
        resolved = self.aliases.get(keyword, keyword)
        logger.info(f"[KlbqWiki] 别名解析: {keyword} -> {resolved}")
        for candidate in self._query_candidates(resolved):
            page = await self._query_page(candidate)
            if page:
                logger.info(f"[KlbqWiki] 直接命中页面: candidate={candidate}, title={page.get('title')}")
                return page
        title = await self._search_title(resolved)
        logger.info(f"[KlbqWiki] 搜索结果: {resolved} -> {title}")
        if not title:
            return None
        page = await self._query_page(title)
        if page:
            logger.info(f"[KlbqWiki] 搜索命中页面: title={page.get('title')}")
        return page

    def _query_candidates(self, title: str) -> list[str]:
        candidates = [title]
        if "·" in title:
            candidates.append(title.replace("·", ""))
        if " " in title:
            candidates.append(title.replace(" ", ""))
        return list(dict.fromkeys(candidate for candidate in candidates if candidate))

    async def _lookup_role_weapon(self, keyword: str) -> Optional[dict]:
        if not keyword.endswith("武器") and not keyword.endswith("的武器"):
            return None
        role_query = keyword.removesuffix("的武器").removesuffix("武器").strip()
        if not role_query:
            return None
        role_title = self.aliases.get(role_query.casefold(), role_query)
        role_page = await self._query_page(role_title)
        if not role_page:
            found_title = await self._search_title(role_title)
            role_page = await self._query_page(found_title) if found_title else None
        if not role_page:
            return None
        html = await self._query_page_html(role_page.get("title") or role_title)
        fields = self._extract_info(html or "", role_page.get("title") or role_title) if html else {}
        weapon = fields.get("武器")
        return await self._query_page(weapon) if weapon else None

    def _extract_keyword(self, event: AstrMessageEvent) -> str:
        msg = (event.message_str or "").strip()
        return re.sub(r"^/(?:卡拉彼丘|klbq)\s*", "", msg, flags=re.I).strip()

    def _clean_text(self, text: str) -> str:
        text = unescape(text or "")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _page_url(self, title: str) -> str:
        return PAGE_URL.format(quote(str(title), safe=""))

    def _extract_info(self, html: str, title: str) -> dict[str, str]:
        parser = _WikiTableParser()
        parser.feed(html or "")
        parser.close()

        fields: dict[str, str] = {"名称": title}
        for row in parser.rows:
            if len(row) >= 2:
                label = self._clean_label(row[0])
                value = self._clean_text(" ".join(row[1:]))
                if label in {"卡拉彼丘画师协会", "画师协会"}:
                    continue
                if label and value and label not in fields:
                    fields[label] = value
            elif len(row) == 1 and "名称" not in fields:
                fields["名称"] = row[0]

        for canonical, candidates in FIELD_ALIASES.items():
            if canonical in fields:
                continue
            for candidate in candidates:
                if candidate in fields:
                    fields[canonical] = fields[candidate]
                    break

        self._extract_weapon_tables(parser.tables, fields)
        self._extract_weapon_feel_text(html, fields)
        weapon = self._extract_weapon_link(parser.links, title)
        if weapon and "武器" not in fields:
            fields["武器"] = weapon
        return fields

    def _extract_weapon_feel_text(self, html: str, fields: dict[str, str]):
        text = re.sub(r"<br\s*/?>", "\n", html or "", flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = self._clean_text(text)
        patterns = {
            "拉栓时间": r"拉栓时间[:：]\s*([^\s]+秒)",
            "后坐力恢复时间": r"后坐力恢复时间[:：]\s*([^\s]+秒)",
            "蓄力时间": r"蓄力时间[:：]\s*([^\s]+秒)",
            "等待开镜时间": r"等待开镜时间[:：]\s*([^\s]+秒)",
            "初段蓄力时间": r"初段蓄力时间[:：]\s*([^\s]+秒)",
            "完成蓄力时间": r"完成蓄力时间[:：]\s*([^\s]+秒)",
            "卸弹匣时间": r"卸弹匣[:：]\s*([^\s]+秒)",
            "装弹匣时间": r"装弹匣[:：]\s*([^\s]+秒)",
            "上膛/结束时间": r"上膛/结束[:：]\s*([^\s]+秒)",
        }
        for label, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                fields[label] = match.group(1)
        reload_parts = [
            f"卸弹匣 {fields['卸弹匣时间']}" if fields.get("卸弹匣时间") else "",
            f"装弹匣 {fields['装弹匣时间']}" if fields.get("装弹匣时间") else "",
            f"上膛/结束 {fields['上膛/结束时间']}" if fields.get("上膛/结束时间") else "",
        ]
        reload_text = "；".join(part for part in reload_parts if part)
        if reload_text:
            fields["换弹动作时间"] = reload_text

    def _extract_weapon_tables(self, tables: list[list[list[str]]], fields: dict[str, str]):
        for table in tables:
            if len(table) < 2:
                continue
            header = [self._clean_label(cell) for cell in table[0]]
            if {"头部", "上肢", "下肢"}.issubset(set(header)):
                self._extract_damage_table(table, fields)
            elif any("基础伤害" in " ".join(row) for row in table):
                self._extract_coefficient_table(table, fields)

    def _extract_damage_table(self, table: list[list[str]], fields: dict[str, str]):
        header = [self._clean_label(cell) for cell in table[0]]
        for row in table[1:]:
            if len(row) < 4 or not re.search(r"\d+\s*米", row[0]):
                continue
            distance = re.sub(r"\s+", "", row[0])
            parts = []
            for label, value in zip(header[1:], row[1:]):
                parts.append(f"{label} {self._compact_value(value)}")
            fields[f"{distance}伤害"] = "；".join(parts)

    def _extract_coefficient_table(self, table: list[list[str]], fields: dict[str, str]):
        flat = [self._clean_text(cell) for row in table for cell in row if self._clean_text(cell)]
        for index, cell in enumerate(flat):
            if cell == "基础伤害" and index + 1 < len(flat):
                fields.setdefault("基础伤害", flat[index + 1])
            elif cell in {"头部", "上肢", "下肢"} and index + 1 < len(flat):
                fields.setdefault("部位系数", "")
                fields["部位系数"] = (fields["部位系数"] + f"{cell} {flat[index + 1]}；").strip("；")

    def _compact_value(self, value: str) -> str:
        value = self._clean_text(value)
        value = value.replace("- ", "")
        value = re.sub(r"\s*：\s*", ":", value)
        value = re.sub(r"\s+", " ", value)
        return value

    def _clean_label(self, label: str) -> str:
        label = self._clean_text(label).rstrip("：:")
        label = re.sub(r"[\[\]（）()]", "", label)
        return label.strip()

    def _extract_weapon_link(self, links: list[tuple[str, str]], title: str) -> str:
        skip_texts = {title, "首页", "语音", "画廊", "誓约", "档案馆"}
        for index, (text, href) in enumerate(links[:80]):
            if text == "武器":
                target = self._title_from_href(href)
                if target and target != title:
                    return target
                if index + 1 < len(links):
                    return links[index + 1][0]
        for text, href in links[:80]:
            if text in skip_texts or text == "武器":
                continue
            if href.startswith("/klbq/") and "action=edit" not in href and "分类:" not in href:
                return text
        return ""

    def _title_from_href(self, href: str) -> str:
        if not href.startswith("/klbq/"):
            return ""
        title = href.removeprefix("/klbq/").split("#", 1)[0].split("?", 1)[0]
        if not title or title.startswith("分类:"):
            return ""
        return unquote(title).replace("_", " ").strip()

    def _is_weapon(self, fields: dict[str, str], title: str) -> bool:
        markers = " ".join([title, fields.get("武器类型", ""), fields.get("类型", ""), fields.get("弹匣容量", ""), fields.get("射速", "")])
        return any(word in markers for word in ["步枪", "冲锋枪", "机枪", "霰弹枪", "手枪", "武器", "射速", "弹匣"])

    def _items_for_output(self, fields: dict[str, str], is_weapon: bool) -> list[dict[str, str]]:
        template = WEAPON_FIELDS if is_weapon else ROLE_FIELDS
        items = []
        for label in template:
            value = fields.get(label)
            if value:
                if len(value) > 260:
                    value = value[:260].rstrip() + "..."
                items.append({"label": label, "value": value})
        return items[:24]

    def _text_output(self, title: str, items: list[dict[str, str]], page_url: str, tip: str = "") -> str:
        lines = [f"卡拉彼丘 Wiki：{title}", ""]
        lines.extend(f"{item['label']}：{item['value']}" for item in items)
        if tip:
            lines.extend(["", tip])
        lines.extend(["", f"详情：{page_url}"])
        return "\n".join(lines)

    def _render_settings(self) -> tuple[int, int, float, bool]:
        columns = max(1, min(4, int(self.config.get("grid_columns", 2) or 2)))
        card_width = max(420, min(1200, int(self.config.get("card_width", 760) or 760)))
        timeout = max(1.0, min(60.0, float(self.config.get("image_timeout", 8) or 8)))
        fallback = bool(self.config.get("text_fallback", True))
        return columns, card_width, timeout, fallback

    async def _render_image(self, title: str, kind: str, items: list[dict[str, str]], thumb: str, tip: str) -> Optional[str]:
        columns, card_width, timeout, _ = self._render_settings()
        try:
            safe_items = [{"label": escape(i["label"]), "value": escape(i["value"])} for i in items]
            render_task = self.html_render(
                CARD_TEMPLATE,
                {
                    "title": escape(title),
                    "kind": escape(kind),
                    "items": safe_items,
                    "thumb": thumb,
                    "tip": escape(tip) if tip else "",
                    "grid_columns": columns,
                    "card_width": card_width,
                },
                options={
                    "type": "jpeg",
                    "quality": 88,
                    "full_page": True,
                    "animations": "disabled",
                    "caret": "hide",
                    "scale": "css",
                    "timeout": timeout * 1000,
                },
            )
            return await asyncio.wait_for(render_task, timeout=timeout + 1)
        except asyncio.TimeoutError:
            logger.warning(f"[KlbqWiki] 图片渲染超时: title={title}, timeout={timeout}s")
            return None
        except Exception as e:
            logger.warning(f"[KlbqWiki] 图片渲染失败: {e}")
            return None

    async def _send_result(self, event: AstrMessageEvent, title: str, page_url: str, fields: dict[str, str], thumb: str = ""):
        is_weapon = self._is_weapon(fields, title)
        items = self._items_for_output(fields, is_weapon)
        if not items:
            items = [{"label": "简介", "value": "暂无可提取的结构化信息。"}]
        kind = "武器资料" if is_weapon else "角色资料"
        weapon = fields.get("武器", "")
        tip = f"提示：可继续使用 /卡拉彼丘 {weapon} 查询{title}的武器。" if (not is_weapon and weapon) else ""

        _, _, timeout, text_fallback = self._render_settings()
        render_image = bool(self.config.get("render_image", True))
        logger.info(f"[KlbqWiki] 输出准备: title={title}, kind={kind}, item_count={len(items)}, render_image={render_image}, timeout={timeout}s, text_fallback={text_fallback}")
        if render_image:
            image_url = await self._render_image(title, kind, items, thumb, tip)
            logger.info(f"[KlbqWiki] 图片渲染结果: title={title}, success={bool(image_url)}")
            if image_url:
                yield event.image_result(image_url)
                if self.config.get("send_detail_link", True):
                    yield event.plain_result(f"详情：{page_url}")
                return
            if not text_fallback:
                yield event.plain_result(f"“{title}”图片渲染失败，请稍后重试。")
                return

        logger.info(f"[KlbqWiki] 回退文本输出: title={title}")
        yield event.plain_result(self._text_output(title, items, page_url, tip))

    async def _handle_query(self, event: AstrMessageEvent, query: str):
        logger.info(f"[KlbqWiki] 收到查询: query={query}")
        if not query:
            yield event.plain_result("用法：/卡拉彼丘 角色名/武器\n备用：/klbq 角色名/武器\n例如：/卡拉彼丘 心夏\n例如：/klbq 空境")
            return

        try:
            page = await self._lookup(query)
            if not page:
                search_url = PAGE_URL.format("Special:%E6%90%9C%E7%B4%A2?") + urlencode({"search": query})
                logger.info(f"[KlbqWiki] 未找到条目: query={query}, search_url={search_url}")
                yield event.plain_result(f"未找到“{query}”的卡拉彼丘 Wiki 条目。\n可手动搜索：{search_url}")
                return

            title = page.get("title") or self.aliases.get(query.casefold(), query)
            page_url = self._page_url(title)
            logger.info(f"[KlbqWiki] 准备解析页面: title={title}, url={page_url}")
            html = await self._query_page_html(title)
            logger.info(f"[KlbqWiki] HTML 获取结果: title={title}, has_html={bool(html)}, html_len={len(html or '')}")
            fields = self._extract_info(html or "", title) if html else {"名称": title}
            if not fields.get("简介"):
                extract = self._clean_text(page.get("extract") or "")
                if extract:
                    fields["简介"] = extract[:220].rstrip() + ("..." if len(extract) > 220 else "")
            thumb = (page.get("thumbnail") or {}).get("source") or ""
            logger.info(f"[KlbqWiki] 解析完成: title={title}, fields={list(fields.keys())}, thumb={bool(thumb)}")

            async for result in self._send_result(event, title, page_url, fields, thumb):
                yield result
        except Exception as e:
            logger.error(f"[KlbqWiki] 查询异常: query={query}, error={e}\n{traceback.format_exc()}")
            yield event.plain_result(f"查询“{query}”时发生错误，已写入后台日志。")

    @filter.event_message_type(filter.EventMessageType.ALL, priority=100)
    async def query_klbq(self, event: AstrMessageEvent):
        message = (event.message_str or "").strip()
        if not re.match(r"^/(?:卡拉彼丘|klbq)(?:\s|$)", message, flags=re.I):
            return
        query = self._extract_keyword(event)
        logger.info(f"[KlbqWiki] 消息监听命中: message={message!r}, query={query!r}")
        event.stop_event()
        async for result in self._handle_query(event, query):
            yield result
