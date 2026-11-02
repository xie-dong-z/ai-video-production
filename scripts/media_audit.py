"""Inspect a local video and fully decode it. Does not judge story or speech."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np


def audit_video(src, require_audio=False):
    if not src.is_file():
        return {'source': str(src), 'technical_checks_passed': False, 'errors': ['文件不存在']}
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    decode = subprocess.run([ff, '-hide_banner', '-i', str(src), '-map', '0', '-f', 'null', '-'],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    has_audio = bool(re.search(r'Stream #.*Audio:', decode.stderr))
    cap = cv2.VideoCapture(str(src))
    facts = {'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
             'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
             'fps': float(cap.get(cv2.CAP_PROP_FPS)),
             'frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
    luma = []
    for ratio in (0, .25, .5, .75, .99):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(max(0, facts['frames'] - 1) * ratio))
        ok, frame = cap.read()
        if ok:
            luma.append(round(float(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).mean()), 3))
    cap.release()
    errors = []
    if decode.returncode:
        errors.append('完整解码失败')
    if not facts['width'] or not facts['height'] or not facts['frames'] or facts['fps'] <= 0:
        errors.append('视频规格无效')
    if require_audio and not has_audio:
        errors.append('缺少要求的音轨')
    peak = None
    if has_audio and decode.returncode == 0:
        raw = subprocess.run([ff, '-v', 'error', '-i', str(src), '-vn', '-f', 'f32le',
                              '-ar', '48000', '-ac', '2', '-'], capture_output=True)
        if raw.returncode:
            errors.append('音频解码失败')
        else:
            samples = np.frombuffer(raw.stdout, dtype='<f4')
            if samples.size:
                peak = float(np.max(np.abs(samples)))
                if not np.isfinite(samples).all():
                    errors.append('音频样本含非有限值')
                if peak >= 1:
                    errors.append('解码音频达到满幅，需要复核爆音')
    facts['duration_estimate_seconds'] = facts['frames'] / facts['fps'] if facts['fps'] else None
    return {'source': str(src), 'full_decode_ok': decode.returncode == 0,
            'technical_checks_passed': not errors, 'errors': errors, 'video': facts,
            'has_audio': has_audio, 'decoded_sample_peak': peak,
            'sample_frame_luma': luma,
            'dark_or_static_policy': '黑暗与静止需要结合剧情复核，不自动判错',
            'content_review_status': '仍需实际视听核对白、演员、动作、口型、节奏',
            'generation_requests_submitted': 0}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--require-audio', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = audit_video(args.video, args.require_audio)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        if args.report.resolve() == args.video.resolve():
            raise ValueError('报告不能覆盖视频原件')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
    print(text)
    return 0 if result['technical_checks_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
