"""Objective picture metrics shared by the benchmark and your renders (Python 3 + ffmpeg only).

Every frame is downscaled to 64x36 and measured:
  luma        mean brightness 0-255 (Rec.709 weights on sRGB values)
  p10 / p90   dark / bright percentiles (contrast)
  sat         mean saturation 0-1
  orange      % of pixels in the character orange (hue 0-30 deg, sat > .35, val > .25):
              how big the character system is on screen
  cool        % of saturated pixels with hue 160-260 deg (the cool world around it)
  motion      mean absolute luma change to the previous sampled frame (per frame step)
The same code produced ../benchmark/metrics.json from the reference video, so numbers are
directly comparable.
"""
import colorsys
import json
import subprocess

W, H = 64, 36


def _frames_from_video(path, t0, t1, fps=10):
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-t', f'{max(0.05, t1 - t0):.3f}', '-i', path,
           '-vf', f'fps={fps},scale={W}:{H}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    n = W * H * 3
    return [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]


def _frames_from_images(paths):
    out = []
    for p in paths:
        cmd = ['ffmpeg', '-v', 'error', '-i', p, '-vf', f'scale={W}:{H}:flags=area', '-f', 'rawvideo',
               '-pix_fmt', 'rgb24', '-']
        out.append(subprocess.run(cmd, check=True, capture_output=True).stdout)
    return out


def frame_stats(buf):
    lum, sat, orange, cool = [], 0.0, 0, 0
    for i in range(0, len(buf), 3):
        r, g, b = buf[i], buf[i + 1], buf[i + 2]
        lum.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        sat += s
        if s > 0.35 and v > 0.25 and (h * 360 <= 30 or h * 360 >= 350):
            orange += 1
        elif s > 0.2 and 160 <= h * 360 <= 260:
            cool += 1
    n = len(lum)
    srt = sorted(lum)
    return {'luma': sum(lum) / n, 'p10': srt[n // 10], 'p90': srt[n * 9 // 10], 'sat': sat / n,
            'orange': 100.0 * orange / n, 'cool': 100.0 * cool / n, '_lum': lum}


def aggregate(frames):
    st = [frame_stats(f) for f in frames]
    if not st:
        return None
    keys = ('luma', 'p10', 'p90', 'sat', 'orange', 'cool')
    out = {k: round(sum(s[k] for s in st) / len(st), 2) for k in keys}
    mot = [sum(abs(a - b) for a, b in zip(x['_lum'], y['_lum'])) / len(x['_lum']) for x, y in zip(st, st[1:])]
    out['motion'] = round(sum(mot) / len(mot), 2) if mot else 0.0
    out['frames'] = len(st)
    return out


def video_shot_metrics(path, shots, fps=10):
    """{shot_id: metrics} for each shot's time range in a video (global times)."""
    return {s['id']: aggregate(_frames_from_video(path, s['start'], s['end'], fps)) for s in shots}


def images_metrics(paths):
    return aggregate(_frames_from_images(paths))


def per_second_luma(path, duration, fps=10):
    fr = _frames_from_video(path, 0.0, duration, fps)
    out = []
    for sec in range(int(duration + 0.999)):
        chunk = fr[sec * fps:(sec + 1) * fps]
        if chunk:
            out.append(round(sum(frame_stats(f)['luma'] for f in chunk) / len(chunk), 1))
    return out


def compare_table(ref, got, tol):
    """Rows (metric, ref, got, delta, ok) using tolerance dict {metric: abs tolerance}."""
    rows = []
    for k, t in tol.items():
        if ref.get(k) is None or got.get(k) is None:
            continue
        d = got[k] - ref[k]
        rows.append((k, ref[k], got[k], round(d, 2), abs(d) <= t))
    return rows


TOLERANCE = {'luma': 18.0, 'p90': 30.0, 'sat': 0.10, 'orange': 6.0, 'cool': 12.0, 'motion': 4.0}


if __name__ == '__main__':
    import sys
    video, shots_json, out = sys.argv[1:4]
    shots = json.load(open(shots_json, encoding='utf-8'))['shots']
    import os
    ref_dir = sys.argv[4] if len(sys.argv) > 4 else None
    hero = {}
    if ref_dir:
        for s in shots:
            fr = sorted(os.path.join(ref_dir, f) for f in os.listdir(ref_dir) if f.startswith(s['id'] + '_t'))
            if fr:
                hero[s['id']] = images_metrics(fr)
    data = {'source': os.path.basename(video), 'method': __doc__.split('\n')[0], 'tolerance': TOLERANCE,
            'shots': video_shot_metrics(video, shots), 'hero': hero,
            'luma_per_second': per_second_luma(video, shots[-1]['end'])}
    json.dump(data, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('->', out)
