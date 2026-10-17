"""S08 24.0-28.37 s  A splash in place, a look at the big key, a big jump, a dive.

Clawd bounces once on the coral key (water kicks up), turns to face the wide hero key,
winds up and leaps; the camera cranes with it, then whips down onto the hero key just as
Clawd plunges through its surface (rings + flash). The cut lands on the impact (off-beat by
design: action decides this cut).
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import fx as FX
from mfilm import keycap as K
from mfilm import lighting as L

from . import common as S


def build(ctx):
    g = ctx.g
    kb = S.keyboard_set(ctx)['kb']
    L.rig_keyboard(ctx.sc)
    a, hero = kb.top('R2K11'), kb.top('R3K12')
    rig = S.clawd(a, yaw=-15)
    C.idle(rig, 1, g(24.8))
    C.blink(rig, g(24.4))
    C.place(rig, g(24.8), a)
    C.hop(rig, g(24.8), g(25.3), a, height=0.7, squash_amt=0.15)
    FX.splash('Splash', a - Vector((0, 0, 0.45)), g(25.3), n=24, speed=5.0)
    K.press(kb, 'R2K11', g(25.3))
    C.turn(rig, g(25.6), g(26.0), S.yaw_to(a, hero))
    C.squint(rig, g(26.1), g(26.5), 0.4)
    C.hop(rig, g(27.0), g(28.0), hero, height=5.0, squash_amt=0.3)
    C.place(rig, g(28.0) + 1, hero)
    C.place(rig, g(28.0) + 9, hero - Vector((0, 0, 1.0)), ease='quad_in')
    core.key(rig.root, 'scale', g(28.0) + 1, Vector((1, 1, 1)))
    core.key(rig.root, 'scale', g(28.0) + 9, Vector((0.2, 0.2, 0.2)))
    FX.ripple('DiveRings', hero + Vector((0, 0, 0.03)), 2.6, g(28.0), 20, 'Z', rings=3.0)
    K.light_up(kb, 'R3K12', g(28.0), level=1.0, peak=2.6)

    cam, tgt = CAM.camera('Cam', tuple(a + Vector((-4.5, -5.5, 2.0))), tuple(a), lens=45, fstop=3.2)
    CAM.orbit(cam, (a.x, a.y, a.z), 7.0, 1.8, -40, -5, 1, g(26.6))
    CAM.move(cam, [(g(27.6), a + Vector((-2.5, -8.0, 7.0))), (g(28.2), hero + Vector((-1.0, -4.5, 7.0)))])
    CAM.follow_bake(tgt, rig.root, 1, g(27.6), offset=(0, 0, 0.6), smooth=6)
    CAM.whip(tgt, g(27.6), g(28.1), hero)
