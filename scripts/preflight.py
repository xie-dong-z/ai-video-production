"""Offline film-plan checks and public-price estimates. Never submits a task."""
import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from production_audit import audit as audit_production, resolve_plan


def check_prompt(clip, allow_timing=False):
    text = clip['prompt']
    errors = []
    masked = text
    for line in clip.get('dialogues', []):
        if line['text'] not in text:
            errors.append('指定对白未出现在正文：' + line['speaker'])
        masked = masked.replace(line['text'], 'DIALOGUE')
    for visible in clip.get('visible_text', []):
        masked = masked.replace(visible, 'VISIBLE_TEXT')
    if not allow_timing and re.search(r'\d+(?:\.\d+)?\s*(?:[-—–~]\s*\d+(?:\.\d+)?)?\s*(?:秒|s(?:econds?)?\b)', masked, re.I):
        errors.append('正文含秒数/时间轴；请移到请求参数或后期表')
    if not allow_timing and re.search(r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\b', masked):
        errors.append('正文含时码')
    if re.search(r'【[^】]*(?:实际引用|图引用|图号)[^】]*】|<Picture N>', text):
        errors.append('正文有未替换的素材占位符')
    return errors


def check_ref(ref, plan_dir):
    errors, notes, facts = [], [], {}
    kind = ref.get('kind')
    role = ref['role']
    allowed = {'image': ('reference_image', 'first_frame', 'last_frame'),
               'video': ('reference_video',), 'audio': ('reference_audio',)}
    if role not in allowed.get(kind, ()):
        errors.append('素材种类与语义角色不对应')
    if role in ('first_frame', 'last_frame') and kind != 'image':
        errors.append('首尾帧必须是图片')
    if ref.get('file'):
        src = Path(ref['file'])
        if not src.is_absolute():
            src = plan_dir / src
        if not src.is_file():
            return ['素材文件不存在：' + str(src)], notes, facts
        facts = {'file': str(src), 'bytes': src.stat().st_size,
                 'sha256': hashlib.sha256(src.read_bytes()).hexdigest()}
        if kind == 'image':
            try:
                with Image.open(src) as image:
                    facts.update(width=image.width, height=image.height, mode=image.mode)
                    image.verify()
            except OSError:
                errors.append('图片不能解码：' + str(src))
        notes.append('本地可读不等于云端可读，提交前验证上传/托管或内联协议')
    elif ref.get('url'):
        parsed = urlsplit(ref['url'])
        if parsed.scheme not in ('https', 'http') or not parsed.hostname:
            errors.append('参考URL不是HTTP(S)地址')
        if parsed.username or parsed.password:
            errors.append('参考URL不能内嵌账号密码')
        host = parsed.hostname or ''
        if parsed.port:
            host += ':' + str(parsed.port)
        facts = {'url': parsed.scheme + '://' + host + parsed.path}
        notes.append('离线预检未验证远程URL可达性')
    else:
        errors.append('素材缺少file或url')
    return errors, notes, facts


def audit(plan, profiles, plan_dir):
    errors, warnings, rows = [], [], []
    if any(key in plan for key in ('assets', 'beats', 'shots', 'edit')):
        structure = audit_production(plan, plan_dir)
        errors.extend(structure['errors'])
        warnings.extend(structure['notes'])
        assets = {a['id']: a for a in plan.get('assets', [])}
        facts = {a['id']: a for a in structure['assets']}
        plan = resolve_plan(plan, assets, facts, [])
    if profiles.get('currency') != 'CNY':
        errors.append('预检使用人民币预算；其他币种须先按带日期的核对汇率转换报价配置')
    ids = []
    reserved = Decimal('0')
    for clip in plan['clips']:
        ident = clip['id']
        if ident in ids:
            errors.append(ident + '：镜头ID重复')
        ids.append(ident)
        model = clip['model']
        if model not in profiles['models']:
            errors.append(ident + '：没有已核对的模型配置')
            continue
        cfg = profiles['models'][model]
        seconds = clip['seconds']
        local = check_prompt(clip, plan.get('allow_prompt_timeline', False))
        if not isinstance(seconds, int) or seconds <= 0:
            local.append('请求时长必须是正整数')
        elif cfg.get('seconds_options') and seconds not in cfg['seconds_options']:
            local.append('请求时长不在通道枚举中：' + str(cfg['seconds_options']))
        elif not cfg.get('seconds_options') and not cfg['min_seconds'] <= seconds <= cfg['max_seconds']:
            local.append('请求时长超出规划安全范围')
        resolution = clip['resolution']
        if resolution not in cfg['resolution_ratios']:
            local.append('该分辨率没有已核对报价')
        if resolution == 'provider_default':
            warnings.append(ident + '：公开说明未确定输出分辨率，正式任务需核对')
        attempts = clip.get('max_attempts', 1)
        if not isinstance(attempts, int) or attempts < 1:
            local.append('尝试次数必须是正整数')
            attempts = 1
        if cfg.get('premium') and model not in plan.get('premium_models_allowed', []):
            local.append('高价通道未列入本计划允许范围')
        refs = clip.get('references', [])
        counts = {kind: sum(r.get('kind') == kind for r in refs) for kind in ('image', 'video', 'audio')}
        for kind, count in counts.items():
            cap = cfg['planning_reference_limits'].get(kind)
            if cap is None and count:
                local.append(kind + '引用能力尚未核对')
            elif cap is not None and count > cap:
                local.append(kind + '引用数量超限')
        if cfg.get('max_total_refs') and len(refs) > cfg['max_total_refs']:
            local.append('混合参考总数超限')
        roles = [r['role'] for r in refs]
        if cfg.get('frame_reference_policy') == 'native_mutually_exclusive':
            boundary = any(r in ('first_frame', 'last_frame') for r in roles)
            reference = any(r.startswith('reference_') for r in roles)
            if boundary and reference:
                local.append('H3原生首尾帧与reference角色互斥')
            if roles.count('first_frame') > 1 or roles.count('last_frame') > 1:
                local.append('首尾帧数量超限')
            if cfg.get('max_prompt_characters') and len(clip['prompt']) > cfg['max_prompt_characters']:
                local.append('正文超过已声明的字符上限')
        assets = []
        for ref in refs:
            bad, notes, facts = check_ref(ref, plan_dir)
            local.extend(bad)
            warnings.extend(ident + '：' + note for note in notes)
            assets.append(facts)
        rate = Decimal(str(cfg['price_cny']))
        if not rate.is_finite() or rate < 0:
            local.append('报价必须是非负有限人民币金额')
            rate = Decimal('0')
        if cfg['unit'] not in ('second', 'request'):
            local.append('计价单位尚未核对为按秒或按次')
        multiplier = Decimal(str(cfg['resolution_ratios'].get(resolution, 1)))
        first = rate * multiplier * (Decimal(str(seconds)) if cfg['unit'] == 'second' else 1)
        reserve = first * attempts
        reserved += reserve
        errors.extend(ident + '：' + issue for issue in local)
        rows.append({'id': ident, 'model': model, 'requested_seconds': seconds,
                     'first_pass_estimate_cny': float(first.quantize(Decimal('0.01'))),
                     'attempt_reserve_cny': float(reserve.quantize(Decimal('0.01'))),
                     'assets': assets, 'checks_passed': not local})
    extra = Decimal(str(plan.get('known_extra_cost_cny', 0)))
    if not extra.is_finite() or extra < 0:
        errors.append('额外费用必须是非负有限金额')
        extra = Decimal('0')
    reserved += extra
    budget = plan.get('budget_cny')
    if budget is None:
        errors.append('未给总预算；付费制作前需明确范围')
    elif not Decimal(str(budget)).is_finite() or Decimal(str(budget)) < 0:
        errors.append('总预算必须是非负有限金额')
    elif reserved > Decimal(str(budget)):
        errors.append('预留尝试费用超过总预算')
    warnings.append('报价来自公示快照，正式任务前刷新；附加输入费用与实际扣费未实测')
    warnings.append('预检不能代替对白、表情、动作和身份的实际审片')
    return {'project_id': plan['project_id'], 'mode': 'offline_preflight',
            'checks_passed': not errors, 'errors': errors, 'warnings': sorted(set(warnings)),
            'budget_cny': budget, 'reserved_estimate_cny': float(reserved.quantize(Decimal('0.01'))),
            'pricing_snapshot': profiles['snapshot_date'], 'clips': rows,
            'generation_requests_submitted': 0, 'ready_for_paid_submission': False,
            'remaining_live_checks': ['素材传输', '通道请求映射', '首个任务与实际扣费', '内容审片']}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--profiles', type=Path, default=Path(__file__).with_name('model_profiles.json'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding='utf-8-sig'))
    result = audit(plan,
                   json.loads(args.profiles.read_text(encoding='utf-8-sig')), args.plan.parent)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        protected = {args.plan.resolve(), args.profiles.resolve()}
        refs = plan.get('assets', []) + [r for c in plan['clips'] for r in c.get('references', [])]
        protected.update((args.plan.parent / r['file']).resolve() for r in refs if r.get('file'))
        if args.report.resolve() in protected:
            raise ValueError('报告不能覆盖输入计划、模型配置或源素材')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
    print(text)
    return 0 if result['checks_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
