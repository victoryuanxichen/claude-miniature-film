"""S06 17.5-20.0 s  The spacebar valley: a side-tracking walk along a river panorama.

Clawd drops onto the spacebar (it wakes up), walks along it while the camera slides
alongside at keycap height, then jumps out of frame top-right.
"""
from mfilm import camera as CAM
from mfilm import character as C
from mfilm import lighting as L

from . import common as S


def build(ctx):
    g = ctx.g
    kb = S.keyboard_set(ctx)['kb']
    L.rig_keyboard(ctx.sc)
    S.wake(ctx, kb)
    sp = kb.top('R5K3')
    z, y = sp.z, sp.y
    x0, x1 = sp.x - 1.6, sp.x + 2.8

    rig = S.clawd((x0 - 0.6, y, z + 5.0), yaw=90)
    C.place(rig, 1, (x0 - 0.6, y, z + 5.0))
    C.place(rig, g(18.0), (x0, y, z), ease='quad_in')
    C.squash(rig, g(18.0), 0.2)
    C.squash(rig, g(18.0) + 8, 0.0, 'back')
    end = C.walk(rig, g(18.25), [(x0, y, z), (x1, y, z)], speed=3.8, step=6)
    C.hop(rig, max(end, g(19.45)), g(20.0) + ctx.H, (x1 + 3.5, y + 3.0, z + 4.5), height=2.5)

    cam, tgt = CAM.camera('Cam', (x0 - 3.0, y - 11.5, z + 0.7), (x0, y, z + 0.6), lens=50, fstop=2.8)
    CAM.move(cam, [(1, (x0 - 3.5, y - 11.5, z + 0.7)), (ctx.last, (x1 + 1.5, y - 11.5, z + 0.8))])
    CAM.follow_bake(tgt, rig.root, 1, ctx.last, offset=(0.4, 0, 0.6), smooth=6)
