---
name: eia-data-query
description: >-
  EIA Open Data Query — 美国能源信息署(EIA) API v2 数据查询技能。统一封装石油、天然气、电力、煤炭、
  核电停运、价格(现货/期货/零售)、STEO 短期能源展望、Total Energy(MER)、SEDS 州数据、国际数据(IEO/SEP)、
  AEO/IEO 展望共 14 大类 230+ 数据端的浏览、facet 枚举、取数、自动分页与 CSV 导出。
  首次使用需配置 API Key。Use when the user asks about US energy data, EIA data, crude oil/gasoline/natural gas prices,
  petroleum inventories, power grid demand/generation, nuclear outages, coal, STEO forecasts, or international energy statistics.
description_zh: "查询美国能源信息署(EIA) API v2 全部数据:石油/天然气/电力/煤炭/核电停运/能源价格/STEO预测/州数据/国际数据"
description_en: "Query all EIA API v2 datasets: petroleum, natural gas, electricity, coal, nuclear outages, prices, STEO, SEDS, international"
version: 1.0.0
allowed-tools: Read,Bash,Glob,Grep
display_name: "EIA 美国能源数据查询"
display_name_en: "EIA Open Data Query"
visibility: "public"
---

# EIA 数据查询技能(eia-data-query)

> **一句话概述**:用一条命令浏览/查询美国能源信息署(EIA) API v2 的全部 14 大类能源数据(232 个数据端点),自动处理 URL 编码、facet 枚举、列名差异、分页与限流。

## 何时使用本技能

- 查询美国能源数据:原油/油品/天然气/煤炭库存、产量、进出口、消费
- 查询能源价格:WTI/布伦特现货、Henry Hub 天然气现货、零售汽油价格(STEO 预测价格)
- 查询电网数据:电力需求/发电/区域交换(小时/日)、核电机组停运
- 查询国际能源统计:各国原油产量/进口(IEO/SEP 体系)
- 需要美国官方口径的能源预测(STEO/AEO/IEO)

## 首次使用:配置 API Key(必做)

脚本按以下顺序自动查找 Key,命中即用:
1. 命令行参数 `--key <KEY>`
2. 环境变量 `EIA_API_KEY`
3. 本地文件 `~/.eia_api_key`(推荐一次性写入)

配置方式(任选一):

```bash
# 一次性写入文件(推荐):
python3 <技能目录>/scripts/eia_query.py setup --key <KEY>
# 或临时用环境变量:
export EIA_API_KEY=<KEY>
# 验证:
python3 <技能目录>/scripts/eia_query.py key
```

> Key 免费申请:eia.gov/opendata。限流 5,000 请求/小时,脚本已内置 0.15s 间隔。

## 快速上手

脚本路径:`<技能目录>/scripts/eia_query.py`(下称 `eq`),仅依赖 python3 + requests。

```bash
EQ="<技能目录>/scripts/eia_query.py"

# 1) 浏览路由树(任意层级下钻)
python3 $EQ routes                        # 顶层 14 条
python3 $EQ routes petroleum/pri --depth 1

# 2) 看端点元数据(频率/facets/data 列/单位)——查数前必看
python3 $EQ meta nuclear-outages/us-nuclear-outages
python3 $EQ meta electricity/rto/daily-region-data

# 3) 枚举 facet 合法值(不确定 facet 值时先用这个)
python3 $EQ facets nuclear-outages/generator-nuclear-outages facility --filter PERRY
python3 $EQ facets steo seriesId --filter BRE          # STEO 1469 个系列中找布伦特

# 4) 取数(自动分页,默认输出 JSON 行)
#    --facet 可重复;多值用逗号 key=v1,v2;--cols 指定 data 列
python3 $EQ data petroleum/pri/spt --freq daily --facet series=RWTC --limit 5
python3 $EQ data nuclear-outages/us-nuclear-outages --cols percentOutage --limit 5
python3 $EQ data natural-gas/stor/wkly --freq weekly --facet duoarea=R48 --facet process=SWO --start 2026-01-01 --csv /tmp/ng_stock.csv
python3 $EQ data coal/consumption-and-quality --freq quarterly --facet location=US --facet sector=98 --cols consumption,price --limit 3

# 5) Key 管理
python3 $EQ setup --key <KEY>
python3 $EQ key
```

## 路由速查表(实测验证)

### 高频日/周级(适合每日自动化)
| 端点 | 频率 | data 列 | 关键 facet 组合 |
|---|---|---|---|
| `electricity/rto/daily-region-data` | 日 | value | respondent=US48, timezone=Eastern, type=D,DF,NG,TI |
| `electricity/rto/daily-fuel-type-data` | 日 | value | respondent=US48, fueltype=16 码, timezone=Eastern |
| `nuclear-outages/us-nuclear-outages` | 日 | **percentOutage**(或 capacity/outage) | 无 facet |
| `nuclear-outages/generator-nuclear-outages` | 日 | percentOutage | facility=**数字码**(先枚举) |
| `petroleum/pri/spt` | 日 | value | series=**RWTC**(WTI)、**RBRTE**(布伦特) |
| `natural-gas/pri/fut` | 日 | value | series=**RNGWHHD**(HH 现货,duoarea=RGC,process=PS0) |
| `petroleum/pri/gnd` | 周 | value | duoarea=NUS, product=EPMR, process=**PTE**(零售) |
| `petroleum/sum/sndw`、`move/wkly`、`move/wimpc`、`stoc/wstk` | 周 | value | duoarea/product/process/series(石油四件套) |
| `natural-gas/stor/wkly` | 周 | value | duoarea=R48, process=SWO |

