"""mfilm.env: the three worlds.

  terminal_space()  inside the screen: dark gloss floor, metal rails, code rows as glowing
                    capsules, the '>' prompt and the orange cursor
  room()            establishing shot: desk, monitor showing code, keyboard, night window
  meadow()          inside the hero keycap: real-scale grass, daisies, dew, pond, far trees,
                    clouds; layout shared with the keycap diorama (see layout_to_world)
"""
import math

import bpy
from mathutils import Vector

from . import materials as M
from .core import box, coll, empty, key, key_visible, link, mesh_obj, rng, shade_smooth
from .gn import add_modifier, scatter_group

# --------------------------------------------------------------------------- code text as geometry


def code_rows(name, origin, width, rows=12, row_gap=0.5, height=0.16, seed=1, c=None, plane='XZ',
              strength=1.2, accent_ratio=0.06, indent_max=4, unit=0.18):
    """Rows of rounded capsules standing in for code: random token lengths, indentation,
    occasional blank lines and a few green accent tokens. Never real text (keeps it abstract and
    readable as 'code' at any distance). plane 'XZ' = vertical wall facing -Y, 'XY' = floor."""
    r = rng(seed)
    grey = M.emission('Code', 'code', strength)
    green = M.emission('CodeAccent', '#8fd19e', strength)
    ox, oy, oz = origin
    objs = []
    for i in range(rows):
        if r.random() < 0.12:
            continue
        x = ox + unit * r.randint(0, indent_max) * 2
        row_end = ox + width * r.uniform(0.35, 1.0)
        while x < row_end:
            L = unit * r.choice([1, 2, 2, 3, 4, 6, 8])
            m = green if r.random() < accent_ratio else grey
            if plane == 'XZ':
                z = oz - i * row_gap
                lo, hi = (x, oy, z), (x + L, oy + 0.04, z + height)
            else:
                y = oy - i * row_gap
                lo, hi = (x, y, oz), (x + L, y + height, oz + 0.04)
            objs.append(box(f'{name}_{i}_{len(objs)}', lo, hi, c, m, bevel=height * 0.45, segs=3))
            x += L + unit * r.choice([0.6, 1, 1])
    return objs


def chevron(name, loc, size=0.6, thick=0.12, c=None, mat=None):
    """The '>' prompt: two bevelled bars meeting at a point, facing -Y."""
    mat = mat or M.emission('Chevron', 'chevron', 1.6)
    root = empty(name, loc, c, size)
    for s, ang in ((1, -40), (-1, 40)):
        b = box(f'{name}_{s}', (-size / 2, -thick / 2, -thick / 2), (size / 2, thick / 2, thick / 2), c, mat,
                bevel=thick * 0.45, segs=3, par=root)
        b.location = (0, 0, s * size * 0.32)
        b.rotation_euler.y = math.radians(ang)
    return root


def cursor(name='Cursor', loc=(0, 0, 0), w=0.34, h=1.05, d=0.16, c=None):
    """The orange terminal cursor: a clay bar with a soft glow (obj['glow'] 0..1)."""
    mat = M.clay('Clay_Cursor', 'cursor', glow_attr='glow')
    o = box(name, (-w / 2, -d / 2, 0), (w / 2, d / 2, h), c, mat, bevel=0.05, segs=3)
    o.location = loc
    o['glow'] = 0.6
    return o


def blink(obj, beat_fn, beat_from, beat_to, on_beats=1, off_beats=1):
    """Cursor blink locked to the beat grid (benchmark: on/off every 0.5 s at 120 BPM).
    beat_fn(n) -> frame of beat n (pass ctx.beat)."""
    b = beat_from
    while b < beat_to:
        key_visible(obj, beat_fn(b), True)
        key_visible(obj, beat_fn(b + on_beats), False)
        b += on_beats + off_beats
    key_visible(obj, beat_fn(beat_to), True)


