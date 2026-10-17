"""mfilm.voxel: everything made of cubes.

  clawd_cells(n)        Clawd voxelised at n cells per sprite pixel (2D sprite, voxel stage, giant)
  sprite_points(...)    the flat pixel sprite as instancing points with a type-on 'order'
  terrain(...)          heightfield of cubes -> one mesh with only exposed faces (dioramas, ground)
  tree(...)             voxel tree: trunk boxes + canopy/fruit points for growth animation
  cube_obj(...)         the bevelled unit cube that reveal/flock instance
"""
import math

import bpy
from mathutils import Vector, noise

from . import materials as M
from .character import ARMS, BODY, EYES, LEGS, PX
from .core import box, mesh_obj, rng
from .gn import points_object

# --------------------------------------------------------------------------- Clawd as cells


def _boxes():
    yield BODY, 'body'
    for s, b in ARMS.items():
        yield b, 'arm_' + s
    for k, b in LEGS.items():
        yield b, 'leg_' + k


def clawd_cells(n=2, shell=False, eye_depth_px=1.0):
    """Cells of Clawd at n cells per sprite pixel. Returns list of (ix, iy, iz, part) in cell
    coordinates (cell size = PX / n, origin at feet centre); part is body, eye, arm_L, arm_R,
    leg_FL, leg_FR, leg_BL or leg_BR. Eyes are carved as holes
    `eye_depth_px` deep with a dark 'eye' cell at the back. shell=True keeps only cells with an
    exposed face (giant made of minis: ~5x fewer instances, identical silhouette)."""
    occ = {}
    for (lo, hi), kind in _boxes():
        for ix in range(round(lo[0] * n), round(hi[0] * n)):
            for iy in range(round(lo[1] * n), round(hi[1] * n)):
                for iz in range(round(lo[2] * n), round(hi[2] * n)):
                    occ[(ix, iy, iz)] = kind
    d = max(1, round(eye_depth_px * n))
    for lo, hi in EYES.values():
        for ix in range(round(lo[0] * n), round(hi[0] * n)):
            for iz in range(round(lo[2] * n), round(hi[2] * n)):
                y0 = round(-3 * n)
                for k in range(d):
                    occ.pop((ix, y0 + k, iz), None)
                occ[(ix, y0 + d, iz)] = 'eye'
    cells = []
    for (ix, iy, iz), kind in occ.items():
        if shell and kind != 'eye':
            nb = [(ix + 1, iy, iz), (ix - 1, iy, iz), (ix, iy + 1, iz), (ix, iy - 1, iz),
                  (ix, iy, iz + 1), (ix, iy, iz - 1)]
            if all(p in occ for p in nb):
                continue
        cells.append((ix, iy, iz, kind))
    return cells


def cell_center(cell, n, px=PX):
    s = px / n
    return Vector(((cell[0] + 0.5) * s, (cell[1] + 0.5) * s, (cell[2] + 0.5) * s))


def cube_obj(name='VoxelCube', size=1.0, mat=None, bevel=0.08, c=None, hide=True):
    """Unit cube centred on its origin, bevelled (instanced by reveal/flock)."""
    h = size / 2
    o = box(name, (-h, -h, -h), (h, h, h), c, mat, bevel=bevel * size, segs=2)
    o.hide_render = hide
    o.hide_viewport = hide
    return o


# --------------------------------------------------------------------------- sprite / morph


SPRITE = [
    "..#########..",
    "..##.###.##..",
    "..##.###.##..",
    "#############",
    "#############",
    "..#########..",
    "...#.#.#.#...",
    "...#.#.#.#...",
]


def sprite_cells(n=1):
    """Front-face pixels of the sprite (x, z) at n cells per pixel, matching clawd_cells."""
    out = []
    rows = len(SPRITE)
    for r, line in enumerate(SPRITE):
        for col, ch in enumerate(line):
            if ch != '#':
                continue
            for a in range(n):
                for b in range(n):
                    ix = (col - 6.5) * n + a
                    iz = (rows - 1 - r) * n + b
                    out.append((round(ix), round(iz)))
    return out


