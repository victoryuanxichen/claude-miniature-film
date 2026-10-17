"""mfilm.swarm: one becomes many, many become one.

  mini()              the mini Clawd mesh (one joined mesh, instanced everywhere)
  fruit_grow()        minis appear on the canopy as fruit (reveal)
  fruit_fall()        fruit drops to the ground on the beat (flock, gravity curve)
  rain_rigidbody()    close-up rain with real collisions and tumbling (Bullet, baked)
  pile()              a field of minis lying in the grass, wriggling
  assemble_giant()    minis stream in and stack bottom-up into the giant (flock)
  giant_rig()         the finished giant as a walking rig whose voxels are minis

Scale: the giant is Clawd voxelised at n=1.5 cells per sprite pixel with shell=True
(body 14 x 9 x 9 cells, ~680 minis). One cell = one mini's body width.
"""
import math

import bpy
from mathutils import Vector

from . import character as C
from . import materials as M
from .core import box, coll, key, link, noise_mod, rng
from .gn import add_modifier, flock_group, points_object, reveal_group, set_input
from .voxel import cell_center, clawd_cells

GIANT_N = 1.5


def mini(name='Mini', cell=0.48, c=None):
    """Mini Clawd whose body is exactly `cell` BU wide. Hidden source for instancing."""
    src_c = c or coll('_Sources')
    o = C.static_mesh(name, px=cell / 9.0, c=src_c)
    o.hide_render = o.hide_viewport = True
    return o


def fruit_grow(name, mini_obj, fruit_pts, f0, f1, seed=1, c=None):
    r = rng(seed)
    rots = [(r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), r.uniform(0, 6.28)) for _ in fruit_pts]
    pts = points_object(name, fruit_pts, {'order': [r.random() for _ in fruit_pts], 'rot': rots}, c)
    mod = add_modifier(pts, reveal_group(name + '_GN', mini_obj, width=0.25))
    set_input(mod, 'Progress', 0.0, f0)
    set_input(mod, 'Progress', 1.3, f1)
    return pts, mod


def fruit_fall(name, mini_obj, fruit_pts, ground_z, f0, f1, spread=3.0, seed=2, c=None):
    """Fruit drops: each mini falls with t^2 from its canopy spot to the ground below it."""
    r = rng(seed)
    starts = [Vector(p) for p in fruit_pts]
    targets = [Vector((p.x + r.uniform(-spread, spread), p.y + r.uniform(-spread, spread), ground_z))
               for p in starts]
    attrs = {'start': [tuple(p) for p in starts], 'target': [tuple(p) for p in targets],
             'order': [r.random() * 0.7 for _ in starts],
             'spin': [(r.uniform(-4, 4), r.uniform(-4, 4), r.uniform(-2, 2)) for _ in starts],
             'rot': [(0.0, 0.0, r.uniform(0, 6.28)) for _ in starts], 'size': [1.0] * len(starts)}
    pts = points_object(name, starts, attrs, c)
    mod = add_modifier(pts, flock_group(name + '_GN', mini_obj, arc=0.0, gravity=True, width=0.3))
    set_input(mod, 'Progress', 0.0, f0, 'linear')
    set_input(mod, 'Progress', 1.0, f1, 'linear')
    return pts, mod


