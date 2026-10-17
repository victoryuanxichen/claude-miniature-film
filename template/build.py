"""Build one shot (and optionally render stills or the whole shot).

Run inside Blender, from the project folder:
    blender -b -P build.py -- --shot S05                      # build + save blend/S05.blend
    blender -b -P build.py -- --shot S05 --stills hero        # + render the hero frames (preset look)
    blender -b -P build.py -- --shot S05 --stills 20,44 --preset previs
    blender -b -P build.py -- --shot S05 --render --preset final   # whole shot -> out/frames/S05/
Stills go to out/stills/<shot>_f####.png. 'hero' = the frames listed in shots.json "hero".
"""
import argparse
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, 'lib'), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from mfilm import project  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--shot', required=True)
ap.add_argument('--preset', default=None, help='clay | previs | look | final | cycles_draft | cycles')
ap.add_argument('--stills', default=None, help="'hero' or comma-separated local frames or t=1.5,2.0 (seconds)")
ap.add_argument('--render', action='store_true')
ap.add_argument('--no-save', action='store_true')
a = ap.parse_args(argv)

preset = a.preset or ('look' if a.stills else 'previs')
ctx = project.Ctx(HERE, a.shot, preset)
mod = importlib.import_module('shots.' + ctx.shot['module'])
ctx.setup()
mod.build(ctx)
ctx.finish(save=not a.no_save)
print(f'[build] {a.shot}: frames 1-{ctx.last}, cut {ctx.cut_in}-{ctx.cut_out}, preset {preset}')

if a.stills:
    if a.stills == 'hero':
        frames = [ctx.f(t) for t in ctx.shot.get('hero', [0.5 * (ctx.end - ctx.start)])]
    elif a.stills.startswith('t='):
        frames = [ctx.f(float(t)) for t in a.stills[2:].split(',')]
    else:
        frames = [int(x) for x in a.stills.split(',')]
    for p in project.render_stills(ctx.sc, frames, os.path.join(HERE, 'out', 'stills'), a.shot):
        print('[still]', p)

if a.render:
    project.render_range(ctx.sc, 1, ctx.last, os.path.join(HERE, 'out', 'frames', a.shot))
