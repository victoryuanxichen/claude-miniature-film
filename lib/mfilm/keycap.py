"""mfilm.keycap: clear resin keycaps with voxel worlds sealed inside, and the keyboard.

Anatomy of one key (all BU = cm):
  root Empty  'Key_R3K12'        props: u (width), biome, row; move it to press the key
   +- shell   'Key_R3K12_Shell'  rounded-rect loft, open bottom, dished top (frosted),
   |                             Bevel -> Solidify (0.06 wall); clear resin, IOR 1.5
   +- world   'Key_R3K12_World'  voxel heightfield (only exposed faces), fills 35-60 % of
   |                             the height; obj['glow'] (0..1) lights it from inside
   +- water   'Key_R3K12_Water'  optional transparent water block (also has 'glow')
   +- light   'Key_R3K12_Light'  point light inside, energy follows glow (spills onto
                                 neighbours and onto Clawd's feet)

Story hooks:
  light_up(keyboard, key_id, frame)  first visit: dark key wakes up when stepped on
  press(keyboard, key_id, frame)     key travel on landing
  set_all_glow(keyboard, value, f)   the end state: every world alight
"""
import math

import bpy
from mathutils import Vector

from . import materials as M
from .core import add_bevel, empty, key, link, mesh_obj, rng, shade_smooth
from .voxel import fbm, terrain

PITCH = 1.905          # 1u key pitch (cm)
BASE = 1.80            # 1u keycap base
TOP_INSET = 0.27       # each side, base -> top
GAP_Z = 0.35           # plate top -> keycap bottom

ROWS_75 = [
    [1] * 16,
    [1] * 13 + [2, 1],
    [1.5] + [1] * 12 + [1.5, 1],
    [1.75] + [1] * 11 + [2.25, 1],
    [2.25] + [1] * 10 + [1.75, 1, 1],
    [1.25, 1.25, 1.25, 6.25, 1, 1, 1, 1, 1, 1],
]
ROW_H = [1.10, 1.00, 0.95, 0.90, 0.95, 1.00]   # sculpted profile heights

# --------------------------------------------------------------------------- materials

_VOX = {
    'grass': 'grass', 'grass_dark': 'grass_dark', 'dirt': 'dirt', 'stone': 'stone', 'sand': 'sand',
    'snow': 'snow', 'ice': 'ice', 'rock': 'rock_dark', 'leaf': 'leaf', 'leaf_dark': '#1f4a22',
    'bark': 'bark', 'seabed': '#2b6c8f', 'city': '#16223a', 'mint': '#8fd6b4', 'mint_dark': '#5aa98a',
    'flower_w': 'daisy', 'flower_b': 'flower_blue', 'fruit': 'clawd', 'foam': 'foam', 'coral': '#f1efe6',
    'lava_rock': '#3a1210',
}
_mats = {}
HEIGHTS = {}           # kid -> column heights of its diorama (for placing things on the surface)


def vox_mats():
    """Shared voxel palette; every material reads obj['glow'] for the inner light-up."""
    try:
        ok = bool(_mats) and all(bpy.data.materials.get(m.name) == m for m in _mats.values())
    except ReferenceError:
        ok = False
    if not ok:
        _mats.clear()
        for k, c in _VOX.items():
            _mats[k] = M.matte('Vox_' + k, c, glow_attr='glow', glow_strength=2.5)
        _mats['city_light'] = M.emission('Vox_city_light', 'city_light', 6.0, glow_attr='glow')
        _mats['lava'] = M.principled('Vox_lava', 'lava', rough=0.6, emission='lava', emission_strength=12.0)
    return _mats


def shell_mats():
    return [M.resin('Resin'), M.resin('ResinFrost', frost=True)]


# --------------------------------------------------------------------------- shell geometry


