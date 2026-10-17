"""mfilm.core: scene setup, timing, keyframes, colour and Blender-version compatibility.

Target: Blender 4.2 LTS - 4.5 LTS. Blender 5.x changes (Action slots, compositor node
groups, EEVEE engine id, sky types) are handled through the guarded helpers below.
World scale convention: 1 BU = 1 cm (scene.unit_settings.scale_length = 0.01), so the
camera's physical depth of field gives a real miniature look.
"""
import math
import random

import bpy
from mathutils import Vector

V = Vector

# --------------------------------------------------------------------------- compat


def sset(obj, attr, value):
    """Set an attribute only if this Blender version has it. Returns True on success."""
    if obj is None or not hasattr(obj, attr):
        return False
    try:
        setattr(obj, attr, value)
        return True
    except (TypeError, AttributeError, ValueError):
        return False


def try_enum(obj, attr, *values):
    """Assign the first enum value this version accepts. Returns the value used or None."""
    for v in values:
        try:
            setattr(obj, attr, v)
            return v
        except (TypeError, AttributeError, ValueError):
            continue
    return None


def _find(sockets, names, typ):
    for n in names:
        for s in sockets:
            if s.name == n and (typ is None or s.type == typ):
                return s
    return None


def inp(node, *names, type=None):
    """Input socket by name (first match), optionally filtered by socket type
    ('VALUE', 'VECTOR', 'RGBA', 'INT', 'GEOMETRY', ...). Raises KeyError if missing."""
    s = _find(node.inputs, names, type)
    if s is None:
        raise KeyError(f"{node.bl_idname}: no input {names} type={type}")
    return s


def outp(node, *names, type=None):
    s = _find(node.outputs, names, type)
    if s is None:
        raise KeyError(f"{node.bl_idname}: no output {names} type={type}")
    return s


def setin(node, value, *names, type=None):
    """Set an input default; silently skips inputs this version doesn't have."""
    s = _find(node.inputs, names, type)
    if s is not None:
        s.default_value = value
    return s


# --------------------------------------------------------------------------- colour


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h, a=1.0):
    """'#cc6549' -> linear RGBA tuple (what Blender colour sockets expect)."""
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (_lin(r), _lin(g), _lin(b), a)


def scale_col(c, k):
    return (c[0] * k, c[1] * k, c[2] * k, c[3] if len(c) > 3 else 1.0)


def mix_col(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


# --------------------------------------------------------------------------- random

def rng(seed):
    return random.Random(seed)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------- timing


class Clock:
    """Seconds/beats -> frames. Frame 1 is t = 0 of the shot (local time)."""

    def __init__(self, fps=30, bpm=120.0, t0=0.0):
        self.fps, self.bpm, self.t0 = fps, float(bpm), float(t0)

    @property
    def spb(self):
        return 60.0 / self.bpm

    @property
    def fpb(self):
        """Frames per beat (15 at 30 fps / 120 BPM, 12 at 24 fps)."""
        return self.spb * self.fps

    def f(self, t):
        """Local seconds -> frame number."""
        return int(round(t * self.fps)) + 1

    def g(self, t_global):
        """Global (film) seconds -> local frame of this shot."""
        return self.f(t_global - self.t0)

    def beat(self, n):
        """Local frame of global beat n (beat 0 = film start)."""
        return self.g(n * self.spb)

    def frames(self, seconds):
        return int(round(seconds * self.fps))


# --------------------------------------------------------------------------- scene


def reset(fps=30, res=(1920, 1080), unit_scale=0.01, name='Shot'):
    """Empty factory scene with film defaults."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.name = name
    r = sc.render
    r.fps, r.fps_base = fps, 1.0
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = unit_scale
    sc.unit_settings.length_unit = 'CENTIMETERS'
    color_management(sc)
    w = bpy.data.worlds.new('World')
    w.use_nodes = True
    sc.world = w
    return sc


def color_management(sc, look='Medium High Contrast', exposure=0.0, gamma=1.0):
    vs = sc.view_settings
    try_enum(vs, 'view_transform', 'AgX', 'Filmic', 'Standard')
    try_enum(vs, 'look', f'AgX - {look}', look, 'None')
    vs.exposure, vs.gamma = exposure, gamma
    try_enum(sc.sequencer_colorspace_settings, 'name', 'sRGB')


def set_range(sc, f_start, f_end):
    sc.frame_start, sc.frame_end = int(f_start), int(f_end)
    sc.frame_set(int(f_start))


def beat_markers(sc, clock, f_end, every=1):
    """Timeline markers on every beat (B12, B13 ...) so the beat grid is visible in the UI."""
    n = int(clock.t0 / clock.spb) - 1
    while True:
        f = clock.beat(n)
        if f > f_end:
            break
        if f >= 1 and n % every == 0:
            sc.timeline_markers.new(f'B{n}', frame=f)
        n += 1


# --------------------------------------------------------------------------- collections / objects


def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in p.children:
        p.children.link(c)
    return c


def link(obj, c=None):
    (c or bpy.context.scene.collection).objects.link(obj)
    return obj


def empty(name, loc=(0, 0, 0), c=None, size=0.5, kind='PLAIN_AXES', par=None):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type, o.empty_display_size = kind, size
    link(o, c)
    if par is not None:
        parent(o, par)
    o.location = loc
    return o


def parent(child, par):
    """Parent with identity inverse: child.location is then in the parent's space."""
    child.parent = par
    child.matrix_parent_inverse.identity()
    return child


def shade_smooth(o, smooth=True):
    me = o.data
    me.polygons.foreach_set('use_smooth', [smooth] * len(me.polygons))
    me.update()


def mesh_obj(name, verts, faces, c=None, mats=None, smooth=False, mat_idx=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    o = link(bpy.data.objects.new(name, me), c)
    for m in (mats or []):
        me.materials.append(m)
    if mat_idx is not None and len(mat_idx) == len(me.polygons):
        me.polygons.foreach_set('material_index', list(mat_idx))
    if smooth:
        shade_smooth(o)
    return o


BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def box_verts(lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]


def box(name, lo, hi, c=None, mat=None, bevel=0.0, segs=3, par=None):
    """Axis-aligned box from corner lo to corner hi (local space of par if given)."""
    o = mesh_obj(name, box_verts(lo, hi), BOX_FACES, c, [mat] if mat else None)
    if bevel > 0:
        add_bevel(o, bevel, segs)
        shade_smooth(o)
    if par is not None:
        parent(o, par)
    return o


def add_bevel(o, width, segs=3, angle_deg=40):
    m = o.modifiers.new('Bevel', 'BEVEL')
    m.width, m.segments = width, segs
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle_deg)
    sset(m, 'harden_normals', False)
    return m


def join_meshes(name, objs, c=None):
    """Bake modifiers and join several mesh objects into one static mesh (for instancing)."""
    import bmesh
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    mats = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.transform(ev.matrix_world)
        offset = len(mats)
        mats += list(me.materials) or [None]
        idx = [0] * len(me.polygons)
        me.polygons.foreach_get('material_index', idx)
        me.polygons.foreach_set('material_index', [i + offset for i in idx])
        bm.from_mesh(me)
        ev.to_mesh_clear()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return link(bpy.data.objects.new(name, me), c)


def hide(o, hidden=True):
    o.hide_render = hidden
    o.hide_viewport = hidden


def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)


