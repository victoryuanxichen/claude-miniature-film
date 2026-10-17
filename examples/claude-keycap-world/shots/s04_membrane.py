"""S04 10.5-11.5 s  Through the glass: Clawd walks into a lens of light and is cut by it.

Side tracking shot, wide lens for strong perspective on the code rows. The membrane is the
screen glass made visible; S05 picks up the same instant from the outside (action match).
"""
from mfilm import camera as CAM
from mfilm import character as C
from mfilm import fx as FX

from . import common as S


def build(ctx):
    f = ctx.f
    S.terminal_set(ctx, cursor=False)
    mem = FX.membrane('Membrane', (0.4, 0, 0.9), radius=2.0, flatten=0.3, axis='X')
    FX.membrane_pass(mem, f(-0.2), f(0.15), f(1.0) + ctx.H, peak=1.0)
    rig = S.clawd((-2.3, 0, 0), yaw=90)
    C.walk(rig, 1, [(-2.3, 0, 0), (2.4, 0, 0)], speed=3.0, step=6)
    cam, tgt = CAM.camera('Cam', (-2.0, -5.2, 0.9), (0, 0, 0.7), lens=28, fstop=2.8)
    CAM.move(cam, [(1, (-2.2, -5.2, 0.9)), (ctx.last, (1.6, -5.2, 0.9))])
    CAM.follow_bake(tgt, rig.root, 1, ctx.last, offset=(0.6, 0, 0.7), smooth=4)