def _rrect(w, d, r, z, seg=4):
    pts = []
    r = min(r, w / 2 - 1e-3, d / 2 - 1e-3)
    corners = [(w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90),
               (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)]
    for cx, cy, a0 in corners:
        for s in range(seg + 1):
            a = math.radians(a0 + 90 * s / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    return pts


def shell(name, u=1.0, h=1.0, dish=0.05, c=None):
    """Keycap shell for a key of width u (in units). Origin at the bottom centre."""
    w, d = BASE + (u - 1) * PITCH, BASE
    tw, td = w - 2 * TOP_INSET, d - 2 * TOP_INSET
    r0 = _rrect(w, d, 0.10, 0.0)
    r1 = _rrect(tw + 0.06, td + 0.06, 0.16, h * 0.93)
    r2 = _rrect(tw, td, 0.14, h)
    n = len(r0)
    verts = r0 + r1 + r2 + [(0.0, 0.0, h - dish)]
    faces, mi = [], []
    for ring in (0, 1):
        for i in range(n):
            a, b = ring * n + i, ring * n + (i + 1) % n
            faces.append((a, b, b + n, a + n))
            mi.append(0)
    ctr = 3 * n
    for i in range(n):
        a, b = 2 * n + i, 2 * n + (i + 1) % n
        faces.append((a, b, ctr))
        mi.append(1)
    o = mesh_obj(name, verts, faces, c, shell_mats(), mat_idx=mi)
    add_bevel(o, 0.04, 2, 25)
    so = o.modifiers.new('Wall', 'SOLIDIFY')
    so.thickness, so.offset = 0.06, -1.0
    so.use_even_offset = True
    shade_smooth(o)
    o.visible_shadow = False      # inner light must reach neighbours and Clawd's feet
    return o


def inner_footprint(u, h, fill):
    """Interior rectangle (w, d) available to the diorama at fill height."""
    w, d = BASE + (u - 1) * PITCH, BASE
    shrink = TOP_INSET * fill / 0.93 + 0.08
    return w - 2 * shrink, d - 2 * shrink


# --------------------------------------------------------------------------- biomes
# biome(nx, ny, H, r, **kw) -> dict(h=2D list, top=2D list, side=fn|None, water=level|None,
#                                   water_mat=str, light=hex, lit_fixed=float|None)


def _grid(nx, ny, fn):
    return [[fn(i, j) for j in range(ny)] for i in range(nx)]


def _sq_u(i, nx, ny):
    """Column -> square-layout u. Layout coords are a square map centred in wide keys."""
    return 0.5 + (i / nx - 0.5) * nx / ny


def _col_of(u, nx, ny):
    """Square-layout u -> column index."""
    return max(0, min(nx - 1, int((0.5 + (u - 0.5) * ny / nx) * nx)))


def b_meadow(nx, ny, H, r, layout=None, after=False, seed=0):
    """Hero key. layout = square-normalised positions {'pond': (u, v, radius), 'tree': (u, v), ...}
    (the square sits in the middle of a wide key; the meadow continues left and right)."""
    L = layout or {'pond': (0.40, 0.60, 0.10), 'tree': (0.617, 0.40), 'hill': (0.12, 0.85)}
    pu, pv, pr = L['pond']
    hu, hv = L.get('hill', (0.12, 0.85))

    def in_pond(i, j):
        return math.hypot(_sq_u(i, nx, ny) - pu, j / ny - pv) < pr

    def h(i, j):
        u, v = _sq_u(i, nx, ny), j / ny
        base = 3 + round(fbm(u * 3, v * 3, 1.0, 3, seed) * 1.2)
        hill = max(0.0, 1 - math.hypot((u - hu) * 1.6, v - hv) / 0.35) * 4
        if in_pond(i, j):
            return 2
        return int(base + hill)

    def top(i, j):
        if in_pond(i, j):
            return 'seabed'
        k = r.random()
        return 'flower_w' if k < 0.03 else 'flower_b' if k < 0.04 else 'grass'

    out = {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, top), 'water': 2.6, 'water_mat': 'water',
           'light': '#b8ffb0'}
    if after:   # the story left a fruit tree where the seed was planted
        tu, tv = L['tree']
        ti, tj = _col_of(tu, nx, ny), max(0, min(ny - 1, int(tv * ny)))
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if 0 <= ti + di < nx and 0 <= tj + dj < ny:
                    out['h'][ti + di][tj + dj] += 6 if (di, dj) == (0, 0) else 4
                    out['top'][ti + di][tj + dj] = 'leaf'
        out['tree_col'] = (ti, tj)
    return out


