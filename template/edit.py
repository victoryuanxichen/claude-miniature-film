#!/usr/bin/env python3
"""Edit, review and timing checks (plain Python 3 + ffmpeg, no Blender needed).

    python3 edit.py check                      # shots.json sanity: gaps, overlaps, cuts vs beat grid
    python3 edit.py assemble [--out out/film.mp4] [--crf 16]   # cut all rendered shots + music
    python3 edit.py sheet S05 [--every 6]       # contact sheet of a rendered shot
    python3 edit.py strip 28.37 [--before 0.3 --after 0.5]     # every frame across a cut (global time)
    python3 edit.py overview [--n 24]           # whole film at a glance (from the assembled mp4)
    python3 edit.py compare S05 [--t 13.5]      # your still next to the benchmark frame (acceptance)
    python3 edit.py metrics [S05 S06 ...]       # luma / contrast / saturation / orange coverage /
                                                #   motion of your frames vs the benchmark bands
Each shot is compared with the benchmark shot named in its "ref" field (default: same id).
Benchmark data lives in reference/ (ref/<shot>_t<sec>.jpg frames + metrics.json).
Rendered frames are expected in out/frames/<shot>/0001.png ... (local frame numbers, handles
included). Shots without frames are replaced by black + their id so the cut always assembles.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'shots.json'), encoding='utf-8'))
FPS, BPM, H = CFG.get('fps', 30), CFG.get('bpm', 120), CFG.get('handles', 6)
W, HGT = CFG.get('res', [1920, 1080])
SPB = 60.0 / BPM


def ff(*args):
    cmd = ['ffmpeg', '-v', 'error', '-y', *map(str, args)]
    subprocess.run(cmd, check=True)


def frames_dir(sid):
    return os.path.join(HERE, 'out', 'frames', sid)


def shot_frames(s):
    dur = int(round((s['end'] - s['start']) * FPS))
    return [os.path.join(frames_dir(s['id']), f'{H + 1 + i:04d}.png') for i in range(dur)]


def cmd_check(_):
    shots = CFG['shots']
    ok = True
    for a, b in zip(shots, shots[1:]):
        if abs(a['end'] - b['start']) > 1e-6:
            print(f"GAP/OVERLAP between {a['id']} ({a['end']}) and {b['id']} ({b['start']})")
            ok = False
    print(f'{"shot":5} {"start":>7} {"end":>7} {"len":>5}  cut-out vs beat')
    for s in shots:
        beats = s['end'] / SPB
        off = (beats - round(beats)) * SPB
        flag = '' if abs(off) < 0.5 / FPS else ('  (off-beat: allowed)' if s.get('offbeat') else '  <-- OFF BEAT')
        if flag.endswith('BEAT'):
            ok = False
        print(f"{s['id']:5} {s['start']:7.3f} {s['end']:7.3f} {s['end'] - s['start']:5.2f}  {off * 1000:+6.0f} ms{flag}")
    total = shots[-1]['end'] - shots[0]['start']
    print(f'total {total:.2f}s, {len(shots)} shots, BPM {BPM}, beat = {SPB * FPS:.1f} frames')
    return 0 if ok else 1


def cmd_assemble(a):
    seq = os.path.join(HERE, 'out', '_seq')
    shutil.rmtree(seq, ignore_errors=True)
    os.makedirs(seq)
    black = os.path.join(seq, '_black.png')
    ff('-f', 'lavfi', '-i', f'color=c=black:s={W}x{HGT}', '-frames:v', 1, black)
    n = 0
    for s in CFG['shots']:
        fr = shot_frames(s)
        have = sum(os.path.exists(p) for p in fr)
        print(f"{s['id']}: {have}/{len(fr)} frames")
        for p in fr:
            n += 1
            dst = os.path.join(seq, f'{n:05d}.png')
            os.symlink(p if os.path.exists(p) else black, dst)
    out = a.out or os.path.join(HERE, 'out', CFG.get('slug', 'film') + '.mp4')
    args = ['-framerate', FPS, '-i', os.path.join(seq, '%05d.png')]
    music = CFG.get('audio', {}).get('music')
    if music and os.path.exists(os.path.join(HERE, music)):
        args += ['-itsoffset', CFG['audio'].get('offset', 0.0), '-i', os.path.join(HERE, music),
                 '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '256k', '-shortest']
    ff(*args, '-vf', f'scale={W}:{HGT}:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', a.crf,
       '-preset', 'slow', '-movflags', '+faststart', out)
    print('->', out)


def cmd_sheet(a):
    d = frames_dir(a.shot)
    out = os.path.join(HERE, 'out', 'check', f'{a.shot}_sheet.jpg')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ff('-framerate', FPS, '-start_number', H + 1, '-i', os.path.join(d, '%04d.png'),
       '-vf', f"select='not(mod(n\\,{a.every}))',scale=480:-1,tile=4x4:padding=4:color=red", '-frames:v', 1, out)
    print('->', out)


def _locate(t):
    for s in CFG['shots']:
        if s['start'] <= t < s['end']:
            return s
    return CFG['shots'][-1]


def cmd_strip(a):
    """Frames from t-before to t+after taken from whichever shot owns each instant."""
    tmp = os.path.join(HERE, 'out', '_strip')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    t0, t1 = a.t - a.before, a.t + a.after
    k = 0
    t = t0
    while t < t1 - 1e-9:
        s = _locate(t)
        lf = H + 1 + int(round((t - s['start']) * FPS))
        src = os.path.join(frames_dir(s['id']), f'{lf:04d}.png')
        if os.path.exists(src):
            k += 1
            os.symlink(src, os.path.join(tmp, f'{k:04d}.png'))
        t += 1.0 / FPS
    out = os.path.join(HERE, 'out', 'check', f'strip_{a.t:.2f}.jpg')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cols = 8
    rows = (k + cols - 1) // cols
    ff('-framerate', FPS, '-i', os.path.join(tmp, '%04d.png'), '-vf',
       f'scale=320:-1,tile={cols}x{rows}:padding=3:color=red', '-frames:v', 1, out)
    print('->', out, f'({k} frames)')


def cmd_overview(a):
    src = os.path.join(HERE, 'out', CFG.get('slug', 'film') + '.mp4')
    total = CFG['shots'][-1]['end']
    out = os.path.join(HERE, 'out', 'check', 'overview.jpg')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    ff('-i', src, '-vf', f'fps={a.n / total},scale=320:-1,tile=6x{(a.n + 5) // 6}:padding=3:color=red',
       '-frames:v', 1, out)
    print('->', out)


REF = os.path.join(HERE, 'reference')


def _shot(sid):
    return next(s for s in CFG['shots'] if s['id'] == sid)


def _ref_frames(ref_id):
    d = os.path.join(REF, 'ref')
    out = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.startswith(ref_id + '_t'):
            out.append((float(f[len(ref_id) + 2:-4]), os.path.join(d, f)))
    return out


def cmd_compare(a):
    """Side by side: left = benchmark frame, right = your still at the matching moment."""
    s = _shot(a.shot)
    ref_id = s.get('ref', s['id'])
    refs = _ref_frames(ref_id)
    if not refs:
        print(f'no reference frames for {ref_id} in {REF}/ref')
        return 1
    if a.t is not None:
        times = [a.t]
    else:
        times = [s['start'] + t for t in s.get('hero', [])] or [r[0] for r in refs]
    os.makedirs(os.path.join(HERE, 'out', 'check'), exist_ok=True)
    bad = 0
    for tg in times:
        lf = H + 1 + int(round((tg - s['start']) * FPS))
        mine = os.path.join(HERE, 'out', 'stills', f"{s['id']}_f{lf:04d}.png")
        if not os.path.exists(mine):
            alt = os.path.join(frames_dir(s['id']), f'{lf:04d}.png')
            mine = alt if os.path.exists(alt) else None
        if mine is None:
            print(f"  t={tg:.2f}: no still/frame {s['id']}_f{lf:04d}.png (build.py --stills t=…)")
            bad += 1
            continue
        want = tg - s['start'] + _shot(ref_id)['start'] if ref_id in [x['id'] for x in CFG['shots']] else tg
        rt, rp = min(refs, key=lambda r: abs(r[0] - want))
        out = os.path.join(HERE, 'out', 'check', f"compare_{s['id']}_t{tg:05.2f}.jpg")
        ff('-i', rp, '-i', mine, '-filter_complex',
           '[0]scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2[a];'
           '[1]scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2[b];'
           '[a][b]hstack', '-q:v', 3, out)
        print(f'  t={tg:.2f}: ref {os.path.basename(rp)}  |  mine {os.path.basename(mine)}  ->  {out}')
    return 1 if bad else 0


def cmd_metrics(a):
    import filmmetrics as FM
    ref = json.load(open(os.path.join(REF, 'metrics.json'), encoding='utf-8'))
    tol = ref.get('tolerance', FM.TOLERANCE)
    ids = a.shots or [s['id'] for s in CFG['shots']]
    fails = 0
    for sid in ids:
        s = _shot(sid)
        fr = [p for p in shot_frames(s)[::3] if os.path.exists(p)]
        stills = not fr
        # rendered shot -> whole-shot reference; hero stills only -> reference hero frames
        r = (ref.get('hero', {}) if stills else ref['shots']).get(s.get('ref', sid))
        if stills:
            st = os.path.join(HERE, 'out', 'stills')
            fr = sorted(os.path.join(st, f) for f in os.listdir(st) if f.startswith(sid + '_f')) \
                if os.path.isdir(st) else []
        if not fr or not r:
            print(f'{sid}: nothing to measure' if r else f'{sid}: no reference metrics')
            continue
        got = FM.images_metrics(fr)
        rows = FM.compare_table(r, got, {k: v for k, v in tol.items() if not (stills and k == 'motion')})
        nbad = sum(1 for row in rows if not row[4])
        fails += nbad
        print(f"{sid} (ref {s.get('ref', sid)}, {len(fr)} frames): " + '  '.join(
            f"{k} {g:.1f}/{rv:.1f}{'' if ok else ' ✗'}" for k, rv, g, d, ok in rows))
    print('all within tolerance' if not fails else f'{fails} metric(s) out of tolerance')
    return 1 if fails else 0


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest='cmd', required=True)
sub.add_parser('check')
p = sub.add_parser('assemble')
p.add_argument('--out')
p.add_argument('--crf', type=int, default=16)
p = sub.add_parser('sheet')
p.add_argument('shot')
p.add_argument('--every', type=int, default=6)
p = sub.add_parser('strip')
p.add_argument('t', type=float)
p.add_argument('--before', type=float, default=0.3)
p.add_argument('--after', type=float, default=0.5)
p = sub.add_parser('overview')
p.add_argument('--n', type=int, default=24)
p = sub.add_parser('compare')
p.add_argument('shot')
p.add_argument('--t', type=float, default=None, help='global seconds (default: the shot hero frames)')
p = sub.add_parser('metrics')
p.add_argument('shots', nargs='*')
a = ap.parse_args()
sys.exit({'check': cmd_check, 'assemble': cmd_assemble, 'sheet': cmd_sheet, 'strip': cmd_strip,
          'overview': cmd_overview, 'compare': cmd_compare, 'metrics': cmd_metrics}[a.cmd](a) or 0)
