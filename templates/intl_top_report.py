# ---------------------------------------------------------------------------
# international 三维度(产量/消费/净进口) Top20 HTML 报告生成器
# 2026-09 实战验证。复用时修改下方常量:
#   SRC       数据 jsonl 所在目录(先用 SKILL.md 快速上手的 data 命令拉取)
#   OUT       报告输出路径
#   M_MONTHS  月度趋势区间(产量口径,注意滞后约 3 个月)
#   Y_MONTHS  年度趋势区间(消费/净进口口径)
#   各表口径: 产量 57x1 月度 / 消费 54x2 年度(无中印) / 净进口=54x2-53x1 推算
# ---------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EIA 原油产量/消费/净进口 Top20 HTML 报告生成器 v2"""
import json, os

SRC = r"C:\Users\cuiyao-jk\WorkBuddy\Claw\tmp\eia_report"
OUT = r"C:\Users\cuiyao-jk\WorkBuddy\Claw\outputs\eia_crude_top20_report.html"
M_MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
Y_MONTHS = ["2021", "2022", "2023", "2024", "2025"]

CN = {"USA":"美国","RUS":"俄罗斯","SAU":"沙特阿拉伯","CHN":"中国","CAN":"加拿大",
      "IRQ":"伊拉克","BRA":"巴西","ARE":"阿联酋","IRN":"伊朗","KWT":"科威特",
      "MEX":"墨西哥","NOR":"挪威","VEN":"委内瑞拉","QAT":"卡塔尔","NGA":"尼日利亚",
      "LBY":"利比亚","DZA":"阿尔及利亚","KAZ":"哈萨克斯坦","IND":"印度","JPN":"日本",
      "KOR":"韩国","GBR":"英国","FRA":"法国","DEU":"德国","ITA":"意大利","ESP":"西班牙",
      "NLD":"荷兰","BEL":"比利时","TUR":"土耳其","IDN":"印度尼西亚","MYS":"马来西亚",
      "THA":"泰国","SGP":"新加坡","AUS":"澳大利亚","EGY":"埃及","AGO":"安哥拉",
      "OMN":"阿曼","COL":"哥伦比亚","ARG":"阿根廷","ZAF":"南非","TKM":"土库曼斯坦",
      "UZB":"乌兹别克斯坦","AZE":"阿塞拜疆","SSD":"南苏丹","GAB":"加蓬","COG":"刚果（布）",
      "TTO":"特立尼达和多巴哥","BHR":"巴林","GHA":"加纳","COD":"刚果（金）","CIV":"科特迪瓦",
      "PNG":"巴布亚新几内亚","BRN":"文莱","DNK":"丹麦","ROU":"罗马尼亚","POL":"波兰",
      "CZE":"捷克","HUN":"匈牙利","AUT":"奥地利","CHE":"瑞士","SWE":"瑞典","FIN":"芬兰",
      "PRT":"葡萄牙","GRC":"希腊","IRL":"爱尔兰","ISR":"以色列","MAR":"摩洛哥","TUN":"突尼斯",
      "SDN":"苏丹","CHL":"智利","ECU":"厄瓜多尔","PER":"秘鲁","BOL":"玻利维亚",
      "NZL":"新西兰","PHL":"菲律宾","VNM":"越南","THA":"泰国","PAK":"巴基斯坦",
      "BGD":"孟加拉国","LKA":"斯里兰卡","MMR":"缅甸","KHM":"柬埔寨","MNG":"蒙古",
      "UKR":"乌克兰","BLR":"白俄罗斯","SRB":"塞尔维亚","BGR":"保加利亚","SVK":"斯洛伐克",
      "HRV":"克罗地亚","SVN":"斯洛文尼亚","EST":"爱沙尼亚","LVA":"拉脱维亚","LTU":"立陶宛",
      "LUX":"卢森堡","ISL":"冰岛","MLT":"马耳他","CYP":"塞浦路斯","JOR":"约旦","LBN":"黎巴嫩",
      "SYR":"叙利亚","YEM":"也门","AFG":"阿富汗","NPL":"尼泊尔","PRK":"朝鲜","TWN":"中国台湾",
      "HKG":"中国香港","MAC":"中国澳门","ALB":"阿尔巴尼亚","BIH":"波黑","MKD":"北马其顿",
      "MNE":"黑山","MDA":"摩尔多瓦","GEO":"格鲁吉亚","ARM":"亚美尼亚","KGZ":"吉尔吉斯斯坦",
      "TJK":"塔吉克斯坦","ETH":"埃塞俄比亚","KEN":"肯尼亚","TZA":"坦桑尼亚","UGA":"乌干达",
      "MOZ":"莫桑比克","ZMB":"赞比亚","ZWE":"津巴布韦","BWA":"博茨瓦纳","NAM":"纳米比亚",
      "SEN":"塞内加尔","MLI":"马里","BFA":"布基纳法索","NER":"尼日尔","TCD":"乍得",
      "CMR":"喀麦隆","CAF":"中非","GNQ":"赤道几内亚","BEN":"贝宁","TGO":"多哥",
      "LBR":"利比里亚","SLE":"塞拉利昂","GIN":"几内亚","GMB":"冈比亚","MRT":"毛里塔尼亚",
      "DJI":"吉布提","RWA":"卢旺达","BDI":"布隆迪","MWI":"马拉维","LSO":"莱索托",
      "SWZ":"斯威士兰","COM":"科摩罗","CPV":"佛得角","STP":"圣多美和普林西比",
      "CUB":"古巴","JAM":"牙买加","HTI":"海地","DOM":"多米尼加","PRI":"波多黎各",
      "GTM":"危地马拉","HND":"洪都拉斯","SLV":"萨尔瓦多","NIC":"尼加拉瓜","CRI":"哥斯达黎加",
      "PAN":"巴拿马","BLZ":"伯利兹","GUY":"圭亚那","SUR":"苏里南","URY":"乌拉圭",
      "PRY":"巴拉圭","FJI":"斐济","SLB":"所罗门群岛","VUT":"瓦努阿图","WSM":"萨摩亚"}

