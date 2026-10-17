"""S12 36.0-40.93 s  The seed becomes a tree; the tree bears copies; the copies fall on the drop.

A dark column (cursor proportions) rises from the glowing seed and keeps growing into a
trunk, branches push out, the voxel canopy blooms inside-out, a green light shaft flares
(38.3 s), orange fruit pops out all over the canopy (39.0-39.8 s) - every fruit is a mini
Clawd - and on the music's big hit at 40.0 s they all start to fall. Camera pulls back and
tilts up from the trunk base to the whole tree with Clawd small at its foot.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import fx as FX
from mfilm import gn
from mfilm import materials as M
from mfilm import swarm as SW
from mfilm import voxel as VX

from . import common as S

TREE_KW = dict(cell=1.0, trunk_h=22, trunk_w=3, canopy_r=8, fruits=70, seed=5)


def grow_tree(ctx, base, t_trunk=(36.0, 37.6), t_canopy=(37.2, 39.0), static=False):
    """Trunk + canopy reveal. static=True builds the finished tree (later shots)."""
    g = ctx.g
    cast = core.coll('Tree')
    tr = VX.tree('Tree', base=tuple(base), c=cast, **TREE_KW)
    bark = VX.cube_obj('TrunkCube', 1.0, M.bark(), bevel=0.04, c=cast)
    leaf = VX.cube_obj('LeafCube', 1.0, M.leaf(), bevel=0.12, c=cast)
    tp = VX.trunk_points('Trunk', tr, c=cast)
    tm = gn.add_modifier(tp, gn.reveal_group('TrunkGN', bark, width=0.05, overshoot=0.3))
    cm = gn.add_modifier(tr['canopy'], gn.reveal_group('CanopyGN', leaf, width=0.15, overshoot=1.0))
    if static:
        gn.set_input(tm, 'Progress', 1.2)
        gn.set_input(cm, 'Progress', 1.3)
    else:
        gn.set_input(tm, 'Progress', 0.0, g(t_trunk[0]), 'cubic_out')
        gn.set_input(tm, 'Progress', 1.1, g(t_trunk[1]))
        gn.set_input(cm, 'Progress', 0.0, g(t_canopy[0]))
        gn.set_input(cm, 'Progress', 1.3, g(t_canopy[1]))
    return tr


def build(ctx):
    g = ctx.g
    W = lambda k: S.on_ground(E.layout_to_world(ctx.layout[k], S.MEADOW_SIZE))  # noqa: E731
    base = W('tree')
    S.meadow_set(ctx, dense_center=base, dense_r=30.0)
    FX.glow_seed('Seed', base + Vector((0, 0, 0.03)), 1)
    tr = grow_tree(ctx, base)
    FX.beam('Beam', base + Vector((-7, -3, 6)), height=40, radius=2.5, tilt_deg=(10, -14), f0=g(38.3), f1=g(39.3))

    mini = S.mini_source()
    fg, _ = SW.fruit_grow('Fruit', mini, tr['fruit'], g(39.0), g(39.8))
    ff, _ = SW.fruit_fall('FruitFall', mini, tr['fruit'], base.z, g(40.0), g(40.9) + ctx.H, spread=6.0)
    core.key_visible(fg, g(40.0), False)
    core.key_visible(ff, g(40.0) - 1, False)
    core.key_visible(ff, g(40.0), True)

    spot = S.on_ground(base + Vector((2.6, -1.8, 0)))
    rig = S.clawd(spot, yaw=S.yaw_to(spot, base))
    C.idle(rig, 1, ctx.last)
    C.tilt(rig, g(36.4), pitch_deg=-6)
    C.tilt(rig, g(38.2), pitch_deg=-16)
    C.squash(rig, g(40.0), 0.12)
    C.squash(rig, g(40.0) + 6, 0.0, 'back')

    cam, tgt = CAM.camera('Cam', tuple(base + Vector((3.0, -6.5, 1.0))), tuple(base + Vector((1.0, 0, 1.5))),
                          lens=35, fstop=4.0)
    CAM.move(cam, [(1, base + Vector((3.0, -6.5, 1.0))), (g(38.6), base + Vector((6.0, -38.0, 4.0))),
                   (ctx.last, base + Vector((5.5, -35.0, 3.8)))])
    CAM.move(tgt, [(1, base + Vector((1.0, 0, 1.5))), (g(37.6), base + Vector((0.5, 0, 9.0))),
                   (g(38.6), base + Vector((0, 0, 14.0))), (ctx.last, base + Vector((0, 0, 12.0)))])
    CAM.lens_keys(cam, [(1, 35), (g(38.6), 28)])
    CAM.fstop_keys(cam, [(1, 4.0), (g(38.6), 8.0)])