def rain_rigidbody(name, mini_obj, starts, f_release0, f_release1, ground_z=0.0, colliders=(), f_end=None,
                   seed=3, bake=True, gravity=300.0, c=None):
    """Real falling minis: linked duplicates, kinematic until their release frame, then
    simulated (they bounce, tumble and pile). Bakes the cache so frames render in any order.
    gravity is in BU/s^2: real g in a 1 BU = 1 cm world would be 981; ~300 reads as 'big
    things falling' inside the keycap world, 981 as 'tiny toys falling'."""
    sc = bpy.context.scene
    sc.use_gravity = True
    sc.gravity = (0.0, 0.0, -gravity)
    c = c or coll(name)
    r = rng(seed)
    if sc.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    rbw = sc.rigidbody_world
    rbw.point_cache.frame_start = max(1, f_release0 - 2)
    rbw.point_cache.frame_end = f_end or sc.frame_end
    for attr, v in (('substeps_per_frame', 10), ('solver_iterations', 20)):
        if hasattr(rbw, attr):
            setattr(rbw, attr, v)
    objs = []
    for i, p in enumerate(starts):
        o = link(bpy.data.objects.new(f'{name}_{i:03d}', mini_obj.data), c)
        o.location = p
        o.rotation_euler = (r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.5), r.uniform(0, 6.28))
        objs.append(o)
    with bpy.context.temp_override(selected_objects=objs, active_object=objs[0], object=objs[0]):
        bpy.ops.rigidbody.objects_add(type='ACTIVE')
    for o in objs:
        rb = o.rigid_body
        rb.collision_shape = 'BOX'
        rb.mass, rb.friction, rb.restitution = 0.05, 0.7, 0.25
        rb.linear_damping, rb.angular_damping = 0.1, 0.25
        rel = r.randint(f_release0, f_release1)
        key(rb, 'kinematic', rbw.point_cache.frame_start, True, 'const')
        key(rb, 'kinematic', rel, False, 'const')
    floor = box(name + '_Floor', (-500, -500, ground_z - 1), (500, 500, ground_z), c)
    floor.hide_render = True
    passive = [floor] + list(colliders)
    with bpy.context.temp_override(selected_objects=passive, active_object=floor, object=floor):
        bpy.ops.rigidbody.objects_add(type='PASSIVE')
    for o in passive:
        o.rigid_body.collision_shape = 'BOX' if o is floor else 'CONVEX_HULL'
    if bake:
        with bpy.context.temp_override(scene=sc):
            bpy.ops.ptcache.bake_all(bake=True)
    return objs


def pile(name, mini_obj, center, radius, count, ground_z=0.0, seed=4, wiggle=True, avoid=(), c=None):
    """Minis lying around after the rain: random yaw, some tipped over, all wriggling a bit."""
    r = rng(seed)
    c = c or coll(name)
    objs = []
    while len(objs) < count:
        a, d = r.uniform(0, 6.28), radius * math.sqrt(r.random())
        p = Vector((center[0] + math.cos(a) * d, center[1] + math.sin(a) * d, ground_z))
        if any((p - Vector(q)).length < rr for q, rr in avoid):
            continue
        o = link(bpy.data.objects.new(f'{name}_{len(objs):03d}', mini_obj.data), c)
        o.location = p
        tip = r.random()
        o.rotation_euler = (math.radians(90) if tip < 0.15 else r.uniform(-0.15, 0.15),
                            math.radians(90) if 0.15 <= tip < 0.25 else r.uniform(-0.15, 0.15), r.uniform(0, 6.28))
        if wiggle:
            key(o, 'rotation_euler', 1, o.rotation_euler.copy())
            noise_mod(o, 'rotation_euler', -1, scale=r.uniform(8, 16), strength=0.12, phase=r.uniform(0, 100))
        objs.append(o)
    return objs


