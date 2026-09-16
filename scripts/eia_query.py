#!/usr/bin/env python3
"""
EIA API v2 查询工具 — 路由浏览 / facet 枚举 / 数据查询 / 自动分页 / CSV 导出

用法:
  eia_query.py routes [path] [--depth N]
  eia_query.py meta <path>
  eia_query.py facets <path> [facet_id] [--filter STR] [--limit N]
  eia_query.py data <path> [--freq F] [--facet k=v1,v2 ...] [--cols c1,c2]
                     [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--limit N] [--all]
                     [--sort asc|desc] [--csv FILE] [--pretty]
  eia_query.py setup --key KEY
  eia_query.py key

依赖:python3 + requests。Key 查找顺序:--key > env EIA_API_KEY > ~/.eia_api_key
"""
import argparse, csv, json, os, sys, time

BASE = 'https://api.eia.gov/v2'
KEY_FILE = os.path.expanduser('~/.eia_api_key')
REQ_INTERVAL = 0.15  # 限流保护

_last_req = [0.0]

def _http(session, path, params):
    # 限流间隔
    gap = time.time() - _last_req[0]
    if gap < REQ_INTERVAL:
        time.sleep(REQ_INTERVAL - gap)
    _last_req[0] = time.time()
    r = session.get(f'{BASE}/{path}' if path else BASE, params=params, timeout=60)
    return r

def get_key(cli_key=None, quiet=False):
    if cli_key:
        return cli_key
    k = os.environ.get('EIA_API_KEY', '')
    if k:
        return k.strip()
    if os.path.exists(KEY_FILE):
        k = open(KEY_FILE).read().strip()
        if k:
            return k
    if not quiet:
        print('ERROR: 未找到 EIA API key。配置方式(任选一):\n'
              '  1. python3 eia_query.py setup --key <KEY>\n'
              '  2. export EIA_API_KEY=<KEY>\n'
              f'  3. 写入 {KEY_FILE}\n'
              '  免费申请: https://www.eia.gov/opendata/', file=sys.stderr)
    return None

def cmd_setup(args):
    if not args.key or len(args.key) < 20:
        print('ERROR: --key 缺失或格式不对(应为 40 位左右字符串)', file=sys.stderr)
        return 1
    with open(KEY_FILE, 'w') as f:
        f.write(args.key.strip())
    os.chmod(KEY_FILE, 0o600)
    print(f'key saved -> {KEY_FILE}')
    return 0

def cmd_key(args):
    k = get_key(quiet=True)
    if not k:
        print('NOT CONFIGURED')
        return 1
    masked = k[:4] + '*' * (len(k) - 8) + k[-4:]
    print(f'OK {masked} ({len(k)} chars, {KEY_FILE})')
    # 快速验证
    import requests
    r = _http(requests.Session(), '', {'api_key': k})
    if r.status_code == 200:
        print('API check: valid')
        return 0
    print(f'API check: HTTP {r.status_code} {r.text[:120]}')
    return 1

def _get(session, path, params, api_key):
    # params 可为 dict 或 [(k,v),...] 列表;列表用于同键重复(facets 多值),requests 会自动编码 []
    if isinstance(params, list):
        p = [('api_key', api_key)] + params
    else:
        p = {'api_key': api_key}
        if params:
            p.update(params)
    r = _http(session, path, p)
    if r.status_code == 200:
        try:
            return r.json(), None
        except Exception as e:
            return None, f'JSON parse error: {e}'
    try:
        j = r.json()
        msg = j.get('error', r.text[:200])
    except Exception:
        msg = r.text[:200]
    return None, f'HTTP {r.status_code}: {msg}'

def _rows_from(resp):
    raw = resp.get('data')
    if isinstance(raw, list):
        return raw
    return []

