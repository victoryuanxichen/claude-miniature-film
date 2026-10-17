"""S07 20.0-24.0 s  Hopping across the board; every landing wakes a world.

High three-quarter view. Landings sit exactly on the beats 20.5 ... 23.0 (one hop per beat),
each key presses and lights up from inside, leaving a lit trail of footprints across the
dark board. Then the camera rises and pulls back to show the trail.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import lighting as L

from . import common as S

ROUTE = ['R4K4', 'R3K5', 'R2K6', 'R1K7', 'R0K8', 'R0K9']


def build(ctx):
    g = ctx.g
    kb = S.keyboard_set(ctx)['kb']
    L.rig_keyboard(ctx.sc)
    S.wake(ctx, kb)
    tops = [kb.top(k) for k in ROUTE]
    land = [g(20.5 + 0.5 * i) for i in range(len(ROUTE))]

    start = tops[0] + Vector((-1.6, -1.8, 3.2))
    rig = S.clawd(start, yaw=S.yaw_to(start, tops[0]))
    C.place(rig, 1, start)
    C.place(rig, land[0], tops[0], ease='quad_in')
    C.squash(rig, land[0], 0.2)
    C.squash(rig, land[0] + 3, 0.0)
    for i in range(1, len(ROUTE)):
        C.hop(rig, land[i - 1] + 3, land[i], tops[i], height=1.1, yaw_deg=S.yaw_to(tops[i - 1], tops[i]),
              squash_amt=0.18)
    C.turn(rig, g(23.3), g(23.6), -20)
    C.blink(rig, g(23.7))

    cam, tgt = CAM.camera('Cam', tuple(tops[0] + Vector((-12, -17, 12))), tuple(tops[0]), lens=40, fstop=4.0)
    CAM.move(cam, [(1, tops[0] + Vector((-12, -17, 12))), (g(23.0), tops[3] + Vector((-8, -15, 13))),
                   (ctx.last, tops[3] + Vector((-6, -24, 24)))])
    CAM.follow_bake(tgt, rig.root, 1, ctx.last, offset=(0, 0, 0.5), smooth=10)
    CAM.lens_keys(cam, [(g(23.0), 40), (ctx.last, 32)])