def sprite_points(name, n=2, px=PX, cursor_x=None, jitter=0.08, seed=3, c=None, y=None):
    """2D sprite as points with 'order' = typing order: pixels nearest the cursor appear
    first, sweeping outward like characters being typed (0..1)."""
    r = rng(seed)
    s = px / n
    cx = cursor_x if cursor_x is not None else -6.5 * px
    pts, order = [], []
    for ix, iz in sprite_cells(n):
        p = Vector(((ix + 0.5) * s, (y if y is not None else -3 * px) + s / 2, (iz + 0.5) * s))
        pts.append(p)
        order.append(abs(p.x - cx) * 0.6 + (8 * px - p.z) * 0.4 + r.uniform(0, jitter))
    m = max(order) or 1.0
    order = [o / m for o in order]
    return points_object(name, pts, {'order': order}, c)


def voxel_points(name, n=2, px=PX, shell=False, order_by='depth', seed=4, c=None, skip_eyes=False):
    """Clawd voxel cells as points. order_by:
       'depth'  front layer first, extruding backwards (2D -> 3D extrusion)
       'bottom' bottom-up stacking (giant assembly)
       'random' sparkle-in"""
    r = rng(seed)
    cells = [cc for cc in clawd_cells(n, shell) if not (skip_eyes and cc[3] == 'eye')]
    pts, order, kinds = [], [], []
    ys = [cc[1] for cc in cells]
    zs = [cc[2] for cc in cells]
    for cc in cells:
        pts.append(cell_center(cc, n, px))
        if order_by == 'depth':
            o = (cc[1] - min(ys)) / max(1, max(ys) - min(ys)) + r.uniform(0, 0.05)
        elif order_by == 'bottom':
            o = (cc[2] - min(zs)) / max(1, max(zs) - min(zs)) + r.uniform(0, 0.08)
        else:
            o = r.random()
        order.append(o)
        kinds.append(1.0 if cc[3] == 'eye' else 0.0)
    m = max(order) or 1.0
    order = [o / m for o in order]
    return points_object(name, pts, {'order': order, 'is_eye': kinds}, c), cells


# --------------------------------------------------------------------------- terrain


def terrain(name, nx, ny, cell, height_fn, color_fn, mats, origin=(0, 0, 0), side_fn=None, c=None,
            min_h=1):
    """Heightfield of cubes as ONE mesh with only exposed faces.
    height_fn(i, j) -> int column height (cells); color_fn(i, j, h) -> material key for the top;
    side_fn(i, j, k, h) -> material key for side face at layer k (default: top colour for the
    top layer, 'dirt' then 'stone' below). mats: {key: material}. Cell (0,0) at origin corner."""
    keys = list(mats.keys())
    kidx = {k: i for i, k in enumerate(keys)}
    H = [[max(min_h, int(height_fn(i, j))) for j in range(ny)] for i in range(nx)]
    verts, faces, fmat = [], [], []
    ox, oy, oz = origin

    def quad(p, mk):
        b = len(verts)
        verts.extend(p)
        faces.append((b, b + 1, b + 2, b + 3))
        fmat.append(kidx.get(mk, 0))

    def side_key(i, j, k, h):
        if side_fn:
            return side_fn(i, j, k, h)
        if k >= h - 1:
            return color_fn(i, j, h)
        return 'dirt' if k >= h - 3 else 'stone'

    for i in range(nx):
        for j in range(ny):
            h = H[i][j]
            x0, x1 = ox + i * cell, ox + (i + 1) * cell
            y0, y1 = oy + j * cell, oy + (j + 1) * cell
            z1 = oz + h * cell
            quad([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], color_fn(i, j, h))
            for di, dj, face in ((1, 0, 'x1'), (-1, 0, 'x0'), (0, 1, 'y1'), (0, -1, 'y0')):
                ni, nj = i + di, j + dj
                nh = H[ni][nj] if 0 <= ni < nx and 0 <= nj < ny else 0
                for k in range(nh, h):
                    za, zb = oz + k * cell, oz + (k + 1) * cell
                    mk = side_key(i, j, k, h)
                    if face == 'x1':
                        quad([(x1, y0, za), (x1, y1, za), (x1, y1, zb), (x1, y0, zb)], mk)
                    elif face == 'x0':
                        quad([(x0, y1, za), (x0, y0, za), (x0, y0, zb), (x0, y1, zb)], mk)
                    elif face == 'y1':
                        quad([(x1, y1, za), (x0, y1, za), (x0, y1, zb), (x1, y1, zb)], mk)
                    else:
                        quad([(x0, y0, za), (x1, y0, za), (x1, y0, zb), (x0, y0, zb)], mk)
    o = mesh_obj(name, verts, faces, c, [mats[k] for k in keys], mat_idx=fmat)
    import bmesh
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=cell * 1e-3)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return o, H