def cmd_routes(args):
    import requests
    key = get_key(args.key)
    if not key:
        return 1
    s = requests.Session()
    path = args.path.strip('/') if args.path else ''

    def walk(p, depth):
        j, err = _get(s, p, {}, key)
        if err:
            print(f'{"  "*depth}[ERR] {p or "/"} -> {err}')
            return
        resp = j.get('response', {})
        name = resp.get('name', '')
        routes = resp.get('routes')
        kind = 'DIR' if routes else 'DATA'
        extra = ''
        if resp.get('frequency'):
            f = resp['frequency']
            ids = [x.get('id') if isinstance(x, dict) else x for x in f] if isinstance(f, list) else list(f.keys())
            extra = f'  freq={",".join(ids)}'
        print(f'{"  "*depth}[{kind}] {p or "/"} | {name}{extra}')
        if routes and depth < args.depth:
            for r in sorted(routes, key=lambda x: x.get('id', '')):
                walk(f"{p}/{r.get('id','')}" if p else r.get('id', ''), depth + 1)

    walk(path, 0)
    return 0

def cmd_meta(args):
    import requests
    key = get_key(args.key)
    if not key:
        return 1
    s = requests.Session()
    j, err = _get(s, args.path.strip('/'), {}, key)
    if err:
        print(f'ERROR: {err}', file=sys.stderr)
        return 1
    if args.pretty:
        print(json.dumps(j, ensure_ascii=False, indent=2))
        return 0
    resp = j.get('response', {})
    out = {'id': resp.get('id'), 'name': resp.get('name'), 'description': resp.get('description')}
    f = resp.get('frequency')
    if isinstance(f, list):
        out['frequencies'] = [x.get('id') if isinstance(x, dict) else x for x in f]
    elif isinstance(f, dict):
        out['frequencies'] = list(f.keys())
    elif f:
        out['frequencies'] = [str(f)]
    if resp.get('facets'):
        out['facets'] = resp['facets']
    d = resp.get('data')
    if isinstance(d, dict):
        # international 等端点的 data 列值可能是 dict(含 units)或 list(单位枚举)
        out['data_columns'] = {
            k: ({'units': v.get('units')} if isinstance(v, dict) else {'raw': v})
            for k, v in d.items()
        }
    if resp.get('startPeriod') or resp.get('endPeriod'):
        out['coverage'] = {'start': resp.get('startPeriod'), 'end': resp.get('endPeriod')}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0

def cmd_facets(args):
    import requests
    key = get_key(args.key)
    if not key:
        return 1
    s = requests.Session()
    path = args.path.strip('/')
    if not args.facet_id:
        # 列出该端点全部 facet 名
        j, err = _get(s, path, {}, key)
        if err:
            print(f'ERROR: {err}', file=sys.stderr)
            return 1
        fs = j.get('response', {}).get('facets', [])
        print('可用 facet(用 facets <path> <facet_id> 枚举取值):')
        for v in fs:
            print(f"  {v.get('id')} | {v.get('description','')}")
        return 0
    j, err = _get(s, f'{path}/facet/{args.facet_id}/', {}, key)
    if err:
        print(f'ERROR: {err}', file=sys.stderr)
        return 1
    vals = j.get('response', {}).get('facets', [])
    total = j.get('response', {}).get('totalFacets', len(vals))
    if args.filter:
        fl = args.filter.lower()
        vals = [v for v in vals if fl in (str(v.get('id', '')) + ' ' + str(v.get('name', ''))).lower()]
    print(f'# {path} facet={args.facet_id} total={total} matched={len(vals)}')
    for v in vals[: args.limit]:
        print(f"  {v.get('id')} | {v.get('name')}")
    return 0

