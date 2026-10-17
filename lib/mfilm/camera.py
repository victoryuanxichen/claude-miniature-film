"""mfilm.camera: the camera language of the film.

The camera always aims at an Empty (`target`) through a Track To constraint, and focuses
on it by default. So every move is two simple location curves: where the camera is, and
where it looks. Handheld wobble goes on both; a whip pan is a fast move of the target.

Defaults that make 1 BU = 1 cm read as a miniature: low height (subject's eye level or
below), 35-85 mm, f/2-f/5.6 (physical DOF is already shallow at this scale).
"""
import math

import bpy
from mathutils import Vector

from .core import empty, key, keys, link, noise_mod, sset


def camera(name='Cam', loc=(0, -20, 2), target=(0, 0, 1), lens=50.0, fstop=2.8, sensor=36.0,
           clip=(0.02, 30000.0), c=None, make_active=True):
    """Camera + aim Empty. Returns (cam, target_empty)."""
    cd = bpy.data.cameras.new(name)
    cd.lens, cd.sensor_width = lens, sensor
    cd.clip_start, cd.clip_end = clip
    cam = link(bpy.data.objects.new(name, cd), c)
    cam.location = loc
    tgt = empty(name + '_Target', target, c, 0.3, 'SPHERE')
    con = cam.constraints.new('TRACK_TO')
    con.target = tgt
    con.track_axis, con.up_axis = 'TRACK_NEGATIVE_Z', 'UP_Y'
    dof(cam, tgt, fstop)
    if make_active:
        bpy.context.scene.camera = cam
    return cam, tgt


def dof(cam, focus_obj=None, fstop=2.8, distance=None, blades=7, ratio=1.0):
    d = cam.data.dof
    d.use_dof = True
    d.aperture_fstop = fstop
    d.aperture_blades = blades
    sset(d, 'aperture_ratio', ratio)
    if focus_obj is not None:
        d.focus_object = focus_obj
    elif distance is not None:
        d.focus_object = None
        d.focus_distance = distance
    return d


def rack(cam, seq):
    """Rack focus by distance: [(frame, distance), ...]. Detaches the focus object."""
    cam.data.dof.focus_object = None
    keys(cam.data.dof, 'focus_distance', seq)


def fstop_keys(cam, seq):
    keys(cam.data.dof, 'aperture_fstop', seq)


def lens_keys(cam, seq):
    """Zoom / dolly-zoom: [(frame, mm), ...]."""
    keys(cam.data, 'lens', seq)


def move(obj, seq):
    """Location keys: [(frame, (x, y, z)), ...] or with a third item = ease name."""
    for item in seq:
        key(obj, 'location', item[0], Vector(item[1]), item[2] if len(item) > 2 else 'ease')


def orbit(cam, center, radius, height, deg_from, deg_to, f0, f1, ease='ease', steps=8):
    """Arc the camera around `center` (keys sampled along the arc so it stays circular)."""
    cx, cy, cz = center
    for i in range(steps + 1):
        u = i / steps
        a = math.radians(deg_from + (deg_to - deg_from) * u)
        f = f0 + (f1 - f0) * u
        loc = (cx + radius * math.sin(a), cy - radius * math.cos(a), cz + height)
        e = ease if i == 0 else 'linear' if i < steps else 'ease'
        key(cam, 'location', round(f), Vector(loc), e)


def follow_bake(obj, subject, f0, f1, offset=(0, 0, 0), smooth=6, step=2, axes=(1, 1, 1)):
    """Make obj (camera or target) trail `subject` with lag: sample the subject's world
    position, smooth it with a moving average, write keys every `step` frames."""
    sc = bpy.context.scene
    pts = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        pts.append(subject.matrix_world.translation.copy())
    sm = []
    for i in range(len(pts)):
        lo, hi = max(0, i - smooth), min(len(pts), i + 1)
        acc = Vector((0, 0, 0))
        for p in pts[lo:hi]:
            acc += p
        sm.append(acc / (hi - lo))
    off = Vector(offset)
    base = obj.location.copy()
    for i in range(0, len(sm), step):
        p = sm[i] + off
        loc = Vector(p[k] if axes[k] else base[k] for k in range(3))
        key(obj, 'location', f0 + i, loc, 'linear')
    sc.frame_set(f0)


def handheld(cam, target, f0, loc_amp=0.03, aim_amp=0.02, scale=40.0):
    """Subtle breathing/handheld wobble. Keys the current positions first if needed."""
    for o, amp in ((cam, loc_amp), (target, aim_amp)):
        if not (o.animation_data and o.animation_data.action):
            key(o, 'location', f0, o.location.copy())
        noise_mod(o, 'location', -1, scale, amp)


def whip(target, f0, f1, to_loc, ease='expo'):
    """Whip pan: the aim point jumps to a new location in a few frames (enable motion blur)."""
    bpy.context.scene.frame_set(f0)
    key(target, 'location', f0, target.location.copy(), ease)
    key(target, 'location', f1, Vector(to_loc), 'ease')
