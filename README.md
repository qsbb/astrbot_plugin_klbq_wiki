# 卡拉彼丘 Wiki 查询

[![AstrBot Plugin](https://img.shields.io/badge/AstrBot-Plugin-4c8bf5)](https://astrbot.app/)
[![Version](https://img.shields.io/badge/version-1.4.3-5c6ac4)](https://github.com/qsbb/astrbot_plugin_klbq_wiki)

一个面向 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 的卡拉彼丘资料查询插件。数据来自卡拉彼丘 Biligame Wiki，支持角色、武器、皮肤、近期生日、当前赛季和喵言喵语查询。

- 插件名称：`astrbot_plugin_klbq_wiki`
- 当前版本：`1.4.3`
- 作者：凌溪
- 项目地址：<https://github.com/qsbb/astrbot_plugin_klbq_wiki>

## 功能特性

- 查询角色资料、背景信息和角色武器
- 查询武器类型、射速、弹匣、移速、换弹时间和分距离部位伤害等数据
- 内置全部角色的常用简称、社区昵称及常见错字
- 查询角色皮肤列表、指定皮肤、宿舍皮和私服皮肤
- 合并发送皮肤模型正面、模型背面和立绘
- 传说皮肤自动合并基础形态及各进阶形态
- 查询近期角色生日、当前赛季及结束时间
- 从 Wiki 随机获取一条喵言喵语
- 将角色和武器资料渲染为图片卡片
- 图片渲染超时或失败时支持文字回退
- 支持调整图片宽度、每行格子数和渲染超时
- 支持用户自定义别名

## 安装

### 从 AstrBot 插件市场安装

1. 打开 AstrBot WebUI。
2. 进入 **插件市场**。
3. 搜索“卡拉彼丘 Wiki 查询”。
4. 点击安装，并按提示重载插件。

依赖会由 AstrBot 根据 `requirements.txt` 自动安装。

### 手动安装

进入 AstrBot 的插件目录并克隆本仓库：

```bash
git clone https://github.com/qsbb/astrbot_plugin_klbq_wiki.git
```

也可以下载仓库压缩包，将解压后的插件目录放入：

```text
AstrBot/data/plugins/astrbot_plugin_klbq_wiki
```

随后安装依赖并重启或重载插件：

```bash
pip install -r requirements.txt
```

## 指令说明

插件同时支持以下两个命令前缀：

```text
/klbq
/卡拉彼丘
```

下表统一使用 `/klbq` 演示。

### 角色与武器

| 指令 | 说明 | 示例 |
| --- | --- | --- |
| `/klbq <角色>` | 查询角色资料 | `/klbq 心夏` |
| `/klbq <武器>` | 查询武器资料 | `/klbq 空境` |
| `/klbq <角色>武器` | 查询该角色使用的武器 | `/klbq 心夏武器` |
| `/klbq <角色>的武器` | 查询该角色使用的武器 | `/klbq 心夏的武器` |
| `/klbq <角色> 武器` | 空格形式的角色武器查询 | `/klbq 心夏 武器` |

角色和武器查询默认返回图片卡片。角色卡会随机展示当前角色的 Wiki 立绘，武器卡会优先展示透明武器图。

### 皮肤

| 指令 | 说明 | 示例 |
| --- | --- | --- |
| `/klbq <角色> 皮肤` | 按品质列出角色全部皮肤 | `/klbq 心夏 皮肤` |
| `/klbq <角色> <皮肤名>` | 查询指定皮肤，支持包含匹配 | `/klbq 心夏 休日冒险` |
| `/klbq <角色> 宿舍皮` | 查询通过宿舍获得的皮肤 | `/klbq 心夏 宿舍皮` |
| `/klbq <角色> 私皮` | 查询 Wiki 中的私服品质皮肤 | `/klbq 心夏 私皮` |

指定皮肤查询会通过合并消息发送 Wiki 中实际存在的图片：

- 模型正面
- 模型背面
- 皮肤立绘

Wiki 没有统一的模型侧面资源，因此插件使用标准公开的模型背面图。部分皮肤可能缺少某类图片，插件只发送实际存在的资源。

传说品质皮肤会自动查找并合并发送基础形态和所有进阶、换色形态。

### 生日、赛季与喵言喵语

| 指令 | 说明 |
| --- | --- |
| `/klbq 生日` | 返回最近几位即将过生日的角色 |
| `/klbq 角色生日` | 与 `/klbq 生日` 相同 |
| `/klbq 赛季` | 返回当前赛季名称、剩余时间和结束日期 |
| `/klbq 赛季结束` | 与 `/klbq 赛季` 相同 |
| `/klbq 喵言喵语` | 从 Wiki 随机发送一条喵言喵语 |
| `/klbq 随机喵言喵语` | 与 `/klbq 喵言喵语` 相同 |

所有查询都必须使用 `/klbq` 或 `/卡拉彼丘` 前缀，避免与其他插件的全局指令冲突。

生日按照 `Asia/Shanghai` 时区计算。角色生日和喵言喵语数据会在内存中缓存 6 小时，以减少对 Wiki 的重复请求。

## 别名支持

内置别名可直接用于角色、角色武器和皮肤查询，例如：

```text
/klbq 奶妈
/klbq 哈基米武器
/klbq LV 皮肤
/klbq 盾构 宿舍皮
```

英文别名不区分大小写，例如 `lv`、`LV` 和 `Lv` 均可查询拉薇。

如需补充自己的别名，可在插件配置的 `custom_aliases` 中按行填写：

```text
心夏老师=心夏
空境武器=空境
```

格式为：

```text
别名=Wiki 页面标题
```

自定义英文别名同样不区分大小写。后填写的自定义别名会覆盖同名内置别名。

## 配置项

安装后可在 AstrBot WebUI 的插件配置页面修改以下选项：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `birthday_count` | 整数 | `5` | 生日查询返回的角色数量，范围 1–20 |
| `render_image` | 布尔 | `true` | 是否将角色和武器资料渲染为图片卡片 |
| `send_detail_link` | 布尔 | `true` | 图片发送后是否补充 Wiki 详情链接 |
| `image_timeout` | 浮点数 | `8` | 图片渲染超时时间，范围 1–60 秒 |
| `text_fallback` | 布尔 | `true` | 图片渲染失败或超时后是否发送文字结果 |
| `grid_columns` | 整数 | `2` | 图片卡片每行资料格子数，范围 1–4 |
| `card_width` | 整数 | `760` | 图片卡片最小宽度，范围 420–1200 像素 |
| `custom_aliases` | 多行文本 | 空 | 自定义别名，每行填写一条映射 |

### 推荐配置

面向手机端 QQ 查看时，推荐：

```text
grid_columns = 2
card_width = 760
image_timeout = 8
text_fallback = true
```

如果网络较慢或 Wiki 响应不稳定，可适当提高 `image_timeout`。不需要图片卡片时，可以关闭 `render_image`。

## 输出与平台兼容

- 角色与武器资料使用 AstrBot 的 HTML 图片渲染能力。
- 皮肤详情使用 AstrBot 合并消息组件发送。
- 合并消息的实际表现取决于消息平台和适配器能力。
- 不支持合并消息的平台可能无法完整展示皮肤详情。
- 所有查询均需要 AstrBot 所在环境能够访问 Biligame Wiki 及其图片域名。

## 常见问题

### 指令没有响应

1. 确认插件已在 AstrBot WebUI 中启用。
2. 重载插件或重启 AstrBot。
3. 检查后台是否出现以 `[KlbqWiki]` 开头的日志。
4. 确认命令与参数之间有空格，例如 `/klbq 心夏`。
5. 检查是否有其他插件提前拦截了同名指令。

### 图片渲染超时

可以在插件配置中提高 `image_timeout`，并保持 `text_fallback` 开启。超时后插件会发送文字结果。

### 图片或资料缺失

插件展示的数据和图片来自 Wiki。页面字段未填写、图片尚未上传或 Wiki 页面结构变化时，部分内容可能无法显示。

### 查询皮肤时没有某个视图

插件只发送 Wiki 中实际存在的模型正面、模型背面和立绘。并非所有皮肤都同时具备三类图片，传说进阶形态也不一定拥有独立立绘。

### 如何增加新别名

优先使用插件设置中的 `custom_aliases`，无需修改代码。格式为每行一条 `别名=页面标题`。

## 数据来源与免责声明

本插件的数据来自：

- [卡拉彼丘 Biligame Wiki](https://wiki.biligame.com/klbq/)
- [卡拉彼丘 Biligame Wiki API](https://wiki.biligame.com/klbq/api.php)

本项目是非官方社区插件，与《卡拉彼丘》官方及 Biligame Wiki 运营方无隶属关系。游戏名称、角色、图片及相关素材的权利归其各自权利人所有。

Wiki 内容可能因版本更新、页面维护或数据延迟发生变化，请以游戏内信息和官方公告为准。

## 更新日志

版本变更请查看 [CHANGELOG.md](./CHANGELOG.md)。

## 反馈与贡献

遇到问题或希望补充别名、字段和查询功能，可以在 GitHub 提交 Issue：

<https://github.com/qsbb/astrbot_plugin_klbq_wiki/issues>

反馈问题时建议附上：

- AstrBot 版本
- 插件版本
- 使用的平台与适配器
- 完整指令
- `[KlbqWiki]` 相关后台日志
- 问题截图