def terminal_space(c=None, length=160.0, seed=2, prompt=(-4.0, 0.0, 1.6), with_cursor=True):
    """The inside of the terminal line. Clawd walks along +X on the floor at z=0, facing -Y
    (toward camera). Returns dict of handles."""
    c = c or coll('Terminal')
    floor = box('TermFloor', (-length / 2, -6, -0.4), (length / 2, 3.2, 0.0), c, M.dark_gloss())
    back = box('TermWall', (-length / 2, 3.2, -0.4), (length / 2, 3.6, 30), c, M.dark_gloss('WallDark', 'void_hi', 0.6))
    rail_m = M.metal('Rail', 'rail', 0.25)
    rails = [box('RailFront', (-length / 2, -2.6, 0.0), (length / 2, -2.45, 0.08), c, rail_m, 0.03),
             box('RailBack', (-length / 2, 3.0, 2.1), (length / 2, 3.15, 2.2), c, rail_m, 0.03),
             box('RailHigh', (-length / 2, 3.0, 6.0), (length / 2, 3.15, 6.08), c, rail_m, 0.03)]
    code = code_rows('CodeWall', (-length / 2 + 2, 3.15, 13.0), length - 4, rows=14, row_gap=0.55, seed=seed, c=c)
    code += code_rows('CodeFar', (-length / 2, 18.0, 22.0), length, rows=20, row_gap=0.9, height=0.3,
                      seed=seed + 1, c=c, strength=0.6, unit=0.4)
    out = {'floor': floor, 'wall': back, 'rails': rails, 'code': code,
           'prompt': chevron('Prompt', prompt, c=c)}
    if with_cursor:
        out['cursor'] = cursor('Cursor', (prompt[0] + 0.9, prompt[1], prompt[2] - 0.55), c=c)
    return out


# --------------------------------------------------------------------------- room


def pine(name, base, h, c, mat):
    """Night pine silhouette: stacked bevelled boxes narrowing upward."""
    root = empty(name, base, c, 1)
    for k in range(6):
        w = h * 0.28 * (1 - k / 7)
        box(f'{name}_{k}', (-w / 2, -w / 2, k * h / 7), (w / 2, w / 2, (k + 1.4) * h / 7), c, mat, par=root)
    return root


def monitor(c=None, screen_center=(0, 30, 26), screen_size=(56, 32), seed=4, rows=26, desk_z=0.0):
    """Monitor on the desk; the screen shows code rows (same capsule language as terminal_space).
    Returns dict with 'screen' (emissive plane, front face at y = sy - 0.05) and 'origin'."""
    c = c or coll('Monitor')
    sx, sy, sz = screen_center
    w, h = screen_size
    bez = M.principled('Bezel', '#0b0d10', rough=0.35)
    box('MonitorBezel', (sx - w / 2 - 1, sy, sz - h / 2 - 1), (sx + w / 2 + 1, sy + 2.5, sz + h / 2 + 1), c, bez, 0.4)
    box('MonitorStand', (sx - 3, sy + 2, desk_z), (sx + 3, sy + 4, sz - h / 2), c, bez, 0.3)
    box('MonitorFoot', (sx - 12, sy - 6, desk_z), (sx + 12, sy + 8, desk_z + 0.8), c, bez, 0.3)
    screen = box('Screen', (sx - w / 2, sy - 0.05, sz - h / 2), (sx + w / 2, sy, sz + h / 2), c,
                 M.emission('ScreenBase', '#0a0f16', 1.0))
    code_rows('ScreenCode', (sx - w / 2 + 2, sy - 0.08, sz + h / 2 - 2.5), w * 0.8, rows=rows, row_gap=1.0,
              height=0.35, seed=seed, c=c, unit=0.45, strength=2.0)
    return {'screen': screen, 'center': Vector(screen_center), 'size': screen_size}