def b_waterfall(nx, ny, H, r, seed=0):
    def h(i, j):
        v = j / ny
        stream = abs(i - nx * 0.55 - fbm(0, v * 2, 1, 2, seed) * 2) < 1.2
        if v > 0.45:
            return int(H * 0.9) - (1 if stream else 0)
        return 2

    def top(i, j):
        v = j / ny
        stream = abs(i - nx * 0.55 - fbm(0, v * 2, 1, 2, seed) * 2) < 1.2
        if v > 0.45:
            return 'seabed' if stream else ('leaf' if r.random() < 0.08 else 'grass')
        return 'seabed'
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, top), 'water': 3.2, 'water_mat': 'water',
            'falls': True, 'light': '#a8e8ff'}


def b_lake(nx, ny, H, r, seed=0):
    def h(i, j):
        d = math.hypot(i / nx - 0.55, j / ny - 0.45)
        return 5 if d < 0.12 else 2 if d < 0.4 else 3

    def top(i, j):
        d = math.hypot(i / nx - 0.55, j / ny - 0.45)
        return 'leaf' if d < 0.06 else 'grass' if d < 0.12 else 'seabed' if d < 0.4 else 'grass'
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, top), 'water': 2.7, 'water_mat': 'water',
            'light': '#9fe0ff'}


def b_snow_crater(nx, ny, H, r, seed=0):
    holes = [(0.35, 0.55, 0.12), (0.66, 0.5, 0.1)]

    def inhole(i, j):
        return any(math.hypot(i / nx - a, j / ny - b) < rr for a, b, rr in holes)

    def h(i, j):
        return 1 if inhole(i, j) else 4 + round(fbm(i * 0.4, j * 0.4, 1, 2, seed))

    def top(i, j):
        return 'rock' if inhole(i, j) else 'snow'
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, top), 'side': lambda i, j, k, hh: 'snow',
            'light': '#ffffff'}


def b_night_city(nx, ny, H, r, seed=0):
    tall = _grid(nx, ny, lambda i, j: (2 + r.randint(0, int(H * 0.8))) if r.random() < 0.55 else 2)

    def top(i, j):
        return 'city_light' if tall[i][j] > 2 and r.random() < 0.7 else 'city'

    def side(i, j, k, hh):
        return 'city_light' if (k > 2 and r.random() < 0.18) else 'city'
    return {'h': tall, 'top': _grid(nx, ny, top), 'side': side, 'light': '#dfe8ff'}


def b_basalt(nx, ny, H, r, seed=0):
    def h(i, j):
        return 3 + int(abs(fbm(i * 0.25, j * 0.25, 1, 3, seed)) * H * 0.6)
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, lambda i, j: 'snow' if r.random() < 0.12 else 'rock'),
            'side': lambda i, j, k, hh: 'rock', 'light': '#c8d0ff'}


def b_lava(nx, ny, H, r, seed=0):
    def h(i, j):
        d = math.hypot(i / nx - 0.5, j / ny - 0.5)
        return 2 if d < 0.16 else 3 + int(d * 6)

    def top(i, j):
        d = math.hypot(i / nx - 0.5, j / ny - 0.5)
        return 'lava' if d < 0.16 else 'lava_rock'
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, top), 'side': lambda i, j, k, hh: 'lava_rock',
            'light': '#ff3a22', 'lit_fixed': 1.0}


def b_terraces(nx, ny, H, r, seed=0):
    def h(i, j):
        d = math.hypot((i / nx - 0.5) * nx / ny, j / ny - 0.5)
        return max(2, int((1 - d / 0.55) * H))

    def top(i, j):
        return 'mint' if h(i, j) % 2 == 0 else 'mint_dark'
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, top), 'side': lambda i, j, k, hh: 'mint_dark',
            'light': '#b8ffd8'}