### 月度级
| 端点 | data 列 | 说明 |
|---|---|---|
| `steo`(seriesId 1469 个) | value | ⭐ 官方月度预测,含未来 24 个月(BREPUUS/WTIPUUS/MGRARUS…) |
| `total-energy`(msn 984 个) | value | 全国月度全品种生产/消费/库存/CO2(ELETPUS 电力净发电…) |
| `crude-oil-imports` | **quantity** | 月度原油进口 by 来源国×品质(gradeId=LSW/MED/HEAVY…),55.7 万行 |
| `international` | value | 全球分国数据:**产量 57×1 实测完整**(不带 countryRegionId 即可拉全量国家);消费仅 54×2(年度覆盖 179 国/月度仅 OECD)、进口仅 OECD 系列 78x——存在结构性数据缺口(无中印),详见坑 5/9/10;countryRegionTypeId=**c**(国家) |
| `natural-gas/pri/sum`、`prod/sum`、`cons/sum`、`sum/snd`、`move/*`、`stor/*` | value | 天然气月度全家桶,与 stor/wkly 同构 |
| `densified-biomass/*` | **production** 等 | 木质颗粒月报 |

### 年/季级
| 端点 | 说明 |
|---|---|
| `coal/*`(12 数据集) | 煤炭:consumption-and-quality(sector=**数字码**,98=电力)、exports-imports(data=quantity,price)、mine-production 等 |
| `seds`(seriesId 968 × stateId) | 州年度能源全景,**CO2 官方新家**(co2-emissions 路由已 deprecated) |
| `aeo/2026`、`ieo/2023` | 长期展望(facets: history/scenario/tableId/seriesId/regionId) |
| `electricity/retail-sales`、`electric-power-operational-data`、`operating-generator-capacity`、`facility-fuel`、`state-electricity-profiles/*` | 电力月/季/年 |

### 快捷路由
`seriesid/{SERIES_ID}`(如 `PET.WCSSTUS1.W`)——已知 v1 系列码的快速验证,仅返回最近窗口。

## 必知坑清单(脚本已规避,手工 curl 时注意)

1. **facets 的 `[]` 必须 URL 编码**(%5B%5D),curl 字面量返回空;用本技能脚本自动规避。
2. **`data[0]=<列名>` 必传且列名因端点而异**:`value`(多数)/`quantity`(crude-oil-imports、coal 进出口)/`percentOutage`(核电)/`production`(生物质)。传错返回 400 并列出合法列名,可借报错自省;或先跑 `meta`。
3. **日级 rto 端点不传 timezone facet 返回 5 份重复**(每时区一份)。
4. **facet 值先枚举再查询**:核电 facility 与煤炭 sector 都是数字码;international 用数字 productId 与小写 typeId。
5. **international 部分组合是数据缺口而非查询错误**(2026-09 实测):原油×消费(57×2)、总油品×消费(53×2)等**全频率 total=0**;全球分国进口不存在(仅 OECD 系列 78x,且仅 8-17 行);月度消费(54×2)仅 36 个 OECD 国家且多为 w 缺数;**中国、印度不在本数据集**(源自 JODI 体系,中印不提交)。产量(57×1)不带 countryRegionId 即可拉全量国家。
6. **期货价格系列 2024-04 已停更**(RCLC1/RNGC1),现价追踪一律用现货系列(RWTC/RBRTE/RNGWHHD)。
7. period 格式:年 `YYYY`、季 `YYYY-"Q"Q`、月 `YYYY-MM`、周/日 `YYYY-MM-DD`、小时 `YYYY-MM-DDTHH24`(UTC)/`LH` 后缀(本地)。
8. 单请求上限 5000 行,需要更多用 `--all` 自动翻页;限流 5,000 次/小时。
9. **international 年度数据 5 种单位混存**(MT/MTOE/QBTU/TBPD/TJ,每国每年每单位一行),跨单位比较前必须按 `unit=TBPD` 过滤;月度数据仅 TBPD。
10. **international 月度国际数据发布滞后约 3 个月**(9 月中旬最新为 5 月);年度数据滞后约 1 年。

## 数据新鲜度(实测)

- 电力 930 / 核电停运:T-1 数据美东当天早 7 点(北京 19-20 点)定稿,末行"进行中日"部分列有值属正常
- 石油周报:周三发布(节假日顺延),周五为周截止
- 天然气周报:周四发布
- 月度数据:次月月底前后陆续发布(STEO 每月第一个周二更新)
- 价格现货:WTI/HH 止于最近交易日

## 输出约定

- `data` 命令默认按 period 降序输出 JSON(每行一条),`--csv` 导出全量
- 所有命令失败时 stderr 输出原因;404/路由变更时先跑上级 `routes` 重新发现入口

## 报告模板

- `templates/intl_top_report.py`:international 三维度(产量/消费/净进口)Top20 HTML 报告生成器(2026-09 实战验证)。含:大区间全量拉取→本地排序 Top20(单页 5000 行内 1 次请求)、5 期 sparkline 趋势、环比/首尾变化着色(涨红跌绿)、中国行高亮、年度多单位过滤(unit=TBPD)、缺数标记(w)处理、数据限制标注。复用时改文件头常量(SRC/OUT/月份区间/口径)。查询策略:先小 limit 探最新 period,再按 period 大区间一次拉全量国家,本地排序取 Top20——不要试图让 API 按 value 排序。
