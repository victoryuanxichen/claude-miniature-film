"""S13 40.93-42.0 s  Mini-Clawd rain, close and low.

Cut on the first impacts. Camera in the grass, foreground blades out of focus, minis drop
through frame and hit the ground around Clawd with real collisions (rigid bodies, baked).
"""
import math

from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import swarm as SW

from . import common as S
from .s12_tree import grow_tree


def build(ctx):
    g = ctx.g
    W = lambda k: S.on_ground(E.layout_to_world(ctx.layout[k], S.MEADOW_SIZE))  # noqa: E731
    base = W('tree')
    view = S.on_ground(base + Vector((3.0, -6.0, 0)))
    S.meadow_set(ctx, dense_center=view, dense_r=20.0)
    grow_tree(ctx, base, static=True)
    rig = S.clawd(S.on_ground(base + Vector((2.6, -1.8, 0))), yaw=-30)
    C.idle(rig, 1, g(40.95))
    C.squash(rig, g(41.0), 0.1)
    C.squash(rig, g(41.0) + 5, -0.05)
    C.squash(rig, g(41.0) + 10, 0.0, 'back')
    C.blink(rig, g(41.5))

    r = core.rng(13)
    starts = []
    for i in range(90):
        a, d = r.uniform(-2.4, 0.9), r.uniform(1.5, 9.0)
        p = view + Vector((math.cos(a) * d, math.sin(a) * d * 0.8 + 2.0, r.uniform(6.0, 18.0)))
        starts.append(p)
    trunk = core.box('TrunkCollider', (base.x - 1.5, base.y - 1.5, base.z), (base.x + 1.5, base.y + 1.5, base.z + 22),
                     core.coll('Colliders'))
    trunk.hide_render = True
    SW.rain_rigidbody('Rain', S.mini_source(), starts, 1, g(41.3), ground_z=view.z, colliders=[trunk],
                      f_end=ctx.last)

    cam, tgt = CAM.camera('Cam', tuple(view + Vector((1.5, -8.0, 0.9))), tuple(view + Vector((0, 2.0, 1.4))),
                          lens=50, fstop=2.0)
    CAM.handheld(cam, tgt, 1, 0.04, 0.03)
