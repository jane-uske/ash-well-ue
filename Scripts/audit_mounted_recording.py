#!/usr/bin/env python3
"""Read-only capture audit. Media frame rate is never an engine FPS measurement."""
import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
import wave


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration,start_time:stream=codec_type,codec_name,duration,start_time,nb_frames,avg_frame_rate,r_frame_rate,sample_rate',
        '-of', 'json', str(path)], text=True))


def audit_raw(directory):
    d = Path(directory)
    meta = json.loads((d / 'recording.json').read_text())
    frames = [json.loads(x) for x in (d / 'frames.jsonl').read_text().splitlines()]
    times = [float(f['real_seconds']) for f in frames]
    duration = float(meta['duration_seconds'])
    intervals = [b-a for a, b in zip(times, times[1:])]
    errors = []
    if len(times) < 2 or not all(math.isfinite(t) for t in times) or any(t <= 0 for t in intervals):
        errors.append('invalid_or_nonmonotonic_frame_timestamps')
    if any(not f.get('saved') or not (d / f['file']).is_file() for f in frames):
        errors.append('missing_or_failed_frame')
    if meta.get('frame_write_failures', 0):
        errors.append('frame_write_failure')
    if times and (times[0] < 0 or times[-1] > duration or duration-times[-1] > .25):
        errors.append('frame_timeline_does_not_cover_recording')
    audio = None
    try:
        with wave.open(str(d / 'game-audio.wav'), 'rb') as w:
            declared = w.getnframes()
            actual = len(w.readframes(declared)) // (w.getnchannels()*w.getsampwidth())
            audio = {'declared_samples': declared, 'readable_samples': actual,
                     'sample_rate': w.getframerate(), 'channels': w.getnchannels(),
                     'duration_seconds': actual/w.getframerate()}
            if actual != declared:
                errors.append('truncated_wav')
    except (OSError, wave.Error, EOFError):
        errors.append('missing_or_invalid_wav')
    # Strict export gate, not proof of audible event alignment. Never time-stretch
    # or pad a short recording to make this condition pass.
    if audio and abs(audio['duration_seconds']-duration) > .25:
        errors.append('audio_wall_duration_mismatch')
    return {'directory': str(d.resolve()), 'recording_seconds': duration,
            'captured_frames': len(frames), 'requested_capture_fps': meta.get('nominal_capture_fps'),
            'observed_capture_fps': len(frames)/duration,
            'mean_capture_interval_seconds': statistics.mean(intervals) if intervals else None,
            'maximum_capture_gap_seconds': max(intervals) if intervals else None,
            'first_capture_seconds': times[0] if times else None,
            'last_capture_seconds': times[-1] if times else None,
            'audio': audio, 'errors': errors, 'av_duration_gate_passed': not errors,
            'engine_fps': None,
            'scope': 'Capture/sample duration audit only. Does not prove lip/event sync or UE render/game frame rate.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--media', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    report = audit_raw(a.directory)
    if a.media:
        report['encoded_media'] = probe(a.media)
    text = json.dumps(report, ensure_ascii=False, indent=2)+'\n'
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text)
    print(text)
    return 0 if report['av_duration_gate_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
