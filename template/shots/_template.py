"""SXX t0-t1 s  <one-line description: what happens, what the viewer must understand>.

Copy this file to sXX_<slug>.py and point the shot's "module" in shots.json at it.
Rules (see SKILL.md): one event per shot; every move eased; the cut-in/out frames are
ctx.cut_in / ctx.cut_out (handles exist on both sides, keep motion going through them);
use ctx.g(<film seconds>) or ctx.beat(<n>) for timing so cuts and hits land on the grid.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import fx as FX
from mfilm import lighting as L

# from . import common as S          # shared sets (keyboard_set, meadow_set, terminal_set ...)


def build(ctx):
    g = ctx.g                               # film seconds -> local frame
    # 1. world (same seeds/layout as every other shot in this world)
    E.terminal_space()
    L.rig_terminal(ctx.sc)
    # 2. cast + acting
    rig = C.build('Clawd', (0, 0, 0))
    C.idle(rig, 1, ctx.last)
    C.blink(rig, g(ctx.start + 0.6))
    # 3. camera: position + aim target, both eased; DOF focuses on the target
    cam, tgt = CAM.camera('Cam', (0.8, -6.0, 0.6), (0, 0, 0.7), lens=50, fstop=2.8)
    CAM.move(cam, [(1, (0.8, -6.0, 0.6)), (ctx.last, (0.6, -5.2, 0.6))])
    CAM.handheld(cam, tgt, 1, 0.01, 0.005)