def screen_sprite(name, loc, pixel=0.35, c=None, strength=4.0, with_prompt=True, cursor_blink=None):
    """The 2D pixel Clawd shown on the monitor (emissive pixels, facing -Y), with the '>'
    prompt on its left and a cursor bar on its right. loc = bottom-centre on the screen surface.
    cursor_blink=(ctx.beat, beat_from, beat_to) makes the cursor blink on the beat."""
    from .voxel import SPRITE
    root = empty(name, loc, c, pixel * 4)
    mat = M.emission(name + '_Mat', 'clawd', strength)
    rows = len(SPRITE)
    for r_, line in enumerate(SPRITE):
        for k, ch in enumerate(line):
            if ch == '#':
                x = (k - 6.5) * pixel
                z = (rows - 1 - r_) * pixel
                box(f'{name}_{r_}_{k}', (x, -0.02, z), (x + pixel, 0.0, z + pixel), c, mat, par=root)
    out = {'root': root}
    if with_prompt:
        ch = chevron(name + '_Prompt', (0, 0, 0), size=pixel * 2.2, thick=pixel * 0.45, c=c)
        ch.parent = root
        ch.location = (-9.5 * pixel, -0.03, 4 * pixel)
        cur = box(name + '_Cursor', (8 * pixel, -0.02, pixel), (9 * pixel, 0.0, 6 * pixel), c, mat, par=root)
        out['cursor'] = cur
        if cursor_blink:
            blink(cur, *cursor_blink)
    return out


def room(c=None, seed=4, screen_center=(0, 30, 26), screen_size=(56, 32), keyboard=True):
    """Desk + monitor + (sleeping) keyboard + window with pines. The monitor's code rows are
    the same capsule language as terminal_space, so the scale reveal reads instantly."""
    c = c or coll('Room')
    desk = box('Desk', (-120, -60, -3), (120, 60, 0), c, M.principled('DeskWood', '#15181c', rough=0.45))
    mon = monitor(c, screen_center, screen_size, seed)
    screen = mon['screen']
    win_m = M.emission('NightSky', '#0e1a33', 0.6)
    box('Window', (-150, 140, 5), (150, 141, 160), c, win_m)
    tree_m = M.principled('PineSil', '#05070b', rough=1.0)
    r = rng(seed)
    for i in range(14):
        pine(f'Pine{i}', (-140 + i * 21 + r.uniform(-6, 6), 135, 0), r.uniform(70, 130), c, tree_m)
    out = {'desk': desk, 'screen': screen}
    if keyboard:
        from .keycap import build_keyboard
        out['keyboard'] = build_keyboard((0, -22, 0), glow=0.0, cell=0.17, lights=False, c=c)
    return out


# --------------------------------------------------------------------------- meadow

HERO_LAYOUT = {           # normalised keycap coordinates (u right, v back), shared by both scales
    'pond': (0.40, 0.60, 0.10), 'tree': (0.617, 0.40), 'seed': (0.617, 0.40), 'hill': (0.12, 0.85),
    'clawd_land': (0.6, 0.35), 'giant': (0.70, 0.45),
}


def layout_to_world(uv, size=120.0, center=(0, 0, 0)):
    """Keycap-normalised (u, v) -> meadow world XY (meadow spans `size` BU across)."""
    return Vector((center[0] + (uv[0] - 0.5) * size, center[1] + (uv[1] - 0.5) * size, center[2]))


