"""S05 11.5-17.5 s  Out of the screen and onto the keyboard.

Seen from outside: Clawd steps out of the monitor glass (rings spread on the screen behind
it), drifts down to the sleeping keyboard and lands on the splash key (13.4 s, key presses,
water kicks up, the key wakes up). A curious tilt, a blink, then a hop to the waterfall key
(lands 16.0 s, wakes up too). The camera follows the descent and settles into a close-up.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import fx as FX
from mfilm import lighting as L

from . import common as S


def build(ctx):
    g, f = ctx.g, ctx.f
    k = S.keyboard_set(ctx)
    kb = k['kb']
    L.rig_keyboard(ctx.sc)
    S.wake(ctx, kb)
    a, b = kb.top('R1K11'), kb.top('R2K12')
    sy = k['monitor']['center'].y - 0.05
    out = Vector((a.x, sy, 6.4))

    rig = S.clawd((a.x, sy + 0.8, 6.4), yaw=0)
    C.place(rig, 1, (a.x, sy + 0.8, 6.4))
    C.place(rig, f(0.5), (a.x, sy - 1.4, 6.3), ease='sine')
    C.place(rig, g(13.4), a, ease='ease')
    C.legs_pose(rig, f(0.5), 0, 0.0)
    C.legs_pose(rig, f(0.9), 0, 0.5, 'sine')
    C.legs_pose(rig, g(13.3), 0, 0.0)
    C.squash(rig, g(13.4) - 3, -0.08)
    C.squash(rig, g(13.4), 0.22)
    C.squash(rig, g(13.4) + 9, 0.0, 'back')
    FX.ripple('ScreenRipple', (out.x, sy - 0.08, out.z + 0.7), 7.0, f(0.05), 34, normal='Y')
    FX.splash('Splash1', a - Vector((0, 0, 0.45)), g(13.4), n=26, speed=5.0)

    C.idle(rig, g(13.4) + 10, g(15.0))
    C.blink(rig, g(14.2))
    C.tilt(rig, g(14.45), roll_deg=11)
    C.tilt(rig, g(14.85), roll_deg=0)
    C.hop(rig, g(15.1), g(16.0), b, height=1.5, yaw_deg=S.yaw_to(b, (b.x - 2, b.y - 8)))
    FX.splash('Splash2', b - Vector((0, 0, 0.5)), g(16.0), n=14, speed=3.5)
    C.blink(rig, g(16.9))

    cam, tgt = CAM.camera('Cam', (2.5, 12.0, 6.5), (a.x, sy - 1.0, 6.4), lens=35, fstop=4.0)
    CAM.move(cam, [(1, (2.5, 12.0, 6.5)), (g(13.4), (a.x - 2.5, a.y - 7.5, 3.2)),
                   (g(15.0), (a.x - 2.0, a.y - 6.4, 2.5)), (g(16.2), (b.x - 1.0, b.y - 6.0, 2.4)),
                   (ctx.last, (b.x - 0.4, b.y - 5.2, 2.2))])
    CAM.follow_bake(tgt, rig.root, 1, ctx.last, offset=(0, 0, 0.7), smooth=8)
    CAM.lens_keys(cam, [(1, 35), (g(15.0), 50)])
    CAM.fstop_keys(cam, [(1, 4.0), (g(15.0), 2.8)])
    CAM.handheld(cam, tgt, 1, 0.02, 0.01)
