"""S17 51.9-59.0 s  It was a keycap all along: one continuous pull-out back to the terminal.

Starts looking straight down through the frosted top of the hero key at the voxel version of
the meadow - same layout as the plan view at the end of S16, now with a fruit tree, a tiny
Clawd and a tiny giant (what happened inside stays inside). The camera rises: the key's walls
come into frame, neighbouring worlds wake up in a ripple spreading from the hero key (the
whole board ends up alight, unlike the sleeping board of S05-S08), Clawd pops out of the key
in a flash (53.3 s), lands, hops toward camera, and looks up at the monitor where the 2D
pixel Clawd sits next to the prompt. The cursor next to it starts blinking on the beat
again. Clawd hops, turns to camera, blinks. Cut to black on the beat at 59.0 s.
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import fx as FX
from mfilm import keycap as K
from mfilm import lighting as L
from mfilm import materials as M

from . import common as S


def build(ctx):
    g = ctx.g
    k = S.keyboard_set(ctx, after=True)
    kb = k['kb']
    L.rig_keyboard(ctx.sc)
    hid = ctx.state.get('hero_key', 'R3K12')
    hero = kb.top(hid)
    K.wave_on(kb, g(52.6), g(53.6), hid)

    tiny = core.coll('Tiny')
    lay = ctx.layout
    for name, uv, px in (('TinyClawd', lay['clawd_land'], 0.012), ('TinyGiant', lay['giant'], 0.035)):
        o = C.static_mesh(name, px=px, c=tiny)
        o.location = K.diorama_point(kb, hid, uv[0], uv[1])
        o.parent = None
    fruit_m = M.matte('TinyFruit', 'clawd', 0.6)
    tp = K.diorama_point(kb, hid, lay['tree'][0], lay['tree'][1])
    r = core.rng(17)
    for i in range(7):
        p = tp + Vector((r.uniform(-0.12, 0.12), r.uniform(-0.12, 0.12), r.uniform(0.0, 0.25)))
        core.box(f'TinyFruit{i}', p - Vector((0.018,) * 3), p + Vector((0.018,) * 3), tiny, fruit_m)

    # screen: the 2D Clawd beside the prompt; its cursor blinks on the beat from 57.5 s
    mon = k['monitor']
    sy = mon['center'].y - 0.06
    sprite = E.screen_sprite('ScreenClawd', (hero.x - 6.0, sy, 8.0), pixel=0.45,
                             cursor_blink=(ctx.beat, int(57.5 * 2), int(60.0 * 2)))
    core.key_visible(sprite['cursor'], 1, False)
    core.key(sprite['root'], 'location', g(56.6), sprite['root'].location.copy())
    core.key(sprite['root'], 'location', g(56.8), sprite['root'].location + Vector((0, 0, 0.35)), 'quad_in')
    core.key(sprite['root'], 'location', g(57.0), sprite['root'].location.copy(), 'bounce')

    # Clawd pops out of the hero key and comes forward
    near = kb.top('R4K12')
    inside = hero - Vector((0, 0, 0.9))
    rig = S.clawd(inside, yaw=0)
    C.show(rig, 1, False)
    C.show(rig, g(53.3), True)
    C.place(rig, g(53.3), inside, ease='expo_out')
    C.place(rig, g(53.6), hero + Vector((0, 0, 2.0)), ease='quad_in')
    C.place(rig, g(53.95), hero)
    core.key(rig.root, 'scale', g(53.3), Vector((0.3, 0.3, 0.3)), 'back')
    core.key(rig.root, 'scale', g(53.6), Vector((1, 1, 1)))
    C.squash(rig, g(53.95), 0.22)
    C.squash(rig, g(53.95) + 8, 0.0, 'back')
    FX.burst('PopOut', hero + Vector((0, 0, 0.05)), g(53.3), n=26, speed=8.0, energy=300.0)
    K.light_up(kb, hid, g(53.3), peak=2.8)
    C.hop(rig, g(55.4), g(55.9), near, height=1.2, yaw_deg=0)
    K.press(kb, 'R4K12', g(55.9))
    C.tilt(rig, g(56.2), pitch_deg=-18)
    C.tilt(rig, g(56.95), pitch_deg=-18)
    C.hop(rig, g(57.0), g(57.4), near, height=0.6, squash_amt=0.15)
    C.turn(rig, g(57.4), g(57.8), 0)
    C.blink(rig, g(58.3))
    C.idle(rig, g(58.0), ctx.last)

    # one continuous camera move: plan view -> rise -> wide board -> low hero framing
    look_end = Vector((near.x, 8.0, 4.2))
    cam, tgt = CAM.camera('Cam', tuple(hero + Vector((0, -0.05, 2.6))), tuple(hero - Vector((0, 0, 0.6))), lens=24,
                          fstop=5.6)
    CAM.move(cam, [(1, hero + Vector((0, -0.05, 2.4))), (g(52.6), hero + Vector((-0.5, -1.5, 6.0))),
                   (g(53.3), hero + Vector((-2.5, -6.0, 6.5))), (g(54.6), hero + Vector((-6.0, -15.0, 9.0))),
                   (g(56.0), Vector((hero.x - 1.5, -16.0, 2.0))), (ctx.last, Vector((hero.x - 1.2, -14.5, 2.0)))])
    CAM.move(tgt, [(1, hero - Vector((0, 0, 0.6))), (g(53.3), hero + Vector((0, 0, 1.0))),
                   (g(54.6), Vector((0, 0, 1.5))), (g(56.0), look_end), (ctx.last, look_end)])
    CAM.lens_keys(cam, [(1, 24), (g(56.0), 35)])
    CAM.fstop_keys(cam, [(1, 5.6), (g(56.0), 4.0)])