def _blade(name, h, w, bend, seed, dew_mat, c):
    """One curved, tapered, slightly twisted grass blade with 0-2 dew drops."""
    r = rng(seed)
    seg = 7
    verts, faces = [], []
    for s in range(seg + 1):
        t = s / seg
        y = bend * t * t * h
        z = t * h
        hw = w * (1 - t) ** 0.8 / 2 + 0.003
        tw = (t - 0.5) * 0.6
        verts += [(-hw * math.cos(tw), y - hw * math.sin(tw), z), (hw * math.cos(tw), y + hw * math.sin(tw), z)]
    for s in range(seg):
        a = s * 2
        faces.append((a, a + 1, a + 3, a + 2))
    o = mesh_obj(name, verts, faces, c, [M.grass_blade()])
    me = o.data
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = ((vi % 2), (vi // 2) / seg)
    shade_smooth(o)
    parts = [o]
    for d in range(r.choice([0, 0, 1, 2])):
        t = r.uniform(0.3, 0.8)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025 + r.random() * 0.02, segments=10, ring_count=6,
                                             location=(0, bend * t * t * h - 0.02, t * h))
        drop = bpy.context.active_object
        drop.name = f'{name}_dew{d}'
        drop.data.materials.append(dew_mat)
        for cl in list(drop.users_collection):
            cl.objects.unlink(drop)
        c.objects.link(drop)
        parts.append(drop)
    if len(parts) > 1:
        from .core import join_meshes
        j = join_meshes(name + '_J', parts, c)
        for p in parts:
            bpy.data.objects.remove(p, do_unlink=True)
        j.name = name
        return j
    return o


def _daisy(name, stem_h, seed, c):
    r = rng(seed)
    white, yellow = M.matte('Petal', 'daisy', 0.5), M.matte('DaisyEye', 'daisy_eye', 0.5)
    stem = box(name + '_stem', (-0.025, -0.025, 0), (0.025, 0.025, stem_h), c, M.grass_blade())
    parts = [stem]
    n = 16
    for i in range(n):
        a = 2 * math.pi * i / n + r.uniform(-0.05, 0.05)
        p = box(f'{name}_p{i}', (0.08, -0.035, -0.01), (0.42, 0.035, 0.01), c, white, 0.008, 1)
        p.rotation_euler = (math.radians(r.uniform(-12, 4)), 0, a)
        p.location = (0, 0, stem_h)
        parts.append(p)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=12, ring_count=6, location=(0, 0, stem_h + 0.02))
    eye = bpy.context.active_object
    eye.scale.z = 0.5
    eye.data.materials.append(yellow)
    for cl in list(eye.users_collection):
        cl.objects.unlink(eye)
    c.objects.link(eye)
    parts.append(eye)
    from .core import join_meshes
    j = join_meshes(name + '_J', parts, c)
    for p in parts:
        bpy.data.objects.remove(p, do_unlink=True)
    j.name = name
    tilt = r.uniform(-0.3, 0.3)
    j.rotation_euler = (tilt, r.uniform(-0.2, 0.2), 0)
    return j


def plant_sets(seed=9):
    """Hidden collections used as scatter sources: GrassSet (blades) and FlowerSet."""
    root = coll('_PlantSources')
    root.hide_render = True
    gs, fs = coll('GrassSet', root), coll('FlowerSet', root)
    dew = M.glass('Dew', 0.0, 1.33)
    r = rng(seed)
    for i in range(10):
        _blade(f'Blade{i}', r.uniform(2.2, 6.5), r.uniform(0.09, 0.16), r.uniform(0.05, 0.3), seed + i, dew, gs)
    for i in range(4):
        _daisy(f'Daisy{i}', r.uniform(4.5, 8.0), seed + 50 + i, fs)
    blue = M.matte('BlueFlower', 'flower_blue', 0.5)
    for i in range(3):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.08, subdivisions=1, location=(0, 0, r.uniform(0.6, 1.4)))
        b = bpy.context.active_object
        b.name = f'Blue{i}'
        b.data.materials.append(blue)
        for cl in list(b.users_collection):
            cl.objects.unlink(b)
        fs.objects.link(b)
    return gs, fs


def ground_height(x, y, center=(0, 0, 0), seed=3):
    """Height of the meadow ground at (x, y) - use it to plant feet, seeds and trunks."""
    from .voxel import fbm
    return center[2] + fbm(x * 0.01, y * 0.01, 1, 3, seed) * 2.0


