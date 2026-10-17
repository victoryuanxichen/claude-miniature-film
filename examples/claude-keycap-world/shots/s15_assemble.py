"""S15 43.0-48.0 s  Many become one: the copies stream over and stack into a giant Clawd.

A held wide, low shot (spectacle needs a stable frame). The minis flow right, building the
giant from the bottom layer up; the last stragglers land on the ragged top; the eyes are
the missing cells. Clawd watches from the left foreground and looks up as it grows.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import env as E
from mfilm import swarm as SW

from . import common as S
from .s12_tree import grow_tree


def build(ctx):
    g = ctx.g
    W = lambda k: S.on_ground(E.layout_to_world(ctx.layout[k], S.MEADOW_SIZE))  # noqa: E731
    base, giant = W('tree'), W('giant')
    S.meadow_set(ctx, dense_center=giant, dense_r=30.0)
    grow_tree(ctx, base, static=True)
    SW.assemble_giant('GiantBuild', S.mini_source(), giant, g(43.2), g(47.4), base + Vector(S.PILE_OFFSET),
                      S.PILE_R, ground_z=base.z, cell=S.MINI_CELL)
    me = S.on_ground(base + Vector(S.CLAWD_UNDER_TREE))
    rig = S.clawd(me, yaw=S.yaw_to(me, giant))
    C.idle(rig, 1, ctx.last)
    C.blink(rig, g(44.5))
    C.tilt(rig, g(45.5), pitch_deg=-10)
    C.tilt(rig, g(47.2), pitch_deg=-16)
    C.blink(rig, g(47.6))
    cam, tgt = CAM.camera('Cam', tuple(giant + Vector((-12.0, -26.0, 1.6))), tuple(giant + Vector((-5.0, 0, 3.2))),
                          lens=35, fstop=5.6)
    CAM.move(cam, [(1, giant + Vector((-12.0, -26.0, 1.6))), (ctx.last, giant + Vector((-11.4, -24.5, 1.6)))])