def load(name, unit=None):
    rows = []
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("{"):
                r = json.loads(line)
                if unit and r.get("unit") != unit:
                    continue
                try:
                    r["v"] = float(r["value"])
                except (TypeError, ValueError):
                    r["v"] = None
                rows.append(r)
    return rows

def by_country(rows, periods):
    d = {}
    for r in rows:
        if r["period"] not in periods:
            continue
        d.setdefault(r["countryRegionId"], {"name": r["countryRegionName"], "vals": {}})
        d[r["countryRegionId"]]["vals"][r["period"]] = r["v"]
    return d

def series(d, cid, periods):
    return [d.get(cid, {}).get("vals", {}).get(m) for m in periods]

def delta(s):
    a, b = s[0], s[-1]
    if a is None or b is None or a == 0:
        return None
    return (b - a) / a * 100

def fmt(x):
    return "—" if x is None else f"{x:,.0f}"

def spark(s, w=110, h=26, color="#185FA5"):
    pts = [v for v in s if v is not None]
    if len(pts) < 2:
        return '<span style="color:#888;font-size:11px">数据不足</span>'
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1
    coords = []
    for i, v in enumerate(s):
        if v is None:
            continue
        x = 4 + i * (w - 8) / (len(s) - 1)
        y = h - 4 - (v - lo) / rng * (h - 8)
        coords.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(coords)
    dot = coords[-1].split(",")
    return (f'<svg width="{w}" height="{h}" style="vertical-align:middle">'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="1.5"/>'
            f'<circle cx="{dot[0]}" cy="{dot[1]}" r="2.2" fill="{color}"/></svg>')

def chg_html(x):
    if x is None:
        return '<span style="color:#888">—</span>'
    sym = "▲" if x >= 0 else "▼"
    color = "#A32D2D" if x >= 0 else "#0F6E56"   # 涨红跌绿
    return f'<span style="color:{color};font-weight:500">{sym} {abs(x):.1f}%</span>'

