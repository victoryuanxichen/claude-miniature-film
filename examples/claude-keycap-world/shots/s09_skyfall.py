"""S09 28.37-30.0 s  Inverted scale: from inside the key the world is endless.

Low wide angle looking up into a blue sky over a misty treeline. Clawd falls from high up,
legs dangling, and lands in the grass (squash, blink). The camera tilts down with it.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import env as E

from . import common as S


def build(ctx):
    g = ctx.g
    land = S.on_ground(E.layout_to_world(ctx.layout['clawd_land'], S.MEADOW_SIZE))
    S.meadow_set(ctx, dense_center=land, dense_r=30.0)
    rig = S.clawd(land + Vector((0, 0, 42)), yaw=-10)
    C.place(rig, 1, land + Vector((0, 0, 42)))
    C.place(rig, g(29.7), land, ease='quad_in')
    C.legs_pose(rig, 1, 0, 0.0)
    C.legs_pose(rig, g(28.9), 8, 0.2, 'sine')
    C.legs_pose(rig, g(29.6), 0, 0.0)
    C.squash(rig, g(29.7) - 3, -0.12)
    C.squash(rig, g(29.7), 0.26)
    C.squash(rig, g(29.7) + 9, 0.0, 'back')
    C.blink(rig, g(29.85))

    cam, tgt = CAM.camera('Cam', tuple(land + Vector((2.5, -28, 2.4))), tuple(land + Vector((0, 0, 30))), lens=24,
                          fstop=5.6)
    CAM.move(cam, [(1, land + Vector((2.5, -28, 2.4))), (ctx.last, land + Vector((2.0, -24, 2.0)))])
    CAM.follow_bake(tgt, rig.root, 1, ctx.last, offset=(0, 0, 0.6), smooth=6)
