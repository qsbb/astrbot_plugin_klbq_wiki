from __future__ import annotations

import asyncio
import random
import re
import time
import traceback
from datetime import date, datetime
from html import escape, unescape
from html.parser import HTMLParser
from typing import Any, Optional
from urllib.parse import quote, unquote, urlencode
from zoneinfo import ZoneInfo

import aiohttp
from bs4 import BeautifulSoup

from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools, register

from .image_cache import ImageCache, to_file_url


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
    "米雪儿·李": "米雪儿",
    "米雪儿": "米雪儿",
    "猫猫": "米雪儿",
    "糖猫": "米雪儿",
    "哈基米": "米雪儿",
    "哈基米雪儿": "米雪儿",
    "信": "信",
    "信前辈": "信",
    "信哥": "信",
    "虾头男": "信",
    "下头男": "信",
    "心夏": "心夏",
    "奶妈": "心夏",
    "奶狙": "心夏",
    "心夏妈妈": "心夏",
    "心夏麻麻": "心夏",
    "妈妈": "心夏",
    "麻麻": "心夏",
    "志木心夏": "心夏",
    "伊薇特": "伊薇特",
    "熊妹": "伊薇特",
    "小熊": "伊薇特",
    "熊熊": "伊薇特",
    "河伊薇": "伊薇特",
    "伊维特": "伊薇特",
    "芙拉薇娅": "芙拉薇娅",
    "芙拉": "芙拉薇娅",
    "蝴蝶": "芙拉薇娅",
    "蝴蝶姐": "芙拉薇娅",
    "忧雾": "忧雾",
    "蜗牛": "忧雾",
    "蜗牛妹": "忧雾",
    "小蜗": "忧雾",
    "蜗蜗": "忧雾",
    "蕾欧娜": "蕾欧娜",
    "土木": "蕾欧娜",
    "工程师": "蕾欧娜",
    "土木姐": "蕾欧娜",
    "千代": "千代",
    "千代姐": "千代",
    # 剪刀手
    "明": "明",
    "牢明": "明",
    "明爷": "明",
    "明老大": "明",
    "拉薇": "拉薇",
    "辣味": "拉薇",
    "拉维": "拉薇",
    "lv": "拉薇",
    "梅瑞狄斯": "梅瑞狄斯",
    "沙猫": "梅瑞狄斯",
    "埃及猫": "梅瑞狄斯",
    "梅瑞迪斯": "梅瑞狄斯",
    "卖沙子的": "梅瑞狄斯",
    "沙狗": "梅瑞狄斯",
    "令": "令",
    "抽奖哥": "令",
    "令哥": "令",
    "牢令": "令",
    "香奈美": "香奈美",
    "奈美": "香奈美",
    "香奈": "香奈美",
    "偶像": "香奈美",
    "歌姬": "香奈美",
    "臭奈美": "香奈美",
    "艾卡": "艾卡",
    "炎帝": "艾卡",
    "唐卡": "艾卡",
    "火妹": "艾卡",
    "姓艾大王": "艾卡",
    "珐格兰丝": "珐格兰丝",
    "调香师": "珐格兰丝",
    "香水": "珐格兰丝",
    "香水姐": "珐格兰丝",
    "调香": "珐格兰丝",
    "小珐": "珐格兰丝",
    "玛拉": "玛拉",
    "玛拉大人": "玛拉",
    "麻辣大人": "玛拉",
    "麻辣": "玛拉",
    # 乌尔比诺
    "奥黛丽·格罗夫": "奥黛丽",
    "奥黛丽": "奥黛丽",
    "机枪": "奥黛丽",
    "机枪姐": "奥黛丽",
    "奥大力": "奥黛丽",
    "大黄": "奥黛丽",
    "玛德蕾娜·利里": "玛德蕾娜·利里",
    "玛德蕾娜": "玛德蕾娜·利里",
    "小画家": "玛德蕾娜·利里",
    "画家": "玛德蕾娜·利里",
    "颜料妹": "玛德蕾娜·利里",
    "小玛": "玛德蕾娜·利里",
    "玛头": "玛德蕾娜·利里",
    "打胶妹": "玛德蕾娜·利里",
    "绯莎": "绯莎",
    "鲨鱼": "绯莎",
    "飞鲨": "绯莎",
    "鲨鲨": "绯莎",
    "星绘": "星绘",
    "星辉": "星绘",
    "小绘": "星绘",
    "星绘精灵": "星绘",
    "小绘精灵": "星绘",
    "白墨": "白墨",
    "墨狗": "白墨",
    "蟑螂": "白墨",
    "绿色蟑螂": "白墨",
    "加拉蒂亚·利里": "加拉蒂亚·利里",
    "加拉蒂亚": "加拉蒂亚·利里",
    "卡牌": "加拉蒂亚·利里",
    "大画家": "加拉蒂亚·利里",
    "魔术师": "加拉蒂亚·利里",
    "汐": "汐",
    "盾汐": "汐",
    "汐姐": "汐",
    "盾狗": "汐",
    "盾构": "汐",
    # “角色武器 / 角色的武器”会动态解析到该角色的武器页面
}