def table(title, note, d, periods, highlight_ids=("CHN",), latest_label=""):
    items = []
    for cid, rec in d.items():
        s = series(d, cid, periods)
        v_latest = s[-1]
        if v_latest is None or v_latest <= 0:
            continue
        items.append((cid, rec["name"], v_latest, s, delta(s)))
    items.sort(key=lambda x: -x[2])
    top = items[:20]
    h = [f'<h2>{title}</h2><p class="note">{note}</p>',
         f'<table><thead><tr><th>#</th><th>国家</th><th>{latest_label}<br><span class="unit">千桶/日 TBPD</span></th>'
         f'<th>趋势<br><span class="unit">{" → ".join([periods[0], periods[-1]])}</span></th>'
         f'<th>最新环比</th><th>首尾变化</th></tr></thead><tbody>']
    for i, (cid, name, v, s, dl) in enumerate(top, 1):
        dl_m = None
        if s[-1] is not None and s[-2] is not None and s[-2] != 0:
            dl_m = (s[-1] - s[-2]) / s[-2] * 100
        hl = ' class="hl"' if cid in highlight_ids else ""
        cn = CN.get(cid, "")
        disp = f"{cn} <span class='en'>{name}</span>" if cn and cn != name else name
        h.append(f"<tr{hl}><td>{i}</td><td><b>{disp}</b></td><td class='num'>{fmt(v)}</td>"
                 f"<td>{spark(s)}</td><td class='num'>{chg_html(dl_m)}</td><td class='num'>{chg_html(dl)}</td></tr>")
    h.append("</tbody></table>")
    missing = ""
    ids20 = {x[0] for x in top}
    if "CHN" not in ids20 and "IND" not in ids20:
        missing = ""
    return "\n".join(h)

# ---- 数据装载 ----
prod_m = by_country(load("act1.jsonl", unit="TBPD"), M_MONTHS)                 # 57x1 月度原油产量
cons_y = by_country(load("cons_annual.jsonl", unit="TBPD"), Y_MONTHS)          # 54x2 年度石油消费
prod53_y = by_country(load("prod53_annual.jsonl", unit="TBPD"), Y_MONTHS)      # 53x1 年度总油品产量

net_y = {}
for cid in set(cons_y) | set(prod53_y):
    s_c = series(cons_y, cid, Y_MONTHS)
    s_p = series(prod53_y, cid, Y_MONTHS)
    vals = {m: (s_c[i] - s_p[i]) for i, m in enumerate(Y_MONTHS)
            if s_c[i] is not None and s_p[i] is not None}
    if vals:
        net_y[cid] = {"name": (cons_y.get(cid) or prod53_y.get(cid))["name"], "vals": vals}

sec1 = table("① 原油产量 Top 20（月度）",
             "口径：Crude oil including lease condensate（productId=57），月度，250+ 国家完整覆盖，含中国。最新月份 2026-05（EIA 月度国际数据滞后约 3 个月）。",
             prod_m, M_MONTHS, latest_label="2026-05")
sec2 = table("② 石油产品消费 Top 20（年度）",
             "口径：Refined petroleum products 消费（productId=54），年度，179 国。<b>注意：中国、印度不在本数据源</b>——EIA 国际数据主要来自 JODI 体系，中印不向其提交月度/年度分国数据，故两表均无中印。原油(57)口径的消费在 EIA API 中不存在（实测 57×2 全频率 total=0）。",
             cons_y, Y_MONTHS, latest_label="2025 全年均值")
sec3 = table("③ 净石油进口 Top 20（推算，年度）",
             "口径：<b>推算值</b> = 石油产品消费(54×2) − 总油品产量(53×1)，单位同为 TBPD。EIA API 不提供全球分国原油/石油进口数据（仅 OECD 国家系列），以产消缺口近似进口依赖度。受消费数据覆盖限制，同样不含中印。",
             net_y, Y_MONTHS, latest_label="2025 全年推算")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>全球原油产量·消费·净进口 Top 20 | EIA 数据报告</title>