def b_coral_sea(nx, ny, H, r, seed=0):
    def h(i, j):
        return 2 + (r.randint(1, 4) if r.random() < 0.15 else 0)

    def top(i, j):
        return 'coral' if r.random() < 0.15 else 'sand'
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, top), 'water': H * 0.95, 'water_mat': 'water',
            'bubbles': 24, 'light': '#7ff0ff'}


def b_deep_ocean(nx, ny, H, r, seed=0):
    return {'h': _grid(nx, ny, lambda i, j: 1), 'top': _grid(nx, ny, lambda i, j: 'seabed'),
            'water': H * 0.8, 'water_mat': 'water_deep', 'bubbles': 10, 'light': '#4f8cff'}


def b_forest_river(nx, ny, H, r, seed=0):
    def river(i, j):
        return abs(j / ny - 0.5 - 0.22 * math.sin(i / nx * 6.28 + seed)) < 0.08

    def h(i, j):
        if river(i, j):
            return 2
        return 3 + (r.randint(2, 5) if r.random() < 0.22 else 0)

    hh = _grid(nx, ny, h)

    def top(i, j):
        return 'seabed' if river(i, j) else ('leaf_dark' if hh[i][j] > 3 else 'grass')
    return {'h': hh, 'top': _grid(nx, ny, top), 'water': 2.6, 'water_mat': 'water',
            'side': lambda i, j, k, h_: 'leaf_dark' if h_ > 3 and k >= 3 else 'dirt', 'light': '#a8ffb8'}


