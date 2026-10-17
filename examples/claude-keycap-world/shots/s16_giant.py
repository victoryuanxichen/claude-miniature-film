"""S16 48.0-51.9 s  The giant steps and waves; the camera rises to a plan view; a glint opens.

The giant takes two heavy steps and waves with an arm made of minis. The camera starts low
behind Clawd, then rises fast to straight overhead (tree crown left, giant right, pond top
left - the exact layout of the keycap diorama). A tiny glint between crown and giant grows
into a glass lens: the hard cut to S17 swaps the real meadow for the voxel miniature.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import env as E
from mfilm import fx as FX
from mfilm import swarm as SW

from . import common as S
from .s12_tree import grow_tree


def build(ctx):
    g = ctx.g
    W = lambda k: S.on_ground(E.layout_to_world(ctx.layout[k], S.MEADOW_SIZE))  # noqa: E731
    base, giant = W('tree'), W('giant')
    S.meadow_set(ctx, dense_center=(base + giant) / 2, dense_r=35.0)
    grow_tree(ctx, base, static=True)
    me = S.on_ground(base + Vector(S.CLAWD_UNDER_TREE))
    gr = SW.giant_rig('Giant', S.mini_source(), giant, S.MINI_CELL, facing_deg=S.yaw_to(giant, me))
    step_to = S.on_ground(giant + (me - giant).normalized() * 2.5)
    C.walk(gr, g(48.2), [giant, step_to], speed=1.6, step=12, swing=18, bob=0.15)
    C.wave(gr, g(49.0), 'R', reps=2, period=10)
    rig = S.clawd(me, yaw=S.yaw_to(me, giant))
    C.idle(rig, 1, ctx.last)
    C.tilt(rig, g(48.3), pitch_deg=-14)
    C.blink(rig, g(49.4))

    mid = (base + giant) / 2
    cam, tgt = CAM.camera('Cam', tuple(me + Vector((-2.5, -5.0, 0.8))), tuple(giant + Vector((0, 0, 3.5))), lens=28,
                          fstop=4.0)
    CAM.move(cam, [(1, me + Vector((-2.5, -5.0, 0.8))), (g(49.6), me + Vector((-4.0, -9.0, 2.5))),
                   (g(50.5), me + Vector((-4.0, -10.0, 5.0)), 'expo'), (g(51.35), mid + Vector((0, -0.6, 75.0)))])
    CAM.move(tgt, [(1, giant + Vector((0, 0, 3.5))), (g(50.5), giant + Vector((0, 0, 3.0)), 'expo'),
                   (g(51.35), mid + Vector((0, 0, 0)))])
    CAM.lens_keys(cam, [(g(50.5), 28), (g(51.35), 35)])
    FX.lens_bubble('Lens', mid + Vector((0, 0, 9.0)), 12.0, g(51.55), g(51.7), ctx.last)