ROLE_FIELDS = [
    "名称",
    "英文名",
    "日文名",
    "别名",
    "性别",
    "身份",
    "定位",
    "阵营",
    "声优",
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
]
WEAPON_FIELDS = [
    "名称",
    "使用者",
    "归属角色",
    "角色",
    "类型",
    "武器类型",
    "介绍",
    "开火模式",
    "辅助攻击",
    "放大倍率",
    "射速",
    "射速（移动端）",
    "瞄准速度",
    "瞄准速度（移动端）",
    "散射控制",
    "后坐力控制",
    "弹匣容量",
    "装填速度",
    "蓄力速度",
    "弦化伤害",
    "10米伤害",
    "20米伤害",
    "30米伤害",
    "40米伤害",
    "50米伤害",
    "基础伤害",
    "部位系数",
    "拉栓时间",
    "换弹动作时间",
    "后坐力恢复时间",
    "蓄力时间",
    "等待开镜时间",
    "初段蓄力时间",
    "完成蓄力时间",
    "移动速度",
    "持枪移速",
    "开镜移速",
    "跑步速度",
    "举枪速度",
    "精准度",
    "后坐力",
    "穿透",
    "原型",
    "简介",
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
.cover { width: 100%; height: 440px; object-fit: contain; border-radius: 20px; margin: 4px 0 24px; padding: 12px; background: rgba(7, 14, 35, .28); box-shadow: inset 0 0 0 1px rgba(255,255,255,.2), 0 12px 38px rgba(0,0,0,.25); }
.grid { position: relative; display: grid; grid-template-columns: repeat({{ grid_columns }}, minmax(0, 1fr)); gap: 12px; width: 100%; }
.row { min-width: 0; padding: 14px 16px; border-radius: 16px; background: rgba(255, 255, 255, .12); border: 1px solid rgba(255, 255, 255, .12); }
.label { color: #90dfff; font-size: 18px; margin-bottom: 6px; }
.value { color: #ffffff; font-size: 21px; line-height: 1.42; word-break: break-all; overflow-wrap: anywhere; white-space: pre-wrap; }
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


BIRTHDAY_TEMPLATE = """
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
.glow2 { position: absolute; left: -80px; bottom: -100px; width: 280px; height: 280px; border-radius: 50%; background: radial-gradient(circle, rgba(255, 200, 120, .35), rgba(255, 200, 120, 0) 70%); }
.header { position: relative; display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; }
.tag { display: inline-block; padding: 7px 14px; border-radius: 999px; background: rgba(255, 255, 255, .14); color: #aee9ff; font-size: 20px; letter-spacing: 1px; }
.title { margin-top: 12px; font-size: 42px; font-weight: 800; text-shadow: 0 4px 16px rgba(0, 0, 0, .28); }
.subtitle { margin-top: 8px; color: #c6d5ff; font-size: 20px; }
.hero { position: relative; display: flex; align-items: center; gap: 22px; margin: 8px 0 26px; padding: 20px; border-radius: 24px; background: rgba(255, 255, 255, .10); border: 1px solid rgba(255, 230, 125, .35); overflow: hidden; }
.hero-art { flex-shrink: 0; width: 260px; height: 360px; object-fit: cover; object-position: center top; border-radius: 18px; background: rgba(7, 14, 35, .35); box-shadow: 0 12px 32px rgba(0, 0, 0, .35); }
.hero-info { flex: 1; min-width: 0; }
.hero-name { font-size: 64px; font-weight: 900; line-height: 1.1; color: #ffffff; text-shadow: 0 4px 20px rgba(118, 221, 255, .55), 0 2px 8px rgba(0, 0, 0, .45); margin-bottom: 12px; word-break: break-all; }
.hero-date { font-size: 30px; font-weight: 700; color: #fff2a8; margin-bottom: 8px; }
.hero-countdown { display: inline-block; padding: 10px 20px; border-radius: 999px; background: rgba(255, 230, 125, .22); border: 1px solid rgba(255, 230, 125, .42); color: #ffe89a; font-size: 24px; font-weight: 700; }
.list-title { position: relative; font-size: 24px; font-weight: 700; color: #aee9ff; margin-bottom: 12px; padding-left: 14px; border-left: 4px solid #76ddff; }
.list { position: relative; display: flex; flex-direction: column; gap: 10px; }
.row { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-radius: 14px; background: rgba(255, 255, 255, .10); border: 1px solid rgba(255, 255, 255, .10); }
.row-name { color: #ffffff; font-size: 22px; font-weight: 600; word-break: break-all; overflow-wrap: anywhere; }
.row-meta { color: #c6d5ff; font-size: 19px; flex-shrink: 0; margin-left: 14px; }
.row-countdown { color: #fff2a8; font-size: 19px; font-weight: 600; flex-shrink: 0; margin-left: 12px; }
.footer { position: relative; margin-top: 22px; color: rgba(237, 247, 255, .62); font-size: 16px; text-align: right; }
</style>
</head>
<body>
<div class="klbq-card">
  <div class="glow"></div>
  <div class="glow2"></div>
  <div class="header">
    <div>
      <div class="tag">卡拉彼丘 Wiki</div>
      <div class="title">{{ title }}</div>
      <div class="subtitle">{{ kind }}</div>
    </div>
  </div>
  {% if hero.art %}
  <div class="hero">
    <img class="hero-art" src="{{ hero.art }}" />
    <div class="hero-info">
      <div class="hero-name">{{ hero.name }}</div>
      <div class="hero-date">{{ hero.date }}</div>
      <div class="hero-countdown">{{ hero.countdown }}</div>
    </div>
  </div>
  {% endif %}
  {% if others %}
  <div class="list-title">其他近期生日</div>
  <div class="list">
    {% for item in others %}
    <div class="row">
      <div class="row-name">{{ item.name }}</div>
      <div class="row-meta">{{ item.date }}</div>
      <div class="row-countdown">{{ item.countdown }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}
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
    "查询卡拉彼丘角色、武器、皮肤、生日、赛季与喵言喵语等 Biligame Wiki 信息",
    "1.5.1",
    "https://github.com/qsbb/astrbot_plugin_klbq_wiki",
)
class KlbqWikiPlugin(Star):
    def __init__(self, context: Context, config: Any = None):
        super().__init__(context)
        self.config = config or {}
        self._session: Optional[aiohttp.ClientSession] = None
        self.aliases = self._load_aliases()
        self._cache: dict[str, tuple[float, Any]] = {}
        self._wiki_semaphore = asyncio.Semaphore(4)
        # 图片缓存实例
        # 遵循 AstrBot 规范：持久化数据存到 data/plugin_data/<插件名>/ 下
        # 而非插件自身目录，防止更新/重装插件时数据被覆盖
        try:
            cache_dir = StarTools.get_data_dir(PLUGIN_NAME) / "images"
        except Exception as e:
            logger.warning(f"[KlbqWiki] 获取数据目录失败，回退到相对路径: {e}")
            cache_dir = None
        self._image_cache = ImageCache(
            enabled=bool(self.config.get("image_cache", True)),
            ttl=max(0, int(self.config.get("image_cache_ttl", 30) or 30)) * 86400,
            cache_dir=cache_dir,
        )

    async def terminate(self):
        if self._session and not self._session.closed:
            await self._session.close()
        logger.info("[KlbqWiki] 插件已卸载")

    def _load_aliases(self) -> dict[str, str]:
        aliases = {alias.casefold(): title for alias, title in BUILTIN_ALIASES.items()}
        raw = str(self.config.get("custom_aliases", "") or "").strip()
        for line in raw.splitlines():
            if "=" not in line:
                continue
            alias, title = line.split("=", 1)
            alias = alias.strip()
            title = title.strip()
            if alias and title:
                aliases[alias.casefold()] = title
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

    def _cache_get(self, key: str) -> Any:
        cached = self._cache.get(key)
        if cached and time.time() - cached[0] < 21600:
            logger.info(f"[KlbqWiki] 缓存命中: {key}")
            return cached[1]
        if cached:
            self._cache.pop(key, None)
        return None

    def _cache_set(self, key: str, value: Any) -> Any:
        self._cache[key] = (time.time(), value)
        return value

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
                "pithumbsize": "800",
            }
        )
        pages = (data or {}).get("query", {}).get("pages", [])
        if not pages:
            logger.info(f"[KlbqWiki] 页面查询无结果: {title}")
            return None
        if pages[0].get("missing"):
            logger.info(f"[KlbqWiki] 页面不存在: {title}")
            return None
        return pages[0]

    async def _query_page_html(self, title: str) -> Optional[str]:
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
        if isinstance(data, dict):
            return (data.get("parse") or {}).get("text")
        return None

    async def _lookup(self, keyword: str) -> Optional[dict]:
        logger.info(f"[KlbqWiki] 开始查询: keyword={keyword}")
        weapon_page = await self._lookup_role_weapon(keyword)
        if weapon_page:
            logger.info(f"[KlbqWiki] 命中角色武器页: {weapon_page.get('title')}")
            return weapon_page
        resolved = self.aliases.get(keyword.casefold(), keyword)
        logger.info(f"[KlbqWiki] 别名解析: {keyword} -> {resolved}")
        for candidate in self._query_candidates(resolved):
            page = await self._query_page(candidate)
            if page:
                logger.info(
                    f"[KlbqWiki] 直接命中页面: candidate={candidate}, title={page.get('title')}"
                )
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
        fields = (
            self._extract_info(html or "", role_page.get("title") or role_title)
            if html
            else {}
        )
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
            f"上膛/结束 {fields['上膛/结束时间']}"
            if fields.get("上膛/结束时间")
            else "",
        ]
        reload_text = "；".join(part for part in reload_parts if part)
        if reload_text:
            fields["换弹动作时间"] = reload_text

    def _extract_weapon_tables(
        self, tables: list[list[list[str]]], fields: dict[str, str]
    ):
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

    def _extract_coefficient_table(
        self, table: list[list[str]], fields: dict[str, str]
    ):
        flat = [
            self._clean_text(cell)
            for row in table
            for cell in row
            if self._clean_text(cell)
        ]
        for index, cell in enumerate(flat):
            if cell == "基础伤害" and index + 1 < len(flat):
                fields.setdefault("基础伤害", flat[index + 1])
            elif cell in {"头部", "上肢", "下肢"} and index + 1 < len(flat):
                fields.setdefault("部位系数", "")
                fields["部位系数"] = (
                    fields["部位系数"] + f"{cell} {flat[index + 1]}；"
                ).strip("；")

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
            if (
                href.startswith("/klbq/")
                and "action=edit" not in href
                and "分类:" not in href
            ):
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
        markers = " ".join(
            [
                title,
                fields.get("武器类型", ""),
                fields.get("类型", ""),
                fields.get("弹匣容量", ""),
                fields.get("射速", ""),
            ]
        )
        return any(
            word in markers
            for word in [
                "步枪",
                "冲锋枪",
                "机枪",
                "霰弹枪",
                "手枪",
                "武器",
                "射速",
                "弹匣",
            ]
        )

    def _items_for_output(
        self, fields: dict[str, str], is_weapon: bool
    ) -> list[dict[str, str]]:
        template = WEAPON_FIELDS if is_weapon else ROLE_FIELDS
        items = []
        for label in template:
            value = fields.get(label)
            if value:
                if len(value) > 260:
                    value = value[:260].rstrip() + "..."
                items.append({"label": label, "value": value})
        return items[:24]

    def _text_output(
        self, title: str, items: list[dict[str, str]], tip: str = ""
    ) -> str:
        lines = [f"卡拉彼丘 Wiki：{title}", ""]
        lines.extend(f"{item['label']}：{item['value']}" for item in items)
        if tip:
            lines.extend(["", tip])
        return "\n".join(lines)

    def _render_settings(self) -> tuple[int, int, float, bool]:
        columns = max(1, min(4, int(self.config.get("grid_columns", 2) or 2)))
        card_width = max(420, min(1200, int(self.config.get("card_width", 760) or 760)))
        timeout = max(1.0, min(60.0, float(self.config.get("image_timeout", 8) or 8)))
        fallback = bool(self.config.get("text_fallback", True))
        return columns, card_width, timeout, fallback

    async def _render_image(
        self, title: str, kind: str, items: list[dict[str, str]], thumb: str, tip: str
    ) -> Optional[str]:
        columns, card_width, timeout, _ = self._render_settings()
        try:
            safe_items = [
                {"label": escape(i["label"]), "value": escape(i["value"])}
                for i in items
            ]
            # html_render 用浏览器渲染，本地路径必须转成 file:// URL
            # 否则 <img src="d:\..."> 在 about:blank 基础下无法解析
            render_task = self.html_render(
                CARD_TEMPLATE,
                {
                    "title": escape(title),
                    "kind": escape(kind),
                    "items": safe_items,
                    "thumb": to_file_url(thumb) if thumb else "",
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
            logger.warning(
                f"[KlbqWiki] 图片渲染超时: title={title}, timeout={timeout}s"
            )
            return None
        except Exception as e:
            logger.warning(f"[KlbqWiki] 图片渲染失败: {e}")
            return None

    async def _send_text_card(
        self,
        event: AstrMessageEvent,
        title: str,
        text: str,
        kind: str = "查询结果",
        tip: str = "",
        thumb: str = "",
    ):
        render_image = bool(self.config.get("render_image", True))
        _, _, timeout, _ = self._render_settings()
        logger.info(
            f"[KlbqWiki] 文本卡片输出: title={title}, kind={kind}, "
            f"render_image={render_image}, timeout={timeout}s"
        )
        if render_image:
            image_url = await self._render_image(
                title,
                kind,
                [{"label": "内容", "value": text}],
                thumb,
                tip,
            )
            if image_url:
                yield event.image_result(image_url)
                return
        logger.info(f"[KlbqWiki] 文本卡片回退: title={title}")
        yield event.plain_result(text)

    async def _send_result(
        self,
        event: AstrMessageEvent,
        title: str,
        page_url: str,
        fields: dict[str, str],
        thumb: str = "",
    ):
        is_weapon = self._is_weapon(fields, title)
        items = self._items_for_output(fields, is_weapon)
        if not items:
            items = [{"label": "简介", "value": "暂无可提取的结构化信息。"}]
        kind = "武器资料" if is_weapon else "角色资料"
        weapon = fields.get("武器", "")
        tip = (
            f"提示：可继续使用 /卡拉彼丘 {weapon} 查询{title}的武器。"
            if (not is_weapon and weapon)
            else ""
        )

        _, _, timeout, text_fallback = self._render_settings()
        render_image = bool(self.config.get("render_image", True))
        logger.info(
            f"[KlbqWiki] 输出准备: title={title}, kind={kind}, item_count={len(items)}, render_image={render_image}, timeout={timeout}s, text_fallback={text_fallback}"
        )
        if render_image:
            image_url = await self._render_image(title, kind, items, thumb, tip)
            logger.info(
                f"[KlbqWiki] 图片渲染结果: title={title}, success={bool(image_url)}"
            )
            if image_url:
                yield event.image_result(image_url)
                if self.config.get("send_detail_link", True):
                    yield event.plain_result(page_url)
                return
            if not text_fallback:
                yield event.plain_result(f"“{title}”图片渲染失败，请稍后重试。")
                return

        logger.info(f"[KlbqWiki] 回退文本输出: title={title}")
        yield event.plain_result(self._text_output(title, items, tip))
        if self.config.get("send_detail_link", True):
            yield event.plain_result(page_url)

    async def _category_members(self, category: str) -> list[str]:
        members: list[str] = []
        cmcontinue = ""
        while True:
            params = {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "list": "categorymembers",
                "cmtitle": f"分类:{category}",
                "cmnamespace": "0",
                "cmlimit": "max",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue
            data = await self._api_get(params)
            if not data:
                raise RuntimeError(f"无法读取分类:{category}")
            members.extend(
                item.get("title", "")
                for item in data.get("query", {}).get("categorymembers", [])
            )
            cmcontinue = data.get("continue", {}).get("cmcontinue", "")
            if not cmcontinue:
                return [name for name in members if name]

    def _parse_birthday(self, html: str) -> Optional[tuple[int, int]]:
        soup = BeautifulSoup(html, "html.parser")
        cell = soup.select_one("td[itemprop=birthDate]")
        text = cell.get_text(" ", strip=True) if cell else ""
        if not text:
            for row in soup.select("tr"):
                cells = row.find_all(["th", "td"])
                if (
                    len(cells) >= 2
                    and self._clean_label(cells[0].get_text(" ", strip=True)) == "生日"
                ):
                    text = cells[1].get_text(" ", strip=True)
                    break
        match = re.search(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
        if not match:
            match = re.search(r"(?<!\d)(\d{1,2})[./-](\d{1,2})(?!\d)", text)
        if not match:
            return None
        month, day = map(int, match.groups())
        try:
            date(2000, month, day)
        except ValueError:
            return None
        return month, day

    async def _birthdays(self) -> list[tuple[str, int, int]]:
        cached = self._cache_get("birthdays")
        if cached is not None:
            return cached
        names = await self._category_members("超弦体")

        async def load(name: str):
            async with self._wiki_semaphore:
                html = await self._query_page_html(name)
            birthday = self._parse_birthday(html or "") if html else None
            return (name, *birthday) if birthday else None

        rows = [
            row for row in await asyncio.gather(*(load(name) for name in names)) if row
        ]
        logger.info(
            f"[KlbqWiki] 生日解析完成: roles={len(names)}, birthdays={len(rows)}"
        )
        return self._cache_set("birthdays", rows)

    async def _handle_fetch_resources(self, event: AstrMessageEvent):
        """更新图片资源：预下载所有角色的立绘和皮肤图到本地缓存。"""
        # 权限检查（仅管理员）
        if not event.is_admin:
            yield event.plain_result("仅管理员可使用更新资源功能。")
            return

        # 若缓存未启用，提示用户
        if not bool(self.config.get("image_cache", True)):
            yield event.plain_result(
                "⚠️ 当前图片缓存（image_cache）已关闭，预下载的图片不会被使用。\n"
                "请先在配置中开启 image_cache。"
            )
            return

        before = self._image_cache.stats()

        def format_bytes(n: int) -> str:
            if not n or n <= 0:
                return "0 B"
            units = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while n >= 1024 and i < len(units) - 1:
                n /= 1024
                i += 1
            return f"{n:.1f} {units[i]}" if n < 10 and i > 0 else f"{int(n)} {units[i]}"

        yield event.plain_result(
            f"📦 开始预下载全部角色立绘和皮肤图到本地...\n"
            f"当前缓存：{before['count']} 个文件，{format_bytes(before['size_bytes'])}\n"
            f"这可能需要几分钟，请耐心等待。"
        )

        start_time = time.time()
        try:
            role_names = await self._category_members("超弦体")
        except Exception as e:
            yield event.plain_result(f"❌ 获取角色列表失败：{e}")
            return

        total = len(role_names)
        if total == 0:
            yield event.plain_result("❌ 未找到任何角色。")
            return

        logger.info(f"[KlbqWiki] 开始预下载 {total} 个角色的资源")

        arts = 0
        skins = 0
        ok = 0
        fail = 0
        last_report = time.time()

        for idx, role in enumerate(role_names, 1):
            role_ok = 0
            role_fail = 0

            # 1. 角色立绘
            try:
                art = await self._get_character_art(role)
                if art and not art.startswith("http"):
                    arts += 1
                    role_ok += 1
                elif art:
                    role_fail += 1
            except Exception:
                role_fail += 1

            # 2. 皮肤图
            try:
                html = await self._query_page_html(role)
                if html:
                    skin_list = self._parse_skins(html)
                    for skin in skin_list:
                        try:
                            urls = await self._skin_images(role, skin["name"])
                            skins += len(urls)
                            for u in urls:
                                if u and not u.startswith("http"):
                                    role_ok += 1
                                elif u:
                                    role_fail += 1
                        except Exception:
                            pass
            except Exception:
                pass

            ok += role_ok
            fail += role_fail

            # 进度反馈：每 5 个角色或超过 15 秒
            now = time.time()
            if idx % 5 == 0 or now - last_report > 15:
                last_report = now
                try:
                    yield event.plain_result(
                        f"⏳ 进度：{idx}/{total}（{round(idx / total * 100)}%）\n当前：{role}"
                    )
                except Exception:
                    pass

        after = self._image_cache.stats()
        elapsed = f"{(time.time() - start_time):.1f}"
        new_count = max(0, after["count"] - before["count"])
        new_size = max(0, after["size_bytes"] - before["size_bytes"])

        yield event.plain_result(
            f"✅ 资源预下载完成！\n"
            f"\n📊 本次统计：\n"
            f"- 角色数量：{total}\n"
            f"- 立绘下载：{arts} 张\n"
            f"- 皮肤下载：{skins} 张\n"
            f"- 成功：{ok}，失败：{fail}\n"
            f"- 耗时：{elapsed} 秒\n"
            f"\n💾 本地缓存：\n"
            f"- 新增文件：{new_count} 个\n"
            f"- 新增大小：{format_bytes(new_size)}\n"
            f"- 总计文件：{after['count']} 个\n"
            f"- 总计大小：{format_bytes(after['size_bytes'])}\n"
            f"- 存储目录：{after['dir']}\n"
            f"\n之后查询角色和皮肤将直接读取本地缓存，图片加载速度大幅提升。"
        )

    async def _handle_birthday(self, event: AstrMessageEvent):
        rows = await self._birthdays()
        if not rows:
            raise RuntimeError("Wiki 暂无可解析的角色生日数据")
        today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
        upcoming = []
        for name, month, day in rows:
            year = today.year
            try:
                target = date(year, month, day)
            except ValueError:
                target = date(year, month, 28)
            if target < today:
                target = date(year + 1, month, day)
            upcoming.append(((target - today).days, month, day, name))
        count = max(1, min(20, int(self.config.get("birthday_count", 5) or 5)))
        upcoming.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
        upcoming = upcoming[:count]

        def when(days: int) -> str:
            if days == 0:
                return "今天"
            if days == 1:
                return "明天"
            return f"还有 {days} 天"

        def date_str(m: int, d: int) -> str:
            return f"{m}月{d}日"

        # 尝试图片渲染：获取最近生日角色的随机立绘
        if bool(self.config.get("render_image", True)):
            try:
                hero = upcoming[0]
                art_url = ""
                try:
                    art_url = await self._get_character_art(hero[3])
                except Exception as e:
                    logger.warning(f"[KlbqWiki] 获取 {hero[3]} 立绘失败: {e}")

                columns, card_width, timeout, fallback = self._render_settings()
                others = [
                    {
                        "name": name,
                        "date": date_str(month, day),
                        "countdown": when(days),
                    }
                    for days, month, day, name in upcoming[1:]
                ]
                render_task = self.html_render(
                    BIRTHDAY_TEMPLATE,
                    {
                        "title": "近期角色生日",
                        "kind": f"最近 {count} 个角色生日（Asia/Shanghai）",
                        "hero": {
                            "name": hero[3],
                            "date": date_str(hero[1], hero[2]),
                            "countdown": when(hero[0]),
                            "art": to_file_url(art_url) if art_url else "",
                        },
                        "others": others,
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
                image_url = await asyncio.wait_for(render_task, timeout=timeout + 1)
                if image_url:
                    yield event.image_result(image_url)
                    return
            except Exception as e:
                logger.warning(f"[KlbqWiki] 生日卡片渲染失败: {e}")
                if not fallback:
                    yield event.plain_result(f"生日卡片渲染失败：{e}")
                    return

        # 文字回退
        lines = [f"最近 {count} 个角色生日（Asia/Shanghai）："]
        for days, month, day, name in upcoming:
            lines.append(f"{date_str(month, day)}　{name}（{when(days)}）")
        text = "\n".join(lines)
        async for result in self._send_text_card(
            event, "近期角色生日", text, "生日查询"
        ):
            yield result

    async def _handle_cat_language(self, event: AstrMessageEvent):
        lines = self._cache_get("cat_language")
        if lines is None:
            html = await self._query_page_html("喵言喵语")
            if not html:
                raise RuntimeError("无法获取“喵言喵语”页面")
            soup = BeautifulSoup(html, "html.parser")
            nodes = soup.select(".CatLanguage > ul > li") or soup.select(
                ".CatLanguage li"
            )
            lines = []
            for node in nodes:
                for reference in node.select("sup.reference"):
                    reference.decompose()
                text = self._clean_text(node.get_text(" ", strip=True))
                if text:
                    lines.append(text)
            self._cache_set("cat_language", lines)
            logger.info(f"[KlbqWiki] 喵言喵语解析完成: count={len(lines)}")
        if not lines:
            raise RuntimeError("“喵言喵语”页面没有可解析内容")
        text = random.choice(lines)
        if not bool(self.config.get("cat_language_image", False)):
            yield event.plain_result(text)
            return
        async for result in self._send_text_card(event, "喵言喵语", text, "随机语录"):
            yield result

    async def _handle_season(self, event: AstrMessageEvent):
        html = await self._query_page_html("首页")
        if not html:
            raise RuntimeError("无法获取 Wiki 首页")
        soup = BeautifulSoup(html, "html.parser")
        timer = soup.select_one('.eventTimer[data-info="赛季"]')
        if not timer:
            raise RuntimeError("首页没有找到赛季计时器")
        card = timer.find_parent(class_="klbq-activity-card")
        title_node = (
            card.select_one(".klbq-activity-card__title, .title, h2, h3, h4")
            if card
            else None
        )
        if title_node:
            title = self._clean_text(title_node.get_text(" ", strip=True))
        elif card:
            card_text = self._clean_text(card.get_text(" ", strip=True))
            title = (
                card_text.split("赛季", 1)[0].strip(" ：:") + "赛季"
                if "赛季" in card_text
                else "当前赛季"
            )
        else:
            title = "当前赛季"
        end_raw = timer.get("data-end", "")
        if not end_raw:
            raise RuntimeError("赛季计时器缺少结束时间")
        normalized = end_raw.strip().replace("Z", "+00:00")
        try:
            end = datetime.fromisoformat(normalized)
        except ValueError:
            end = None
            for pattern in (
                "%Y/%m/%d %H:%M",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
            ):
                try:
                    end = datetime.strptime(end_raw.strip(), pattern)
                    break
                except ValueError:
                    continue
            if end is None:
                raise RuntimeError(f"无法解析赛季结束时间：{end_raw}")
        shanghai = ZoneInfo("Asia/Shanghai")
        end = (
            end.replace(tzinfo=shanghai)
            if end.tzinfo is None
            else end.astimezone(shanghai)
        )
        now = datetime.now(shanghai)
        seconds = int((end - now).total_seconds())
        status = (
            "已结束"
            if seconds <= 0
            else f"剩余 {seconds // 86400} 天 {(seconds % 86400) // 3600} 小时"
        )
        logger.info(f"[KlbqWiki] 赛季解析完成: title={title}, end={end.isoformat()}")
        text = f"状态：{status}\n结束时间：{end:%Y-%m-%d %H:%M}（Asia/Shanghai）"
        async for result in self._send_text_card(event, title, text, "赛季信息"):
            yield result

    async def _image_urls(self, filenames: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        titles = list(
            dict.fromkeys(
                f"文件:{name.removeprefix('文件:')}" for name in filenames if name
            )
        )
        for offset in range(0, len(titles), 50):
            data = await self._api_get(
                {
                    "action": "query",
                    "format": "json",
                    "formatversion": "2",
                    "redirects": "1",
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "titles": "|".join(titles[offset : offset + 50]),
                }
            )
            if not data:
                continue
            for page in data.get("query", {}).get("pages", []):
                info = page.get("imageinfo") or []
                if info and info[0].get("url"):
                    filename = page.get("title", "").removeprefix("文件:")
                    result[filename] = info[0]["url"]
                    result[filename.replace(" 背面", "_背面")] = info[0]["url"]
        return result

    async def _enhance_thumb(
        self, title: str, html: str, fields: dict[str, str], fallback: str
    ) -> str:
        try:
            soup = BeautifulSoup(html, "html.parser")
            is_weapon = self._is_weapon(fields, title)
            filenames: list[str] = []
            if is_weapon:
                user = (
                    fields.get("使用者") or fields.get("归属角色") or fields.get("角色")
                )
                if user:
                    filenames.append(f"{user}-weapon.png")
                scopes = soup.select(".weapon-table") or soup.select("table")
                for scope in scopes:
                    for image in scope.select("img"):
                        name = image.get("alt", "")
                        if name:
                            filenames.append(name)
            else:
                excluded = ("生日", "壁纸", "表情", "模型")
                for image in soup.select("img"):
                    name = unquote(image.get("alt", ""))
                    if (
                        title in name
                        and "立绘" in name
                        and not any(word in name for word in excluded)
                    ):
                        filenames.append(name)
                category = await self._api_get(
                    {
                        "action": "query",
                        "format": "json",
                        "formatversion": "2",
                        "generator": "categorymembers",
                        "gcmtitle": f"分类:{title}",
                        "gcmnamespace": "6",
                        "gcmlimit": "max",
                        "prop": "imageinfo",
                        "iiprop": "url",
                    }
                )
                urls = []
                for page in (category or {}).get("query", {}).get("pages", []):
                    name = page.get("title", "").removeprefix("文件:")
                    info = page.get("imageinfo") or []
                    if (
                        title in name
                        and "立绘" in name
                        and not any(word in name for word in excluded)
                        and info
                    ):
                        urls.append(info[0].get("url", ""))
                urls = [url for url in urls if url]
                if urls:
                    logger.info(
                        f"[KlbqWiki] 角色立绘候选: title={title}, count={len(urls)}"
                    )
                    return await self._image_cache.get(random.choice(urls))
            urls = list((await self._image_urls(filenames)).values())
            if urls:
                logger.info(
                    f"[KlbqWiki] 增强图片候选: title={title}, count={len(urls)}"
                )
                picked = urls[0] if is_weapon else random.choice(urls)
                return await self._image_cache.get(picked)
        except Exception as e:
            logger.warning(
                f"[KlbqWiki] 增强图片获取失败，使用原缩略图: title={title}, error={e}"
            )
        return await self._image_cache.get(fallback)

    async def _get_character_art(self, title: str) -> str:
        """获取角色的随机立绘 URL（通过分类查询，不依赖页面 HTML）。

        用于生日卡片等只需要角色立绘的场景。
        返回本地缓存路径（若启用缓存）或远程 URL，失败返回空字符串。
        """
        try:
            excluded = (
                "生日",
                "壁纸",
                "表情",
                "模型",
                "头像",
                "图标",
                "武器",
                "皮肤",
                "宿舍",
                "cg",
                "CG",
            )
            category = await self._api_get(
                {
                    "action": "query",
                    "format": "json",
                    "formatversion": "2",
                    "generator": "categorymembers",
                    "gcmtitle": f"分类:{title}",
                    "gcmnamespace": "6",
                    "gcmlimit": "max",
                    "prop": "imageinfo",
                    "iiprop": "url",
                }
            )
            urls = []
            for page in (category or {}).get("query", {}).get("pages", []):
                name = page.get("title", "").removeprefix("文件:")
                info = page.get("imageinfo") or []
                if (
                    title in name
                    and "立绘" in name
                    and not any(word in name for word in excluded)
                    and info
                ):
                    url = info[0].get("url", "")
                    if url:
                        urls.append(url)
            if urls:
                return await self._image_cache.get(random.choice(urls))
        except Exception as e:
            logger.warning(f"[KlbqWiki] 获取角色立绘失败: {e}")
        return ""

    def _parse_skins(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        group = soup.select_one(".klbq-skin-group")
        if not group:
            return []
        quality_names = {
            "0": "默认",
            "1": "普通",
            "2": "稀有",
            "3": "卓越",
            "4": "完美",
            "5": "传说",
            "6": "私服",
        }
        qualities: dict[str, str] = {}
        for item in group.select("li[data-quality]"):
            quality = quality_names.get(
                item.get("data-quality", ""), item.get("data-quality", "未知")
            )
            for link in item.select('a[href^="#skin_pane_"]'):
                qualities[self._clean_text(link.get_text(" ", strip=True))] = quality
        skins = []
        for pane in group.select('.tab-pane[id^="skin_pane_"]'):
            name = self._clean_text(
                pane.get("id", "").removeprefix("skin_pane_").replace("_", " ")
            )
            if not name:
                continue
            text = self._clean_text(pane.get_text(" ", strip=True))
            obtain = ""
            intro = ""
            for row in pane.select("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    label = self._clean_label(cells[0].get_text(" ", strip=True))
                    value = self._clean_text(cells[1].get_text(" ", strip=True))
                    if "获得" in label or "获取" in label:
                        obtain = value
                    elif "介绍" in label or "描述" in label:
                        intro = value
            skins.append(
                {
                    "name": name,
                    "quality": qualities.get(name, "未知"),
                    "intro": intro,
                    "obtain": obtain,
                    "text": text,
                }
            )
        logger.info(f"[KlbqWiki] 皮肤解析完成: count={len(skins)}")
        return skins

    async def _skin_images(self, role: str, skin: str) -> list[str]:
        names = [
            f"{role}时装-{skin}.jpg",
            f"{role}时装-{skin}_背面.jpg",
            f"{role}-{skin}立绘.png",
        ]
        urls = await self._image_urls(names)
        remote_urls = [urls[name] for name in names if name in urls]
        # 通过缓存批量转成本地路径，避免每次查询重复下载
        if remote_urls:
            return await self._image_cache.get_many(remote_urls)
        return []

    async def _handle_skin(
        self, event: AstrMessageEvent, role_query: str, skin_query: str
    ):
        role = self.aliases.get(role_query.casefold(), role_query)
        page = await self._query_page(role)
        if not page:
            found = await self._search_title(role)
            page = await self._query_page(found) if found else None
        if not page:
            text = f"未找到角色“{role_query}”。"
            async for result in self._send_text_card(
                event, "未找到角色", text, "查询提示"
            ):
                yield result
            return
        role = page.get("title") or role
        html = await self._query_page_html(role)
        if not html:
            raise RuntimeError(f"无法获取“{role}”角色页面")
        skins = self._parse_skins(html)
        if not skins:
            raise RuntimeError(f"“{role}”页面没有可解析的皮肤资料")
        skin_query = {"宿舍皮": "私服", "私皮": "私服"}.get(skin_query, skin_query)
        if skin_query == "皮肤":
            groups: dict[str, list[str]] = {}
            for skin in skins:
                groups.setdefault(skin["quality"], []).append(skin["name"])
            order = ["默认", "私服", "传说", "完美", "卓越", "稀有", "普通", "未知"]
            items = [
                {"label": quality, "value": "、".join(groups[quality])}
                for quality in order
                if quality in groups
            ]
            page_url = self._page_url(role)
            thumb = await self._enhance_thumb(
                role,
                html,
                {"名称": role},
                (page.get("thumbnail") or {}).get("source") or "",
            )
            _, _, timeout, text_fallback = self._render_settings()
            render_image = bool(self.config.get("render_image", True))
            logger.info(
                f"[KlbqWiki] 皮肤列表输出: role={role}, quality_count={len(items)}, "
                f"render_image={render_image}, timeout={timeout}s"
            )
            if render_image:
                image_url = await self._render_image(
                    role,
                    "皮肤列表",
                    items,
                    thumb,
                    "输入 /klbq 角色名 皮肤名 查询皮肤详情",
                )
                if image_url:
                    yield event.image_result(image_url)
                    if self.config.get("send_detail_link", True):
                        yield event.plain_result(page_url)
                    return
                if not text_fallback:
                    yield event.plain_result(
                        f"“{role}”皮肤列表图片渲染失败，请稍后重试。"
                    )
                    return
            lines = [f"{role}皮肤列表："]
            for item in items:
                lines.append(f"\n【{item['label']}】\n{item['value']}")
            yield event.plain_result("".join(lines))
            if self.config.get("send_detail_link", True):
                yield event.plain_result(page_url)
            return
        if skin_query == "私服":
            matches = [skin for skin in skins if skin["quality"] == "私服"]
        else:
            matches = [skin for skin in skins if skin["name"] == skin_query]
            if not matches:
                matches = [
                    skin
                    for skin in skins
                    if skin_query in skin["name"] or skin["name"] in skin_query
                ]
        if not matches:
            text = f"未找到“{role}”的皮肤“{skin_query}”。"
            async for result in self._send_text_card(
                event, "未找到皮肤", text, "查询提示"
            ):
                yield result
            return
        if len(matches) > 1:
            text = "找到多个候选：\n" + "\n".join(
                f"- {skin['name']}（{skin['quality']}）" for skin in matches
            )
            async for result in self._send_text_card(
                event, f"{role}皮肤候选", text, "皮肤查询"
            ):
                yield result
            return
        selected = matches[0]
        related = [selected]
        if selected["quality"] == "传说":
            base = selected["name"].split("-", 1)[0]
            related = [
                skin
                for skin in skins
                if skin["quality"] == "传说"
                and (skin["name"] == base or skin["name"].startswith(base + "-"))
            ]
        nodes = []
        sender = str(event.get_sender_id())
        image_count = 0
        for skin in related:
            urls = await self._skin_images(role, skin["name"])
            image_count += len(urls)
            details = [f"{role} · {skin['name']}", f"品质：{skin['quality']}"]
            if skin["intro"]:
                details.append(f"介绍：{skin['intro']}")
            if skin["obtain"]:
                details.append(f"获得方式：{skin['obtain']}")
            content = [Comp.Plain("\n".join(details))]
            content.extend(Comp.Image.fromURL(url) for url in urls)
            nodes.append(Comp.Node(uin=sender, name="卡拉彼丘 Wiki", content=content))
        logger.info(
            f"[KlbqWiki] 皮肤图片准备完成: role={role}, skin={selected['name']}, related={len(related)}, images={image_count}"
        )
        if not image_count:
            details = selected["intro"] or selected["obtain"] or "暂无更多文字资料。"
            anchor = self._page_url(role) + "#" + quote(f"skin_pane_{selected['name']}")
            text = f"{role} · {selected['name']}（{selected['quality']}）\n{details}"
            async for result in self._send_text_card(
                event, selected["name"], text, "皮肤详情"
            ):
                yield result
            if self.config.get("send_detail_link", True):
                yield event.plain_result(anchor)
            return
        yield event.chain_result([Comp.Nodes(nodes)])
        if self.config.get("send_detail_link", True):
            anchor = self._page_url(role) + "#" + quote(f"skin_pane_{selected['name']}")
            yield event.plain_result(anchor)

    @staticmethod
    def _help_text() -> str:
        return (
            "卡拉彼丘 Wiki 查询帮助\n"
            "\n【角色与武器】\n"
            "/klbq 心夏　查询角色资料\n"
            "/klbq 空境　查询武器资料\n"
            "/klbq 心夏武器　查询角色武器\n"
            "\n【皮肤】\n"
            "/klbq 心夏 皮肤　查看皮肤列表\n"
            "/klbq 心夏 休日冒险　查询指定皮肤\n"
            "/klbq 心夏 私服　查询私服皮肤\n"
            "宿舍皮、私皮等同于私服\n"
            "\n【其他】\n"
            "/klbq 生日　查看近期角色生日\n"
            "/klbq 赛季　查看赛季结束时间\n"
            "/klbq 喵言喵语　随机喵言喵语\n"
            "\n【管理（仅管理员）】\n"
            "/klbq 更新资源　预下载全部角色立绘和皮肤图到本地缓存\n"
            "\n支持 /卡拉彼丘 前缀和角色别名。"
        )

    async def _handle_query(self, event: AstrMessageEvent, query: str):
        logger.info(f"[KlbqWiki] 收到查询: query={query}")
        if not query or query.casefold() in {"help", "帮助"}:
            text = self._help_text()
            async for result in self._send_text_card(
                event, "使用帮助", text, "指令说明"
            ):
                yield result
            return

        try:
            if query in {"生日", "角色生日"}:
                logger.info(f"[KlbqWiki] 特殊查询分派: birthday, query={query}")
                async for result in self._handle_birthday(event):
                    yield result
                return
            if query in {"喵言喵语", "随机喵言喵语"}:
                logger.info(f"[KlbqWiki] 特殊查询分派: cat_language, query={query}")
                async for result in self._handle_cat_language(event):
                    yield result
                return
            if query in {"赛季", "赛季结束"}:
                logger.info(f"[KlbqWiki] 特殊查询分派: season, query={query}")
                async for result in self._handle_season(event):
                    yield result
                return
            if query in {"更新资源", "缓存资源", "预下载"}:
                logger.info(f"[KlbqWiki] 特殊查询分派: fetch_resources, query={query}")
                async for result in self._handle_fetch_resources(event):
                    yield result
                return
            parts = query.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in {"武器", "的武器"}:
                query = f"{parts[0]}武器"
            elif len(parts) == 2:
                logger.info(
                    f"[KlbqWiki] 特殊查询分派: skin, role={parts[0]}, skin={parts[1]}"
                )
                async for result in self._handle_skin(event, parts[0], parts[1]):
                    yield result
                return

            page = await self._lookup(query)
            if not page:
                search_url = PAGE_URL.format("Special:%E6%90%9C%E7%B4%A2?") + urlencode(
                    {"search": query}
                )
                logger.info(
                    f"[KlbqWiki] 未找到条目: query={query}, search_url={search_url}"
                )
                text = f"未找到“{query}”的卡拉彼丘 Wiki 条目。"
                async for result in self._send_text_card(
                    event, "未找到条目", text, "查询提示"
                ):
                    yield result
                yield event.plain_result(search_url)
                return

            title = page.get("title") or self.aliases.get(query.casefold(), query)
            page_url = self._page_url(title)
            logger.info(f"[KlbqWiki] 准备解析页面: title={title}, url={page_url}")
            html = await self._query_page_html(title)
            logger.info(
                f"[KlbqWiki] HTML 获取结果: title={title}, has_html={bool(html)}, html_len={len(html or '')}"
            )
            fields = self._extract_info(html or "", title) if html else {"名称": title}
            if not fields.get("简介"):
                extract = self._clean_text(page.get("extract") or "")
                if extract:
                    fields["简介"] = extract[:220].rstrip() + (
                        "..." if len(extract) > 220 else ""
                    )
            fallback_thumb = (page.get("thumbnail") or {}).get("source") or ""
            thumb = await self._enhance_thumb(title, html or "", fields, fallback_thumb)
            logger.info(
                f"[KlbqWiki] 解析完成: title={title}, fields={list(fields.keys())}, thumb={bool(thumb)}, enhanced={thumb != fallback_thumb}"
            )

            async for result in self._send_result(
                event, title, page_url, fields, thumb
            ):
                yield result
        except Exception as e:
            logger.error(
                f"[KlbqWiki] 查询异常: query={query}, error={e}\n{traceback.format_exc()}"
            )
            text = f"查询“{query}”时发生错误，已写入后台日志。"
            async for result in self._send_text_card(
                event, "查询失败", text, "错误提示"
            ):
                yield result

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
