"""S10 30.0-33.0 s  Macro: through the grass toward the lens, then a discovery.

Camera at grass-blade height with a 75 mm lens: foreground blades melt into blur, dew and
daisies sparkle. Clawd walks toward camera, squints in the sun (31.0 s), and on the beat at
32.0 s turns: far off, an orange cursor stands in the grass.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import env as E

from . import common as S


def build(ctx):
    g = ctx.g
    W = lambda k: S.on_ground(E.layout_to_world(ctx.layout[k], S.MEADOW_SIZE))  # noqa: E731
    land, seed = W('clawd_land'), W('seed')
    S.meadow_set(ctx, grass_density=22.0, dense_center=land, dense_r=25.0)
    E.cursor('SeedCursor', seed)

    start = S.on_ground(land + Vector((-1.2, 6.0, 0)))
    stop = S.on_ground(land + Vector((0.0, 2.0, 0)))
    rig = S.clawd(start, yaw=S.yaw_to(start, stop))
    C.walk(rig, g(30.1), [start, stop], speed=2.6, step=7)
    C.squint(rig, g(31.0), g(31.6), 0.25)
    C.turn(rig, g(32.0), g(32.35), S.yaw_to(stop, seed))
    C.tilt(rig, g(32.4), roll_deg=-6)

    # camera sits a little left so the far cursor (seed) lands inside the right third when Clawd turns
    cam, tgt = CAM.camera('Cam', tuple(land + Vector((-0.6, -3.2, 0.65))), tuple(stop + Vector((0, 0, 0.7))),
                          lens=75, fstop=2.8)
    CAM.move(cam, [(1, land + Vector((-0.6, -3.2, 0.65))), (ctx.last, land + Vector((-0.6, -2.6, 0.65)))])
    CAM.follow_bake(tgt, rig.root, 1, ctx.last, offset=(0, 0, 0.75), smooth=8)
    CAM.handheld(cam, tgt, 1, 0.015, 0.01)
