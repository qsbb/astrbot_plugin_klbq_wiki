# astrbot_plugin_klbq_wiki

卡拉彼丘 Wiki 查询插件。

作者：凌溪

## 功能

- 使用命令 `/卡拉彼丘 角色名/武器` 查询卡拉彼丘 Biligame Wiki
- 优先提取页面结构化信息
- 提取不到结构化内容时，自动回退到页面简介
- 返回详情页链接，便于继续查看

## 用法

```text
/卡拉彼丘 米雪儿
/卡拉彼丘 汐
/卡拉彼丘 彩绘
```

## 安装

1. 将插件目录放到 AstrBot 的 `plugin` 目录下
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 重启 AstrBot

## 说明

插件会访问：

- https://wiki.biligame.com/klbq/%E9%A6%96%E9%A1%B5
- https://wiki.biligame.com/klbq/api.php

如果某个页面没有明显简介，插件会尝试从页面信息框中提取字段并按固定模板输出。
