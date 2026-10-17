"""Shared sets for the benchmark film. Every shot module calls one of these, so the same
world is rebuilt identically (same seeds, same layout) in every shot: continuity is data."""
import math

from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import keycap as K
from mfilm import lighting as L
from mfilm import materials as M
from mfilm import swarm as SW

KB_SEED = 7
HERO = (3, 12)                       # Enter key = the meadow world
BIOME_OVERRIDES = {                  # the keys on Clawd's route get their story biomes
    (1, 11): 'splash', (2, 12): 'waterfall', (5, 3): 'river_panorama',
    (4, 4): 'lake', (3, 5): 'forest_river', (2, 6): 'snow_crater', (1, 7): 'night_city',
    (0, 8): 'basalt', (0, 9): 'glacier', (2, 11): 'coral_sea',
}
MONITOR = dict(screen_center=(0, 24, 21), screen_size=(56, 32))
MEADOW_SIZE = 120.0
MINI_CELL = 0.48
PILE_OFFSET = (5.0, 1.0, 0.0)        # the sea of minis, relative to the tree base (S14, S15)
PILE_R = 6.0
CLAWD_UNDER_TREE = (-2.0, -8.0, 0.0)  # where Clawd watches from in S14-S16


def biomes():
    return K.assign_biomes(K.ROWS_75, KB_SEED, HERO, overrides=BIOME_OVERRIDES)


def keyboard_set(ctx, awake=False, after=False, only=None, lights=True, monitor=True, cell=0.085):
    """Keyboard (+ monitor behind it) in the state it has at this shot's start."""
    c = core.coll('Keyboard')
    kb = K.build_keyboard((0, 0, 0), seed=KB_SEED, glow=1.0 if awake else 0.0, biomes=biomes(), cell=cell,
                          lights=lights, only=only, c=c,
                          meadow_kw={'layout': ctx.layout or None, 'after': after})
    if not awake:
        for kid in ctx.lit_keys(ctx.start):
            if kid in kb.keys:
                K.set_key_glow(kb, kid, 1.0)
    desk = core.box('Desk', (-90, -45, -3.2), (90, 60, -1.6), c, M.principled('DeskWood', '#15181c', rough=0.42))
    out = {'kb': kb, 'desk': desk}
    if monitor:
        out['monitor'] = E.monitor(core.coll('Monitor'), desk_z=-1.6, **MONITOR)
    return out


def wake(ctx, kb):
    """Key wake-ups (lit_trail) that fall inside this shot."""
    for kid, f in ctx.lit_events():
        if kid in kb.keys:
            K.light_up(kb, kid, f)
            K.press(kb, kid, f)


def terminal_set(ctx, cursor=True):
    t = E.terminal_space(core.coll('Terminal'), with_cursor=cursor, prompt=(-2.1, 0.0, 0.7))
    if cursor:
        t['cursor'].location = (-1.0, 0.0, 0.02)
    rig = L.rig_terminal(ctx.sc, (0, 0, 0.6))
    return t, rig


def far_cursor(loc=(9.0, 1.8, 0.0)):
    """The second orange cursor standing in the distance (motif plant)."""
    return E.cursor('FarCursor', loc)


def meadow_set(ctx, grass_density=16.0, dense_center=None, dense_r=30.0, radius=140.0):
    c = core.coll('Meadow')
    m = E.meadow(c, (0, 0, 0), radius, MEADOW_SIZE, dense_center=dense_center, dense_r=dense_r,
                 grass_density=grass_density, layout=ctx.layout or None)
    L.rig_meadow(ctx.sc, 38.0, 135.0)
    return m


def on_ground(p):
    """Snap a world XY onto the meadow ground."""
    return Vector((p[0], p[1], E.ground_height(p[0], p[1])))


def clawd(loc, yaw=0.0, name='Clawd'):
    return C.build(name, tuple(loc), facing_deg=yaw, c=core.coll('Cast'))


def mini_source():
    return SW.mini('Mini', MINI_CELL)


def yaw_to(a, b):
    """Facing (deg) for something at a looking at b."""
    return math.degrees(C.heading(b[0] - a[0], b[1] - a[1]))