def cmd_data(args):
    import requests
    key = get_key(args.key)
    if not key:
        return 1
    s = requests.Session()
    path = args.path.strip('/')
    params = {
        'sort[0][column]': 'period',
        'sort[0][direction]': args.sort,
    }
    if args.freq:
        params['frequency'] = args.freq
    cols = [c for c in (args.cols or '').split(',') if c] or ['value']
    for i, c in enumerate(cols):
        params[f'data[{i}]'] = c
    for fc in args.facet or []:
        if '=' not in fc:
            print(f'ERROR: --facet 须为 key=v1,v2 形式,收到 {fc}', file=sys.stderr)
            return 1
    # 用元组列表保留同键多值(facets[key][]=v1, v1, ...),requests 自动 URL 编码 []
    tuple_params = list(params.items())
    for fc in args.facet or []:
        k, vs = fc.split('=', 1)
        for v in vs.split(','):
            if v:
                tuple_params.append((f'facets[{k}][]', v))
    if args.start:
        tuple_params.append(('start', args.start))
    if args.end:
        tuple_params.append(('end', args.end))

    limit = args.limit if args.limit else 5000
    page_size = min(limit, 5000)
    all_rows, offset = [], 0
    total = None
    while True:
        p = list(tuple_params) + [('length', str(page_size)), ('offset', str(offset))]
        j, err = _get(s, f'{path}/data/', p, key)
        if err:
            print(f'ERROR: {err}', file=sys.stderr)
            print('提示:列名/facet 不对?先跑 meta 与 facets 子命令自省。', file=sys.stderr)
            return 1
        resp = j.get('response', {})
        rows = _rows_from(resp)
        if total is None:
            try:
                total = int(resp.get('total') or 0)
            except (TypeError, ValueError):
                total = None
            if not args.all and total and total > limit:
                print(f'# NOTE: total={total} 超过 --limit={limit},仅取前 {limit} 行;要取全量请加 --all', file=sys.stderr)
        all_rows.extend(rows[: max(0, limit - len(all_rows))] if limit else rows)
        if not args.all:
            break
        if len(rows) < page_size:
            break
        if total is not None and len(all_rows) >= min(int(total), 5_000_000):
            break
        offset += page_size
    if not all_rows:
        print('# (empty) — 0 行。检查 facet 组合是否正确/该组合是否有数据。', file=sys.stderr)
        return 2
    if args.csv:
        cols_seen = []
        for row in all_rows:
            for k in row.keys():
                if k not in cols_seen:
                    cols_seen.append(k)
        with open(args.csv, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols_seen)
            w.writeheader()
            for row in all_rows:
                w.writerow(row)
        print(f'# wrote {len(all_rows)} rows -> {args.csv}', file=sys.stderr)
        return 0
    for row in all_rows:
        print(json.dumps(row, ensure_ascii=False))
    print(f'# {len(all_rows)} rows (total={total})', file=sys.stderr)
    return 0

def main():
    ap = argparse.ArgumentParser(description='EIA API v2 query tool')
    ap.add_argument('--key', help='EIA API key(临时,优先级最高)')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('setup', help='保存 API key 到 ~/.eia_api_key')
    p.add_argument('--key', required=True)
    p.set_defaults(fn=cmd_setup)

    p = sub.add_parser('key', help='查看 key 状态并验证')
    p.set_defaults(fn=cmd_key)

    p = sub.add_parser('routes', help='浏览路由树')
    p.add_argument('path', nargs='?', default='')
    p.add_argument('--depth', type=int, default=1)
    p.set_defaults(fn=cmd_routes)

    p = sub.add_parser('meta', help='端点元数据(频率/facet/data列/单位)')
    p.add_argument('path')
    p.add_argument('--pretty', action='store_true', help='输出原始 JSON')
    p.set_defaults(fn=cmd_meta)

    p = sub.add_parser('facets', help='枚举 facet 合法值')
    p.add_argument('path')
    p.add_argument('facet_id', nargs='?')
    p.add_argument('--filter', help='按 id+name 过滤(不区分大小写)')
    p.add_argument('--limit', type=int, default=30)
    p.set_defaults(fn=cmd_facets)

    p = sub.add_parser('data', help='查数据(自动分页)')
    p.add_argument('path')
    p.add_argument('--freq', help='frequency id: annual/quarterly/monthly/weekly/daily/hourly/local-hourly/four-week-average')
    p.add_argument('--facet', action='append', help='facet 过滤,key=v1,v2(可重复)')
    p.add_argument('--cols', help='data 列名,逗号分隔(默认 value)')
    p.add_argument('--start')
    p.add_argument('--end')
    p.add_argument('--limit', type=int, help='最多取多少行(默认 5000,单页)')
    p.add_argument('--all', action='store_true', help='自动翻页取全量')
    p.add_argument('--sort', default='desc', choices=['asc', 'desc'])
    p.add_argument('--csv', help='导出 CSV 文件')
    p.set_defaults(fn=cmd_data)

    args = ap.parse_args()
    return args.fn(args)

if __name__ == '__main__':
    sys.exit(main())
