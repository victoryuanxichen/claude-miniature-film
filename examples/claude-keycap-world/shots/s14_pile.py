"""S14 42.0-43.0 s  A sea of copies under the tree, all wriggling."""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import env as E
from mfilm import swarm as SW

from . import common as S
from .s12_tree import grow_tree


def build(ctx):
    W = lambda k: S.on_ground(E.layout_to_world(ctx.layout[k], S.MEADOW_SIZE))  # noqa: E731
    base = W('tree')
    S.meadow_set(ctx, dense_center=base, dense_r=25.0)
    grow_tree(ctx, base, static=True)
    me = S.on_ground(base + Vector(S.CLAWD_UNDER_TREE))
    rig = S.clawd(me, yaw=S.yaw_to(me, base + Vector(S.PILE_OFFSET)))
    C.idle(rig, 1, ctx.last)
    SW.pile('Pile', S.mini_source(), base + Vector(S.PILE_OFFSET), S.PILE_R, 320, ground_z=base.z,
            avoid=[(tuple(base), 2.4), (tuple(me), 1.6)])
    cam, tgt = CAM.camera('Cam', tuple(base + Vector((-4.5, -17.0, 1.4))), tuple(base + Vector((2.0, -3.0, 1.5))),
                          lens=30, fstop=4.0)
    CAM.move(cam, [(1, base + Vector((-4.5, -17.0, 1.4))), (ctx.last, base + Vector((-4.2, -15.8, 1.35)))])