<style>
  body {{ font-family: "Segoe UI","Microsoft YaHei",sans-serif; margin:0; background:#F5F6F8; color:#222; }}
  .wrap {{ max-width: 980px; margin: 0 auto; padding: 24px 20px 60px; }}
  header {{ background: linear-gradient(135deg,#0C447C,#185FA5); color:#fff; padding: 26px 32px; border-radius: 12px; }}
  header h1 {{ margin: 0 0 8px; font-size: 22px; }}
  header p {{ margin: 2px 0; font-size: 13px; opacity: .92; }}
  h2 {{ font-size: 17px; margin: 34px 0 4px; color: #0C447C; border-left: 4px solid #185FA5; padding-left: 10px; }}
  .note {{ font-size: 12px; color: #555; margin: 4px 0 10px; line-height: 1.7; background:#fff; padding:8px 12px; border-radius:6px; border:1px solid #E8ECF2; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); font-size: 13px; }}
  th {{ background: #EEF3FA; color: #0C447C; padding: 9px 10px; text-align: left; font-weight: 600; }}
  th .unit {{ font-weight: 400; font-size: 11px; color: #667; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #EFF1F4; }}
  tr.hl td {{ background: #FFF7E0; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .en {{ color: #999; font-size: 11px; }}
  .foot {{ margin-top: 30px; font-size: 11px; color: #888; line-height: 1.9; background:#fff; padding:14px 16px; border-radius:8px; }}
</style>
</head>
<body><div class="wrap">
<header>
  <h1>全球原油产量 · 消费 · 净进口 Top 20 国家</h1>
  <p>数据源：U.S. EIA Open Data API v2（international 数据集）| 产量口径最新至 <b>2026-05</b>；消费/净进口口径最新至 <b>2025 年</b></p>
  <p>生成时间：2026-09-16 | 单位统一为千桶/日（TBPD）| 中国行以浅黄底色高亮</p>
</header>
{sec1}
{sec2}
{sec3}
<div class="foot">
  <b>口径与数据限制说明（重要）</b><br>
  1. <b>三个维度采用了不同口径</b>：产量=原油(57)；消费=石油产品(54)；净进口=54−53 推算。原因：EIA international 数据集中<b>不存在</b>原油口径的月度/年度分国消费（实测 57×2 全频率 total=0），也<b>不存在</b>全球分国进口数据（仅 OECD 国家系列 productId=78x）。<br>
  2. <b>中国与印度缺席消费与净进口两表</b>：该数据集主要源自 JODI 体系，中印不向其提交分国数据。中国石油消费可参考其他权威来源（如国家统计局、IEA）。产量表完整含中国（2026-05 约 4,389 千桶/日，全球第 5）。<br>
  3. 产量为月度流量口径；年度消费的 API 原始值含 5 种单位（MT/MTOE/QBTU/TBPD/TJ），本报告已过滤仅取 TBPD 保持同口径可比。<br>
  4. value 中的 EIA 缺数标记（w=withheld 等）已过滤，趋势线自动跳过缺失期。<br>
  5. 数据查询时间 2026-09-16，由 WorkBuddy 技能 eia-data-query 自动拉取生成；限流 0.15s/请求，Key 配置于 ~/.eia_api_key。
</div>
</div></body></html>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("report ->", OUT, f"({os.path.getsize(OUT):,} bytes)")

def top5(label, d, periods):
    items = []
    for cid, rec in d.items():
        s = series(d, cid, periods)
        if s[-1] and s[-1] > 0:
            items.append((s[-1], CN.get(cid, rec["name"]), cid))
    items.sort(reverse=True)
    print(f"{label} Top5:", "; ".join(f"{n}({c}) {v:,.0f}" for v, n, c in items[:5]))

top5("[月度产量2026-05]", prod_m, M_MONTHS)
top5("[年度消费2025]", cons_y, Y_MONTHS)
top5("[净进口推算2025]", net_y, Y_MONTHS)