def b_glacier(nx, ny, H, r, seed=0):
    return {'h': _grid(nx, ny, lambda i, j: 2 + (i // 3 + j // 4) % 5),
            'top': _grid(nx, ny, lambda i, j: 'ice' if r.random() < 0.8 else 'snow'),
            'side': lambda i, j, k, hh: 'ice', 'light': '#d8f4ff'}


def b_snow_forest(nx, ny, H, r, seed=0):
    def h(i, j):
        return 3 + (r.randint(2, 5) if r.random() < 0.18 else 0)
    hh = _grid(nx, ny, h)
    return {'h': hh, 'top': _grid(nx, ny, lambda i, j: 'snow'),
            'side': lambda i, j, k, h_: 'stone' if h_ > 3 and k >= 3 else 'snow', 'light': '#f0f6ff'}


def b_beach(nx, ny, H, r, seed=0):
    def h(i, j):
        return 2 if j / ny < 0.25 else 3
    return {'h': _grid(nx, ny, h),
            'top': _grid(nx, ny, lambda i, j: 'seabed' if j / ny < 0.25 else
                         ('grass' if r.random() < 0.12 else 'sand')),
            'water': 2.5, 'water_mat': 'water', 'light': '#fff3d0'}


def b_splash(nx, ny, H, r, seed=0):
    def h(i, j):
        return 1
    return {'h': _grid(nx, ny, h), 'top': _grid(nx, ny, lambda i, j: 'seabed'),
            'water': H * 0.7, 'water_mat': 'water', 'foam': 30, 'light': '#bff6ff'}


def b_river_panorama(nx, ny, H, r, seed=0):
    """Spacebar: a whole valley with a river along its length and snow-dusted trees."""
    def river(i, j):
        return abs(j / ny - 0.45 - 0.08 * math.sin(i / nx * 9 + seed)) < 0.14

    def h(i, j):
        if river(i, j):
            return 2
        return 3 + (r.randint(2, 4) if r.random() < 0.3 else 0)
    hh = _grid(nx, ny, h)

    def top(i, j):
        if river(i, j):
            return 'seabed'
        return 'snow' if hh[i][j] > 4 else ('leaf_dark' if hh[i][j] > 3 else 'grass')
    return {'h': hh, 'top': _grid(nx, ny, top), 'water': 2.6, 'water_mat': 'water',
            'side': lambda i, j, k, h_: 'leaf_dark' if h_ > 3 and k >= 3 else 'dirt', 'light': '#c8f0ff'}


BIOMES = {
    'meadow': b_meadow, 'waterfall': b_waterfall, 'lake': b_lake, 'snow_crater': b_snow_crater,
    'night_city': b_night_city, 'basalt': b_basalt, 'lava': b_lava, 'terraces': b_terraces,
    'coral_sea': b_coral_sea, 'deep_ocean': b_deep_ocean, 'forest_river': b_forest_river,
    'glacier': b_glacier, 'snow_forest': b_snow_forest, 'beach': b_beach, 'splash': b_splash,
    'river_panorama': b_river_panorama, 'empty': None,
}
COOL = {'lake', 'coral_sea', 'deep_ocean', 'glacier', 'night_city', 'splash', 'waterfall'}
WARM = {'meadow', 'terraces', 'beach', 'forest_river', 'snow_crater', 'snow_forest', 'basalt'}


# --------------------------------------------------------------------------- one key


def build_key(kid, biome, u=1.0, h=1.0, loc=(0, 0, 0), cell=0.085, fill=0.5, seed=0, c=None,
              glow=0.0, light=True, **kw):
    """One keycap with its world. Returns the root Empty."""
    root = empty('Key_' + kid, loc, c, 0.4)
    root['u'], root['biome'] = u, biome
    sh = shell(f'Key_{kid}_Shell', u, h, c=c)
    sh.parent = root
    fn = BIOMES.get(biome)
    if fn is None:
        return root
    iw, idp = inner_footprint(u, h, fill)
    nx, ny = max(4, int(iw / cell)), max(4, int(idp / cell))
    Hc = max(3, int(h * fill / cell))
    r = rng(hash((kid, seed)) & 0xFFFF)
    spec = fn(nx, ny, Hc, r, seed=seed, **kw)
    mats = vox_mats()
    used = {k for row in spec['top'] for k in row} | {'dirt', 'stone'}
    if spec.get('side'):
        for i in range(nx):
            for j in range(ny):
                for k in range(spec['h'][i][j]):
                    used.add(spec['side'](i, j, k, spec['h'][i][j]))
    sub = {k: mats[k] for k in mats if k in used}
    world, _ = terrain(f'Key_{kid}_World', nx, ny, cell,
                       lambda i, j: spec['h'][i][j], lambda i, j, hh: spec['top'][i][j], sub,
                       origin=(-nx * cell / 2, -ny * cell / 2, 0.02), side_fn=spec.get('side'), c=c)
    world.parent = root
    HEIGHTS[kid] = spec['h']
    root['cell'], root['nx'], root['ny'] = cell, nx, ny
    glow_objs = [world]
    if spec.get('water') is not None:
        wl = 0.02 + spec['water'] * cell
        wm = M.water('Water') if spec['water_mat'] == 'water' else M.water('WaterDeep', 'water_deep')
        from .core import box
        wtr = box(f'Key_{kid}_Water', (-nx * cell / 2, -ny * cell / 2, 0.03), (nx * cell / 2, ny * cell / 2, wl),
                  c, wm)
        wtr.parent = root
        wtr.visible_shadow = False
        glow_objs.append(wtr)
    lit_fixed = spec.get('lit_fixed')
    for o in glow_objs:
        o['glow'] = lit_fixed if lit_fixed is not None else glow
    root['glow_targets'] = ','.join(o.name for o in glow_objs)
    if light:
        from .lighting import light as mk_light
        lp = mk_light(f'Key_{kid}_Light', 'POINT', (0, 0, h * 0.35), energy=0.0,
                      color=spec.get('light', '#ffffff'), size=0.4, c=c)
        lp.parent = root
        lp.data.energy = 60.0 * (lit_fixed if lit_fixed is not None else glow)
        lp['max_energy'] = 60.0
        root['light'] = lp.name
    root['fixed'] = lit_fixed is not None
    return root


# --------------------------------------------------------------------------- keyboard


def assign_biomes(rows, seed=7, hero=(3, 12), red=((4, 1), (5, 2)), space='river_panorama',
                  empty_ratio=0.22, overrides=None):
    """Deterministic biome map {(row, k): biome}: no two horizontal neighbours from the same
    temperature family when avoidable, one hero meadow, fixed red keys, spacebar panorama."""
    r = rng(seed)
    pool = [b for b in BIOMES if b not in ('meadow', 'lava', 'river_panorama', 'empty')]
    out = {}
    for ri, row in enumerate(rows):
        prev = None
        for k, u in enumerate(row):
            if (ri, k) == tuple(hero):
                b = 'meadow'
            elif (ri, k) in [tuple(x) for x in red]:
                b = 'lava'
            elif u >= 6:
                b = space
            elif r.random() < empty_ratio:
                b = 'empty'
            else:
                for _ in range(8):
                    b = r.choice(pool)
                    fam = 'c' if b in COOL else 'w'
                    if prev is None or fam != prev:
                        break
            out[(ri, k)] = b
            prev = 'c' if b in COOL else 'w' if b in WARM else prev
    for kk, b in (overrides or {}).items():
        out[tuple(kk)] = b
    return out


class Keyboard:
    def __init__(self):
        self.keys = {}      # kid -> root
        self.plate = None
        self.case = None

    def kid(self, row, k):
        return f'R{row}K{k}'

    def root(self, kid):
        return self.keys[kid]

    def top(self, kid):
        """World position of the centre of a keycap's top surface (where Clawd stands)."""
        ro = self.keys[kid]
        bpy.context.view_layer.update()
        h = ROW_H[int(kid[1])]
        return ro.matrix_world @ Vector((0, 0, h - 0.04))


def build_keyboard(origin=(0, 0, 0), rows=ROWS_75, seed=7, glow=0.0, cell=0.085, biomes=None,
                   hero=(3, 12), lights=True, c=None, only=None, meadow_kw=None):
    """Whole board. glow = initial glow for every world (0 = asleep, 1 = awake).
    only = set of key ids to build (others get empty shells) to save time in close-ups."""
    kb = Keyboard()
    bm = biomes or assign_biomes(rows, seed, hero)
    ox, oy, oz = origin
    total_w = max(sum(r_) for r_ in rows) * PITCH
    for ri, row in enumerate(rows):
        x = ox - total_w / 2
        y = oy + (len(rows) / 2 - ri - 0.5) * PITCH
        for k, u in enumerate(row):
            kid = kb.kid(ri, k)
            cx = x + u * PITCH / 2
            b = bm[(ri, k)]
            if only is not None and kid not in only:
                b = 'empty'
            kw = dict(meadow_kw or {}) if b == 'meadow' else {}
            kb.keys[kid] = build_key(kid, b, u, ROW_H[ri], (cx, y, oz + GAP_Z), cell, seed=seed + ri * 31 + k,
                                     c=c, glow=glow, light=lights and b != 'empty', **kw)
            x += u * PITCH
    depth = len(rows) * PITCH
    kb.plate = plate_map((ox, oy, oz), total_w, depth, c=c)
    from .core import box
    kb.case = box('KB_Case', (ox - total_w / 2 - 0.9, oy - depth / 2 - 0.9, oz - 1.6),
                  (ox + total_w / 2 + 0.9, oy + depth / 2 + 0.9, oz - 0.05), c,
                  M.metal('Anodized', 'case', 0.38), bevel=0.35, segs=4)
    return kb


def plate_map(center, w, d, cell=0.25, seed=11, c=None):
    """The continuous dim landscape under the keys (seen through gaps and clear keycaps)."""
    mats = vox_mats()
    nx, ny = int(w / cell), int(d / cell)

    def h(i, j):
        return 1 + int(max(0.0, fbm(i * 0.08, j * 0.08, 1, 3, seed)) * 3)

    def top(i, j, hh):
        v = fbm(i * 0.1 + 5, j * 0.1, 1, 2, seed)
        return 'seabed' if v < -0.25 else 'leaf_dark' if v > 0.3 else 'grass_dark'
    sub = {k: mats[k] for k in ('seabed', 'leaf_dark', 'grass_dark', 'dirt', 'stone')}
    o, _ = terrain('KB_PlateMap', nx, ny, cell, h, top, sub,
                   origin=(center[0] - w / 2, center[1] - d / 2, center[2] - 0.9), c=c)
    o['glow'] = 0.12
    return o


# --------------------------------------------------------------------------- story hooks


def _glow_targets(root):
    return [bpy.data.objects[n] for n in root.get('glow_targets', '').split(',') if n]


def light_up(kb, kid, f, level=1.0, peak=1.8, rise=3, settle=10):
    """A sleeping key wakes up (Clawd landed on it): flash to `peak`, settle to `level`."""
    ro = kb.root(kid)
    if ro.get('fixed'):
        return
    for o in _glow_targets(ro):
        key(o, '["glow"]', f - 1, o.get('glow', 0.0))
        key(o, '["glow"]', f + rise, peak, 'expo_out')
        key(o, '["glow"]', f + rise + settle, level)
    ln = ro.get('light')
    if ln:
        lp = bpy.data.objects[ln]
        mx = lp.get('max_energy', 60.0)
        key(lp.data, 'energy', f - 1, lp.data.energy)
        key(lp.data, 'energy', f + rise, mx * peak, 'expo_out')
        key(lp.data, 'energy', f + rise + settle, mx * level)


def diorama_point(kb, kid, u, v):
    """World position on the surface of a key's diorama at square-layout (u, v)."""
    ro = kb.root(kid)
    cell, nx, ny = ro['cell'], ro['nx'], ro['ny']
    i, j = _col_of(u, nx, ny), max(0, min(ny - 1, int(v * ny)))
    h = HEIGHTS[kid][i][j]
    bpy.context.view_layer.update()
    local = Vector(((i + 0.5) * cell - nx * cell / 2, (j + 0.5) * cell - ny * cell / 2, 0.02 + h * cell))
    return ro.matrix_world @ local


def set_key_glow(kb, kid, value, f=None):
    ro = kb.root(kid)
    if ro.get('fixed'):
        return
    for o in _glow_targets(ro):
        if f is None:
            o['glow'] = value
        else:
            key(o, '["glow"]', f, value)
    ln = ro.get('light')
    if ln:
        lp = bpy.data.objects[ln]
        e = lp.get('max_energy', 60.0) * value
        if f is None:
            lp.data.energy = e
        else:
            key(lp.data, 'energy', f, e)


def set_all_glow(kb, value, f=None):
    for kid, ro in kb.keys.items():
        if ro.get('fixed'):
            continue
        for o in _glow_targets(ro):
            if f is None:
                o['glow'] = value
            else:
                key(o, '["glow"]', f, value)
        ln = ro.get('light')
        if ln:
            lp = bpy.data.objects[ln]
            if f is None:
                lp.data.energy = lp.get('max_energy', 60.0) * value
            else:
                key(lp.data, 'energy', f, lp.get('max_energy', 60.0) * value)


def wave_on(kb, f0, f1, origin_kid, level=1.0):
    """End-of-film reveal: keys light up in a ripple spreading from origin_kid."""
    o = kb.root(origin_kid).location
    dist = {k: (r.location - o).length for k, r in kb.keys.items()}
    mx = max(dist.values()) or 1.0
    for kid, dd in dist.items():
        light_up(kb, kid, int(f0 + (f1 - f0) * dd / mx), level, peak=1.4)


def press(kb, kid, f, depth=0.12):
    ro = kb.root(kid)
    z = ro.location.z
    key(ro, 'location', f - 1, z, index=2)
    key(ro, 'location', f + 2, z - depth, 'ease', index=2)
    key(ro, 'location', f + 9, z, 'back', index=2)