# --------------------------------------------------------------------------- keyframes

EASE = {
    'linear': ('LINEAR', None), 'ease': ('BEZIER', None), 'const': ('CONSTANT', None),
    'back': ('BACK', 'EASE_OUT'), 'back_in': ('BACK', 'EASE_IN'), 'bounce': ('BOUNCE', 'EASE_OUT'),
    'elastic': ('ELASTIC', 'EASE_OUT'), 'sine': ('SINE', 'EASE_IN_OUT'),
    'quad_in': ('QUAD', 'EASE_IN'), 'quad_out': ('QUAD', 'EASE_OUT'), 'quad': ('QUAD', 'EASE_IN_OUT'),
    'cubic_in': ('CUBIC', 'EASE_IN'), 'cubic_out': ('CUBIC', 'EASE_OUT'), 'cubic': ('CUBIC', 'EASE_IN_OUT'),
    'expo_in': ('EXPO', 'EASE_IN'), 'expo_out': ('EXPO', 'EASE_OUT'), 'expo': ('EXPO', 'EASE_IN_OUT'),
}


def fcurves_of(idb):
    """All F-curves animating an ID (works with legacy and slotted/layered Actions)."""
    ad = getattr(idb, 'animation_data', None)
    if not ad or not ad.action:
        return []
    act = ad.action
    slot = getattr(ad, 'action_slot', None)
    if slot is not None and hasattr(act, 'layers'):
        try:
            from bpy_extras import anim_utils
            cb = anim_utils.action_get_channelbag_for_slot(act, slot)
            if cb:
                return list(cb.fcurves)
        except Exception:
            pass
        found = []
        for layer in act.layers:
            for strip in layer.strips:
                try:
                    cb = strip.channelbag(slot)
                except Exception:
                    cb = None
                if cb:
                    found += list(cb.fcurves)
        if found:
            return found
    return list(getattr(act, 'fcurves', []))


def _full_path(idb, path):
    owner = idb.id_data
    return path if idb == owner else idb.path_from_id(path)


def _assign(idb, path, value, index):
    if path.startswith('['):
        idb[path[2:-2]] = value
    elif index >= 0:
        getattr(idb, path)[index] = value
    else:
        setattr(idb, path, value)


def _interp(idb, path, frame, ease, index):
    ip, es = EASE.get(ease, ('BEZIER', None))
    full = _full_path(idb, path)
    for fc in fcurves_of(idb.id_data):
        if fc.data_path != full or (index >= 0 and fc.array_index != index):
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - frame) < 0.5:
                kp.interpolation = ip
                if es:
                    kp.easing = es
                if ip == 'BEZIER':
                    kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'


def key(idb, path, frame, value=None, ease='ease', index=-1):
    """Insert one key. ease names the curve of the segment *leaving* this key (see EASE)."""
    if value is not None:
        _assign(idb, path, value, index)
    idb.keyframe_insert(data_path=path, frame=frame, index=index)
    _interp(idb, path, frame, ease, index)


def keys(idb, path, seq, index=-1):
    """seq: [(frame, value), ...] or [(frame, value, ease), ...]."""
    for item in seq:
        f, v = item[0], item[1]
        key(idb, path, f, v, item[2] if len(item) > 2 else 'ease', index)


def key_visible(o, frame, visible):
    """Hard on/off switch (constant interpolation) for render and viewport."""
    key(o, 'hide_render', frame, not visible, 'const')
    key(o, 'hide_viewport', frame, not visible, 'const')


def noise_mod(idb, path, index=-1, scale=25.0, strength=0.1, phase=0.0, seed_offset=0.0):
    """Procedural wobble on an animated channel (handheld camera, idle sway). Needs a key first."""
    full = _full_path(idb, path)
    mods = []
    for fc in fcurves_of(idb.id_data):
        if fc.data_path == full and (index < 0 or fc.array_index == index):
            m = fc.modifiers.new('NOISE')
            m.scale, m.strength = scale, strength
            m.phase, m.offset = phase + fc.array_index * 7.3, seed_offset
            mods.append(m)
    return mods
