"""S11 33.0-36.0 s  Planting the cursor.

Clawd walks up to the cursor, circles it once (curiosity), and the cursor sinks into the
ground, leaving a small warm light: the only warm light in the meadow, and the seed of the
tree in S12.
"""
import math

from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import fx as FX

from . import common as S


def build(ctx):
    g = ctx.g
    W = lambda k: S.on_ground(E.layout_to_world(ctx.layout[k], S.MEADOW_SIZE))  # noqa: E731
    land, seed = W('clawd_land'), W('seed')
    S.meadow_set(ctx, dense_center=seed, dense_r=25.0)
    cur = E.cursor('SeedCursor', seed)
    core.key(cur, 'location', g(35.4), seed.copy(), 'quad_in')
    core.key(cur, 'location', g(35.8), seed - Vector((0, 0, 1.15)))
    core.key_visible(cur, g(35.85), False)
    FX.glow_seed('Seed', seed + Vector((0, 0, 0.03)), g(35.8))

    start = S.on_ground(land + Vector((0.0, 2.0, 0)))
    d = (seed - start).normalized()
    near = S.on_ground(seed - d * 1.7)
    a0 = math.atan2(near.y - seed.y, near.x - seed.x)
    arc = [S.on_ground(seed + Vector((math.cos(a0 + math.radians(45 * i)) * 1.7,
                                      math.sin(a0 + math.radians(45 * i)) * 1.7, 0))) for i in range(0, 4)]
    rig = S.clawd(start, yaw=S.yaw_to(start, seed))
    end = C.walk(rig, g(33.1), [start, near], speed=3.2, step=7)
    end = C.walk(rig, end + 2, arc, speed=3.0, step=6)
    C.turn(rig, end + 2, end + 7, S.yaw_to(arc[-1], seed))
    C.tilt(rig, g(35.8), pitch_deg=12)
    C.blink(rig, g(35.95))

    cam, tgt = CAM.camera('Cam', tuple(seed + Vector((-4.5, -6.0, 1.3))), tuple(seed + Vector((0, 0, 0.6))),
                          lens=40, fstop=3.2)
    CAM.orbit(cam, (seed.x, seed.y, seed.z), 7.0, 1.3, -38, -18, 1, ctx.last)
    CAM.follow_bake(tgt, rig.root, 1, ctx.last, offset=(0, 0, 0.6), smooth=12)
