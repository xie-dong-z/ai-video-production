"""Read model metadata and optional public pricing. Never creates media tasks."""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def redact(value, key=''):
    if isinstance(value, dict):
        return {k: redact(v, key) for k, v in value.items()
                if k.lower() not in ('api_key', 'api-key', 'access_token', 'authorization', 'cookie', 'password', 'secret')}
    if isinstance(value, list):
        return [redact(v, key) for v in value]
    if isinstance(value, str):
        if key:
            value = value.replace(key, '[REDACTED]')
        return re.sub(r'(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}', '[REDACTED]', value)
    return value


def read_json(url, key=None, timeout=18):
    hdr = {'Accept': 'application/json', 'User-Agent': 'ai-video-production-readonly/1.0'}
    if key:
        hdr['Authorization'] = 'Bearer ' + key
    result = {'url': url, 'checked_at': datetime.now(timezone.utc).isoformat()}
    try:
        with build_opener(NoRedirect()).open(Request(url, headers=hdr), timeout=timeout) as res:
            result['http_status'] = res.status
            result['data'] = json.loads(res.read())
    except (HTTPError, URLError, TimeoutError, ValueError) as err:
        result['http_status'] = getattr(err, 'code', None)
        result['error_type'] = type(err).__name__
    return result


def refresh(api_base, key=None, provider=None, models=(), hours=(), timeout=18):
    base = api_base.rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('api-base必须是已确认的HTTP(S)服务地址')
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('api-base不能含凭据、查询参数或片段')
    if provider == 'simplefuture' and (parsed.hostname != 'simplefuture.zone' or parsed.scheme != 'https'):
        raise ValueError('simplefuture额外查询仅适用于该提供方的HTTPS服务')
    if hours and provider != 'simplefuture':
        raise ValueError('公开性能查询目前只适配simplefuture')
    if any(h < 1 or h > 720 for h in hours):
        raise ValueError('统计窗口须在1至720小时之间')

    catalog = read_json(base + '/models', key, timeout)
    body = catalog.pop('data', {})
    items = body.get('data') if isinstance(body, dict) else None
    valid = isinstance(items, list) and all(isinstance(r, dict) and isinstance(r.get('id'), str) for r in items)
    catalog['schema_verified'] = valid
    catalog['models'] = [{k: r.get(k) for k in ('id', 'object', 'owned_by')} for r in items] if valid else []
    catalog['model_count'] = len(catalog['models']) if valid else None
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'api_base': base,
              'mode': 'read_only_discovery', 'models': catalog, 'generation_requests_submitted': 0,
              'verification': {'catalog': 'verified' if valid else 'unverified', 'create': 'not_tested',
                               'upload': 'not_tested', 'content': 'not_tested', 'billing': 'not_tested'}}
    if provider == 'simplefuture':
        origin = parsed.scheme + '://' + parsed.netloc
        result['public_pricing'] = read_json(origin + '/api/pricing', timeout=timeout)
        result['public_performance'] = []
        for model in models:
            for h in hours:
                path = '/api/perf-metrics?model=' + quote(model, safe='') + '&hours=' + str(h)
                item = read_json(origin + path, timeout=timeout)
                item.update(model=model, hours=h, sample_denominator='not_verified')
                result['public_performance'].append(item)
    extra = ([result['public_pricing']] + result['public_performance']) if provider == 'simplefuture' else []
    complete = all(r.get('http_status') == 200 and isinstance(r.get('data'), dict)
                   and r['data'].get('success') is not False for r in extra)
    result['status'] = 'ready' if valid and complete else 'partial'
    return redact(result, key or '')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-base', required=True)
    parser.add_argument('--api-key-env')
    parser.add_argument('--provider', choices=['simplefuture'])
    parser.add_argument('--model', action='append', default=[])
    parser.add_argument('--hours', type=int, nargs='+', default=[])
    parser.add_argument('--timeout', type=float, default=18)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    key = os.environ.get(args.api_key_env) if args.api_key_env else None
    if args.api_key_env and not key:
        parser.error('指定的进程凭据变量未设置；无需把Key粘贴到命令行参数')
    result = refresh(args.api_base, key, args.provider, args.model, args.hours, args.timeout)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': result['status'], 'models': result['models']['model_count'],
                      'public_performance_queries': len(result.get('public_performance', [])),
                      'paid_requests': 0, 'report': str(args.out)}, ensure_ascii=False))
    return 0 if result['status'] == 'ready' else 2


if __name__ == '__main__':
    raise SystemExit(main())
