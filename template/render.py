"""Re-render an already built shot with another preset (no rebuild). Works on a render box
that only has the project folder:
    blender -b blend/S05.blend -P render.py -- --preset final               # whole shot
    blender -b blend/S05.blend -P render.py -- --preset cycles --frames 7-60
    blender -b blend/S05.blend -P render.py -- --preset look --stills 20,44
Resumable: existing frames are skipped (placeholders let several machines share a folder).
"""
import argparse
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))
from mfilm import project  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--preset', default='final')
ap.add_argument('--frames', default=None, help='a-b (local frames); default = whole shot incl. handles')
ap.add_argument('--stills', default=None)
a = ap.parse_args(argv)

sc = bpy.context.scene
shot = sc.name
project.apply_preset(sc, a.preset)
if a.stills:
    project.render_stills(sc, [int(x) for x in a.stills.split(',')], os.path.join(HERE, 'out', 'stills'),
                          f'{shot}_{a.preset}')
else:
    f0, f1 = (map(int, a.frames.split('-')) if a.frames else (sc.frame_start, sc.frame_end))
    project.render_range(sc, f0, f1, os.path.join(HERE, 'out', 'frames', shot))