def assemble_giant(name, mini_obj, origin, f0, f1, start_center, start_radius, ground_z=0.0, cell=0.48,
                   n=GIANT_N, seed=5, c=None, core=True):
    """Minis travel from scattered spots on the ground into the giant's shell, bottom layer
    first, last few arriving from the top (the ragged-top look of the benchmark)."""
    r = rng(seed)
    cells = [cc for cc in clawd_cells(n, shell=True) if cc[3] != 'eye']
    px = cell * n
    O = Vector(origin)
    targets = [O + cell_center(cc, n, px) - Vector((0, 0, cell * 0.5)) for cc in cells]
    zs = [t.z for t in targets]
    zmin, zmax = min(zs), max(zs)
    starts, order = [], []
    for t in targets:
        a, d = r.uniform(0, 6.28), start_radius * math.sqrt(r.random())
        starts.append(Vector((start_center[0] + math.cos(a) * d, start_center[1] + math.sin(a) * d, ground_z)))
        order.append((t.z - zmin) / max(1e-6, zmax - zmin) * 0.8 + r.uniform(0, 0.12))
    attrs = {'start': [tuple(p) for p in starts], 'target': [tuple(p) for p in targets], 'order': order,
             'spin': [(r.uniform(-3, 3), r.uniform(-3, 3), r.uniform(-6, 6)) for _ in targets],
             'rot': [(0.0, 0.0, 0.0)] * len(targets), 'size': [1.0] * len(targets)}
    pts = points_object(name, starts, attrs, c)
    mod = add_modifier(pts, flock_group(name + '_GN', mini_obj, arc=4.0, gravity=False, width=0.18))
    set_input(mod, 'Progress', 0.0, f0, 'linear')
    set_input(mod, 'Progress', 1.0, f1, 'linear')
    out = {'points': pts, 'mod': mod, 'count': len(targets)}
    if core:   # dark interior so the eye holes read black, appears once the body is half built
        b = C.BODY
        lo = O + Vector((b[0][0] * px + cell, b[0][1] * px + cell, b[0][2] * px + cell))
        hi = O + Vector((b[1][0] * px - cell, b[1][1] * px - cell, b[1][2] * px - cell))
        core_o = box(name + '_Core', tuple(lo), tuple(hi), c, M.principled('GiantCore', '#0b0605', rough=1.0))
        from .core import key_visible
        key_visible(core_o, f0, False)
        key_visible(core_o, int(f0 + (f1 - f0) * 0.45), True)
        out['core'] = core_o
    return out


def giant_rig(name, mini_obj, loc, cell=0.48, n=GIANT_N, facing_deg=0.0, c=None):
    """The assembled giant as a real rig: each part's minis are instanced on points parented
    to that part's pivot, so character.walk / wave / hop all work on the giant."""
    c = c or coll(name)
    px = cell * n
    rig = C.build(name, loc, px, c, facing_deg=facing_deg)
    for o in bpy.data.objects:
        if o.name.startswith(name + '_') and o.type == 'MESH':
            o.hide_render = o.hide_viewport = True
    groups = {}
    for cc in clawd_cells(n, shell=True):
        if cc[3] == 'eye':
            continue
        groups.setdefault(cc[3], []).append(cell_center(cc, n, px) - Vector((0, 0, cell * 0.5)))
    ng = reveal_group(name + '_GN', mini_obj)
    hipz = C.HIP_Z * px
    for part, pts in groups.items():
        if part == 'body':
            par, off = rig.hip, Vector((0, 0, hipz))
        elif part.startswith('arm_'):
            s = part[-1]
            par = rig.arms[s]
            off = Vector((C.ARMS[s][1][0] * px if s == 'L' else C.ARMS[s][0][0] * px, 0, 4 * px))
        else:
            k = part[4:]
            par = rig.legs[k]
            lo, hi = C.LEGS[k]
            off = Vector(((lo[0] + hi[0]) / 2 * px, (lo[1] + hi[1]) / 2 * px, hipz))
        po = points_object(f'{name}_{part}_Pts', [p - off for p in pts], {'order': [0.0] * len(pts)}, c)
        po.parent = par
        mod = add_modifier(po, ng)
        set_input(mod, 'Progress', 1.0)
        set_input(mod, 'Width', 0.001)
    b = C.BODY
    core = box(name + '_Core', (b[0][0] * px + cell, b[0][1] * px + cell, (b[0][2] - C.HIP_Z) * px + cell),
               (b[1][0] * px - cell, b[1][1] * px - cell, (b[1][2] - C.HIP_Z) * px - cell), c,
               M.principled('GiantCore', '#0b0605', rough=1.0))
    core.parent = rig.hip
    return rig
