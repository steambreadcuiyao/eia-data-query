# eia-data-query

**EIA Open Data Query Skill** — 美国能源信息署(EIA) API v2 一站式查询技能 / A one-stop query skill for all EIA API v2 datasets.

用一条命令浏览/查询 EIA API v2 的 **14 大类、232 个数据端点**,自动处理 URL 编码、facet 枚举、列名差异、分页与限流。

> Query/browse all EIA API v2 datasets (14 top-level categories, 232 data endpoints) with a single CLI tool — handling URL-encoding, facet enumeration, per-endpoint column names, pagination and rate-limiting automatically.

## 覆盖数据(Coverage)

| 类别 | 内容 | 最高频率 |
|---|---|---|
| Petroleum 石油 | 库存/产量/进出口/炼化/价格(现货、零售)/周报四件套 | 日 |
| Natural Gas 天然气 | 库存/产量/消费/进出口/Henry Hub 价格 | 日 |
| Electricity 电力 | 需求/日前预测/净发电/区域交换/分燃料(930)、零售/机组容量 | 小时 |
| Nuclear Outages 核电 | 全美/电厂/机组级停运 | 日 |
| Prices 价格 | WTI/Brent 现货、汽油柴油零售、STEO 预测价 | 日 |
| STEO / AEO / IEO | 短期/长期官方能源展望(含预测值) | 月/年 |
| Coal / SEDS / Total Energy | 煤炭、州级年度全景(含 CO2)、全国月度总能源 | 季/年 |
| International 国际 | 268 国产量/进口/消费(IEO/SEP 体系) | 月 |

## 结构(Files)

```
eia-data-query/
├── SKILL.md              # 技能主文档:使用时机、Key 配置、路由速查表、坑清单
├── workbuddy.json        # 技能元数据
└── scripts/
    └── eia_query.py      # 查询工具(routes / meta / facets / data / setup / key)
```

## 首次配置 API Key(Setup)

Key 查找顺序:`--key` 参数 → 环境变量 `EIA_API_KEY` → `~/.eia_api_key`。免费申请:[eia.gov/opendata](https://www.eia.gov/opendata/)

```bash
python3 scripts/eia_query.py setup --key <YOUR_EIA_API_KEY>
python3 scripts/eia_query.py key     # 验证
```

## 快速上手(Quick Start)

```bash
# 浏览路由树
python3 scripts/eia_query.py routes petroleum/pri --depth 1

# 看端点元数据(频率/facet/列/单位)
python3 scripts/eia_query.py meta nuclear-outages/us-nuclear-outages

# 枚举 facet 合法值
python3 scripts/eia_query.py facets nuclear-outages/generator-nuclear-outages facility --filter PERRY

# 取数(自动分页 / CSV 导出)
python3 scripts/eia_query.py data petroleum/pri/spt --freq daily --facet series=RWTC,RBRTE --limit 5
python3 scripts/eia_query.py data natural-gas/stor/wkly --freq weekly --facet duoarea=R48 --facet process=SWO --start 2026-01-01 --csv ng.csv
```

依赖:仅 python3 + requests。限流 5,000 请求/小时(脚本内置 0.15s 间隔)。

## 已知坑(详见 SKILL.md)

- facets 的 `[]` 必须 URL 编码;`data[0]=<列名>` 必传且**列名因端点而异**(value/quantity/percentOutage/production…)
- 电力 rto 日级数据不传 timezone facet 会返回 5 份重复
- 核电 facility、煤炭 sector 的 facet 值是**数字码**;international 必须带齐全部维度
- **期货价格系列 2024-04 已停更**,现价追踪用现货系列(RWTC / RBRTE / RNGWHHD)

## License

MIT
