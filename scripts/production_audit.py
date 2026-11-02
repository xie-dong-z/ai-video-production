"""Offline asset lineage, beat coverage and source-to-output caption checks."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def spec_hash(spec):
    raw = json.dumps(spec, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def index(items, label, errors):
    result = {}
    for item in items:
        ident = item['id']
        if ident in result:
            errors.append(f'{label}ID重复：{ident}')
        result[ident] = item
    return result


def asset_status(plan, base, errors, notes):
    assets = index(plan.get('assets', []), '素材', errors)
    facts = {}
    for ident, asset in assets.items():
        fact = {'id': ident, 'stale': False, 'spec_hash': spec_hash(asset.get('spec', {}))}
        if asset.get('file'):
            src = Path(asset['file'])
            if not src.is_absolute():
                src = base / src
            if not src.is_file():
                errors.append(f'{ident}：素材文件不存在：{src}')
            else:
                fact['sha256'] = hashlib.sha256(src.read_bytes()).hexdigest()
                if asset.get('sha256') and asset['sha256'] != fact['sha256']:
                    fact['stale'] = True
        elif asset.get('url'):
            notes.append(f'{ident}：远程内容未读取，无法证实文件指纹')
        if asset.get('spec_hash') and asset['spec_hash'] != fact['spec_hash']:
            fact['stale'] = True
        facts[ident] = fact
    visiting, done = set(), set()

    def visit(ident):
        if ident in visiting:
            errors.append('素材依赖成环：' + ident)
            facts[ident]['stale'] = True
            return
        if ident in done:
            return
        visiting.add(ident)
        for parent in assets[ident].get('parents', []):
            pid = parent['id']
            if pid not in assets:
                errors.append(f'{ident}：父素材不存在：{pid}')
                facts[ident]['stale'] = True
                continue
            visit(pid)
            pf = facts[pid]
            changed = pf['stale']
            for key in ('sha256', 'spec_hash'):
                if key in parent and key in pf and parent[key] != pf[key]:
                    changed = True
            if not parent.get('sha256') and not parent.get('spec_hash'):
                notes.append(f'{ident} → {pid}：没有派生时指纹，无法证明未变化')
            facts[ident]['stale'] |= changed
        visiting.remove(ident)
        done.add(ident)

    for ident in assets:
        visit(ident)
    return assets, facts


def resolve_plan(plan, assets, facts, errors):
    prepared = copy.deepcopy(plan)
    beats = {b['id']: b for b in plan.get('beats', [])}
    shots = {s['id']: s for s in plan.get('shots', [])}
    for clip in prepared.get('clips', []):
        for ref in clip.get('references', []):
            ident = ref.get('asset_id')
            if not ident:
                continue
            asset = assets.get(ident)
            if asset is None:
                errors.append(f"{clip['id']}：引用未知素材：{ident}")
                continue
            if asset.get('admission') != 'runtime':
                errors.append(f'{ident}：未允许作为生成输入')
            if facts[ident]['stale']:
                errors.append(f'{ident}：素材或上游要求已变化，需复核派生结果')
            uses = ref.get('use', [])
            if not uses or not set(uses) <= set(asset.get('allowed_use', [])):
                errors.append(f'{ident}：引用职责未声明或超出允许用途')
            if set(uses) & set(asset.get('excluded_use', [])):
                errors.append(f'{ident}：引用职责包含禁止借用属性')
            # Path/kind come from the single asset record, never an independently edited copy.
            for key in ('kind', 'file', 'url'):
                ref.pop(key, None)
                if key in asset:
                    ref[key] = asset[key]
        if 'beats' in plan and 'shots' in plan:
            canonical = []
            for sid in clip.get('shot_ids', []):
                for bid in shots.get(sid, {}).get('beat_ids', []):
                    beat = beats.get(bid, {})
                    if beat.get('kind') == 'dialogue':
                        canonical.append({'speaker': beat['speaker'], 'text': beat['text']})
            if 'dialogues' in clip and clip['dialogues'] != canonical:
                errors.append(f"{clip['id']}：对白副本与节拍记录不一致")
            clip['dialogues'] = canonical
    return prepared


def story_checks(plan, errors):
    if 'beats' not in plan and 'shots' not in plan:
        return
    beats = index(plan.get('beats', []), '节拍', errors)
    shots = index(plan.get('shots', []), '导演镜头', errors)
    covered = [bid for shot in shots.values() for bid in shot.get('beat_ids', [])]
    if covered != list(beats):
        errors.append('镜头的节拍覆盖存在遗漏、重复、未知ID或顺序变化')
    if 'clips' in plan:
        assigned = [sid for clip in plan['clips'] for sid in clip.get('shot_ids', [])]
        if assigned != list(shots):
            errors.append('生成片段的镜头覆盖存在遗漏、重复或顺序变化')
        for clip in plan['clips']:
            for sid in clip.get('shot_ids', []):
                for bid in shots.get(sid, {}).get('beat_ids', []):
                    beat = beats.get(bid, {})
                    if beat.get('kind') == 'dialogue' and beat['text'] not in clip.get('prompt', ''):
                        errors.append(f"{clip['id']}：指定对白未出现在正文：{bid}")


def edit_checks(plan, assets, facts, errors):
    edit = plan.get('edit')
    if edit is None:
        return {}
    segments = index(edit.get('segments', []), '剪辑片段', errors)
    words = index(edit.get('words', []), '词', errors)
    captions_by_id = index(edit.get('captions', []), '字幕', errors)
    for wid, word in words.items():
        start, end = word['start'], word['end']
        if not all(math.isfinite(v) for v in (start, end)) or start < 0 or end <= start:
            errors.append(f'{wid}：源词时间无效')
        if word['asset_id'] not in assets:
            errors.append(f'{wid}：源词素材不存在')
        elif word.get('source_sha256') and facts[word['asset_id']].get('sha256') != word['source_sha256']:
            errors.append(f'{wid}：转写对应的源文件已变化或无法核实')
    mapped, offsets = {}, {}
    offset = 0.0
    for sid, seg in segments.items():
        if seg.get('transition') or seg.get('speed_curve') or seg.get('overlap'):
            errors.append(f'{sid}：非线性或重叠剪辑不适用本时间映射')
        a, b, speed = seg['in'], seg['out'], seg.get('speed', 1)
        if not all(math.isfinite(v) for v in (a, b, speed)) or a < 0 or b <= a or speed <= 0:
            errors.append(f'{sid}：剪辑入出点或速度无效')
            continue
        asset = assets.get(seg['asset_id'])
        if asset is None:
            errors.append(f'{sid}：剪辑源素材不存在')
        elif asset.get('duration_seconds') is not None and b > asset['duration_seconds']:
            errors.append(f'{sid}：出点超过已记录的源时长')
        if asset and facts[seg['asset_id']]['stale']:
            errors.append(f'{sid}：剪辑源素材已变化，需复核词时间与选片')
        offsets[sid] = offset
        for wid, word in words.items():
            if word['asset_id'] != seg['asset_id']:
                continue
            start, end = word['start'], word['end']
            if not all(math.isfinite(v) for v in (start, end)) or start < 0 or end <= start:
                errors.append(f'{wid}：源词时间无效')
                continue
            if end <= a or start >= b:
                continue
            partial = start < a or end > b
            if partial and not (seg.get('allow_word_cut') and seg.get('word_cut_reason')):
                errors.append(f'{sid}：切点截断词：{wid}')
            mapped[(sid, wid)] = {'start': offset + (max(a, start) - a) / speed,
                                  'end': offset + (min(b, end) - a) / speed}
        offset += (b - a) / speed
    captions = []
    for cap in captions_by_id.values():
        spans, chosen = [], set()
        if not cap.get('word_ids'):
            errors.append(f"{cap['id']}：字幕缺少词ID")
        for wid in cap.get('word_ids', []):
            matches = [(sid, span) for (sid, word_id), span in mapped.items()
                       if word_id == wid and (not cap.get('segment_id') or cap['segment_id'] == sid)]
            if len(matches) != 1:
                errors.append(f"{cap['id']}：词不存在、已剪掉或重复使用需指定segment_id：{wid}")
                continue
            sid, span = matches[0]
            chosen.add(sid)
            spans.append(span)
        if len(chosen) > 1:
            errors.append(f"{cap['id']}：字幕跨剪辑片段，请按切点拆分")
        if spans:
            if any(a['start'] > b['start'] for a, b in zip(spans, spans[1:])):
                errors.append(f"{cap['id']}：字幕词序与输出顺序不一致")
            captions.append({'id': cap['id'], 'text': cap['text'],
                             'start': min(s['start'] for s in spans),
                             'end': max(s['end'] for s in spans)})
    return {'duration_seconds': offset, 'segment_offsets': offsets, 'captions': captions}


def audit(plan, base):
    errors, notes = [], []
    assets, facts = asset_status(plan, base, errors, notes)
    story_checks(plan, errors)
    resolve_plan(plan, assets, facts, errors)
    edit = edit_checks(plan, assets, facts, errors)
    return {'checks_passed': not errors, 'errors': sorted(set(errors)), 'notes': sorted(set(notes)),
            'assets': list(facts.values()), 'edit': edit,
            'generation_requests_submitted': 0, 'ready_for_paid_submission': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding='utf-8-sig'))
    result = audit(plan, args.plan.parent)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        protected = {args.plan.resolve()}
        protected.update((args.plan.parent / a['file']).resolve() for a in plan.get('assets', []) if a.get('file'))
        if args.report.resolve() in protected:
            raise ValueError('报告不能覆盖输入计划或源素材')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
    print(text)
    return 0 if result['checks_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