def ground(name, center, radius, res=1.5, dense_center=None, dense_r=40.0, holes=(), seed=3, c=None):
    """Gently rolling ground disc with a 'density' point attribute: 1 near dense_center,
    fading to 0.12 at the rim, 0 inside holes [(x, y, r), ...] (pond)."""
    from .voxel import fbm
    cx, cy, cz = center
    n = int(2 * radius / res)
    verts, faces, dens = [], [], []
    idx = {}
    dc = Vector(dense_center or center)
    for i in range(n + 1):
        for j in range(n + 1):
            x, y = cx - radius + i * res, cy - radius + j * res
            if math.hypot(x - cx, y - cy) > radius + res:
                continue
            z = ground_height(x, y, center, seed)
            idx[(i, j)] = len(verts)
            verts.append((x, y, z))
            d = math.hypot(x - dc.x, y - dc.y)
            v = max(0.12, 1 - max(0.0, d - dense_r) / (radius * 0.6))
            for hx, hy, hr in holes:
                if math.hypot(x - hx, y - hy) < hr:
                    v = 0.0
            dens.append(v)
    for i in range(n):
        for j in range(n):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k in idx for k in q):
                faces.append(tuple(idx[k] for k in q))
    o = mesh_obj(name, verts, faces, c, [M.principled('Soil', '#2c4a1b', rough=0.95)])
    a = o.data.attributes.new('density', 'FLOAT', 'POINT')
    a.data.foreach_set('value', dens)
    return o


def far_trees(center, r0=260.0, r1=420.0, count=40, seed=6, c=None):
    """Soft rounded tree silhouettes on the horizon (hazed by world_haze)."""
    r = rng(seed)
    mat = M.matte('FarTree', '#3f6a3a', 0.9)
    out = []
    for i in range(count):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(r0, r1)
        x, y = center[0] + math.cos(a) * d, center[1] + math.sin(a) * d
        hgt = r.uniform(25, 45)
        for k in range(3):
            bpy.ops.mesh.primitive_ico_sphere_add(radius=hgt * r.uniform(0.3, 0.45), subdivisions=2,
                                                  location=(x + r.uniform(-8, 8), y + r.uniform(-8, 8),
                                                            hgt * r.uniform(0.6, 0.9)))
            b = bpy.context.active_object
            b.name = f'FarTree{i}_{k}'
            b.data.materials.append(mat)
            for cl in list(b.users_collection):
                cl.objects.unlink(b)
            (c or bpy.context.scene.collection).objects.link(b)
            shade_smooth(b)
            out.append(b)
    return out


def meadow(c=None, center=(0, 0, 0), radius=140.0, size=120.0, dense_center=None, dense_r=35.0,
           grass_density=16.0, flower_density=0.05, layout=None, seed=3, clouds=True, pond=True):
    """The keycap world at full scale. Clawd (1.5 BU wide) is ankle-high to the grass, which is
    what makes it feel tiny. Returns dict of handles (ground, pond, positions from layout)."""
    c = c or coll('Meadow')
    L = layout or HERO_LAYOUT
    gs, fs = plant_sets(seed)
    pos = {k: layout_to_world(v, size, center) for k, v in L.items()}
    holes = []
    if pond:
        pu, pv, pr = L['pond']
        holes.append((pos['pond'].x, pos['pond'].y, pr * size))
    g = ground('Ground', center, radius, 1.5, dense_center or pos.get('clawd_land', center), dense_r, holes,
               seed, c)
    add_modifier(g, scatter_group('GrassScatter', gs, grass_density, seed, (0.6, 1.4)), 'Grass')
    add_modifier(g, scatter_group('FlowerScatter', fs, flower_density, seed + 1, (0.8, 1.2), 0.15), 'Flowers')
    out = {'ground': g, 'pos': pos}
    if pond:
        bpy.ops.mesh.primitive_circle_add(vertices=48, radius=holes[0][2] * 1.05, fill_type='NGON',
                                          location=(holes[0][0], holes[0][1], center[2] + 0.2))
        w = bpy.context.active_object
        w.name = 'Pond'
        w.data.materials.append(M.water('PondWater', 'water_deep', 0.03))
        for cl in list(w.users_collection):
            cl.objects.unlink(w)
        c.objects.link(w)
        out['pond'] = w
    far_trees(center, c=c, seed=seed)
    if clouds:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=3500, segments=48, ring_count=24, location=center)
        d = bpy.context.active_object
        d.name = 'CloudDome'
        d.data.materials.append(M.sky_dome())
        for cl in list(d.users_collection):
            cl.objects.unlink(d)
        c.objects.link(d)
        d.visible_shadow = False
        out['clouds'] = d
    return out