def fbm(x, y, scale=1.0, octaves=4, seed=0):
    v, a, f, norm = 0.0, 1.0, 1.0 / scale, 0.0
    for o in range(octaves):
        v += a * noise.noise(Vector((x * f + seed * 17.13, y * f - seed * 7.7, seed * 0.37 + o)))
        norm += a
        a *= 0.5
        f *= 2.0
    return v / norm


# --------------------------------------------------------------------------- tree


def tree(name, base=(0, 0, 0), cell=0.5, trunk_h=24, trunk_w=3, canopy_r=9, seed=5, fruits=60,
         branches=3, c=None):
    """Voxel tree. Returns dict:
      trunk_cells   list of (Vector, order) - trunk cubes, order bottom-up (grow by reveal)
      canopy        points object: canopy cubes with 'order' (inside-out) for reveal
      fruit         list of Vector - fruit positions on the canopy surface (mini Clawds)
      top           canopy centre
    All in BU; cell = cube size."""
    r = rng(seed)
    bx, by, bz = base
    trunk = []
    for k in range(trunk_h):
        for a in range(trunk_w):
            for b in range(trunk_w):
                p = Vector((bx + (a - trunk_w / 2 + 0.5) * cell, by + (b - trunk_w / 2 + 0.5) * cell,
                            bz + (k + 0.5) * cell))
                trunk.append((p, k / trunk_h))
    tips = []
    for i in range(branches):
        ang = r.uniform(0, 2 * math.pi)
        k0 = int(trunk_h * r.uniform(0.55, 0.85))
        p = Vector((bx, by, bz + k0 * cell))
        for s in range(r.randint(4, 7)):
            p = p + Vector((math.cos(ang) * cell, math.sin(ang) * cell, cell * 0.8))
            trunk.append((p.copy(), (k0 + s) / trunk_h))
        tips.append(p)
    top = Vector((bx, by, bz + trunk_h * cell))
    centers = [top] + tips
    pts, order, rots = [], [], []
    seen = set()
    for ci, ctr in enumerate(centers):
        rad = canopy_r * (1.0 if ci == 0 else r.uniform(0.5, 0.7))
        R = int(rad) + 1
        for i in range(-R, R + 1):
            for j in range(-R, R + 1):
                for k in range(-R, R + 1):
                    d = math.sqrt(i * i + j * j + (k * 1.3) ** 2)
                    wob = fbm(i * 0.3 + ci, j * 0.3, 1.0, 2, seed) * rad * 0.35
                    if d > rad + wob:
                        continue
                    q = (round(ctr.x / cell) + i, round(ctr.y / cell) + j, round(ctr.z / cell) + k)
                    if q in seen:
                        continue
                    seen.add(q)
                    pts.append(Vector(q) * cell)
                    order.append(d / (rad + 1) * 0.8 + ci * 0.05 + r.uniform(0, 0.12))
                    rots.append((0.0, 0.0, r.uniform(-0.15, 0.15)))
    m = max(order) or 1.0
    canopy = points_object(name + '_Canopy', pts, {'order': [o / m for o in order], 'rot': rots}, c)
    surface = [p for p in pts if (p - top).length > canopy_r * cell * 0.75]
    r.shuffle(surface)
    fruit = surface[:fruits]
    return {'trunk_cells': trunk, 'canopy': canopy, 'fruit': fruit, 'top': top}


def trunk_points(name, tree_dict, c=None):
    pts = [p for p, _ in tree_dict['trunk_cells']]
    order = [o for _, o in tree_dict['trunk_cells']]
    m = max(order) or 1.0
    return points_object(name, pts, {'order': [o / m for o in order]}, c)
