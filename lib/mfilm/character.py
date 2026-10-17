"""mfilm.character: Clawd (the Claude Code pixel critter) as a rig of boxes, plus its acting.

Design (sprite pixels, 1 px = PX BU; hero Clawd body = 9 px = 1.5 BU wide):

      ..#########..      body  9 x 6 px, depth 6 px, bevel 0.45 px
      ..##.###.##..      eyes  1 x 2 px, dark, on the front (-Y) face
      ..##.###.##..
      #############      arms  2 x 2 px stubs, depth 2 px, at body mid-height
      #############
      ..#########..
      ...#.#.#.#...      legs  1 x 2 px; outer pair = front legs, inner pair = back legs
      ...#.#.#.#...

Rig: root (ground, travel + facing) > hip (squash/stretch, bob) > body, eye pivots,
arm pivots; leg pivots hang from root at hip height so legs stay planted while the body
squashes. Clawd has no mouth: it acts with blinks, squints, body tilt, hops and turns.
"""
import math

import bpy
from mathutils import Vector

from . import materials as M
from .core import box, empty, join_meshes, key, smooth01

PX = 1.0 / 6.0

BODY = ((-4.5, -3, 2), (4.5, 3, 8))
ARMS = {'L': ((-6.5, -1, 3), (-4.5, 1, 5)), 'R': ((4.5, -1, 3), (6.5, 1, 5))}
LEGS = {'FL': ((-3.5, -3, 0), (-2.5, -2, 2)), 'FR': ((2.5, -3, 0), (3.5, -2, 2)),
        'BL': ((-1.5, 2, 0), (-0.5, 3, 2)), 'BR': ((0.5, 2, 0), (1.5, 3, 2))}
EYES = {'L': ((-2.5, -3, 5), (-1.5, -3, 7)), 'R': ((1.5, -3, 5), (2.5, -3, 7))}
HIP_Z = 2.0


def _center(lo, hi):
    return tuple((lo[i] + hi[i]) / 2 for i in range(3))


class Rig:
    """Handles to one Clawd's parts (find again later with Rig.find(name))."""

    def __init__(self, name):
        g = bpy.data.objects.get
        self.name = name
        self.root, self.hip, self.body = g(name), g(name + '_Hip'), g(name + '_Body')
        self.arms = {s: g(f'{name}_Arm{s}') for s in 'LR'}
        self.eyes = {s: g(f'{name}_Eye{s}') for s in 'LR'}
        self.legs = {k: g(f'{name}_Leg{k}') for k in LEGS}
        self.px = self.root.get('px', PX) if self.root else PX

    @classmethod
    def find(cls, name):
        return cls(name)

    @property
    def height(self):
        return 8 * self.px

    @property
    def width(self):
        return 13 * self.px


def build(name='Clawd', loc=(0, 0, 0), px=PX, c=None, mat=None, eye_mat=None, facing_deg=0.0):
    """Build a rigged Clawd standing at loc (feet on loc.z). Returns Rig."""
    mat = mat or M.clay()
    eye_mat = eye_mat or M.eye()
    root = empty(name, loc, c, size=px * 8)
    root['px'] = px
    root.rotation_euler.z = math.radians(facing_deg)
    hip = empty(name + '_Hip', (0, 0, HIP_Z * px), c, size=px * 4, par=root)

    def part(nm, lo, hi, par, origin, bevel, m):
        a = [(lo[i] - origin[i]) * px for i in range(3)]
        b = [(hi[i] - origin[i]) * px for i in range(3)]
        return box(nm, a, b, c, m, bevel=bevel * px, segs=4, par=par)

    part(name + '_Body', *BODY, hip, (0, 0, HIP_Z), 0.45, mat)
    for s, (lo, hi) in ARMS.items():
        pivot = ((hi[0] if s == 'L' else lo[0]), 0.0, 4.0)
        pv = empty(f'{name}_Arm{s}', ((pivot[0]) * px, 0, (pivot[2] - HIP_Z) * px), c, px * 2, par=hip)
        part(f'{name}_Arm{s}_M', lo, hi, pv, pivot, 0.2, mat)
    for s, (lo, hi) in EYES.items():
        ctr = _center(lo, hi)
        pv = empty(f'{name}_Eye{s}', (ctr[0] * px, -3 * px, (ctr[2] - HIP_Z) * px), c, px, par=hip)
        part(f'{name}_Eye{s}_M', (lo[0], -3.06, lo[2]), (hi[0], -2.9, hi[2]), pv, (ctr[0], -3, ctr[2]), 0.0,
             eye_mat)
    for k, (lo, hi) in LEGS.items():
        ctr = _center(lo, hi)
        top = (ctr[0], ctr[1], HIP_Z)
        pv = empty(f'{name}_Leg{k}', (top[0] * px, top[1] * px, top[2] * px), c, px, par=root)
        part(f'{name}_Leg{k}_M', lo, hi, pv, top, 0.18, mat)
    return Rig(name)


def static_mesh(name='MiniClawd', px=PX, c=None, mat=None):
    """Single joined mesh (for instancing hundreds of minis). Origin at the feet."""
    r = build('_tmp_' + name, (0, 0, 0), px, c, mat)
    parts = [o for o in bpy.data.objects if o.name.startswith('_tmp_' + name) and o.type == 'MESH']
    obj = join_meshes(name, parts, c)
    for o in [o for o in bpy.data.objects if o.name.startswith('_tmp_' + name)]:
        bpy.data.objects.remove(o, do_unlink=True)
    del r
    return obj


def meshes(rig):
    return [o for o in bpy.data.objects if o.name.startswith(rig.name + '_') and o.type == 'MESH']


def show(rig, f, visible):
    """Hard switch the whole character on/off at frame f (e.g. hidden until it materialises)."""
    from .core import key_visible
    for o in meshes(rig):
        key_visible(o, f, visible)


# --------------------------------------------------------------------------- acting
# All functions take frames; pass clock.f(...) / clock.beat(...) values.


def heading(dx, dy):
    """root.rotation_euler.z that makes Clawd face direction (dx, dy). Model faces -Y."""
    return math.atan2(dx, -dy)


def place(rig, f, loc, yaw_deg=None, ease='ease'):
    key(rig.root, 'location', f, Vector(loc), ease)
    if yaw_deg is not None:
        key(rig.root, 'rotation_euler', f, math.radians(yaw_deg), ease, index=2)


def squash(rig, f, amount, ease='ease'):
    """amount > 0 squashes (wider, shorter), < 0 stretches. Volume-preserving-ish."""
    z = 1.0 - amount
    xy = 1.0 + amount * 0.5
    key(rig.hip, 'scale', f, Vector((xy, xy, z)), ease)


def blink(rig, f, dur=5):
    for e in rig.eyes.values():
        key(e, 'scale', f, Vector((1, 1, 1)))
        key(e, 'scale', f + 2, Vector((1.05, 1, 0.1)))
        key(e, 'scale', f + dur, Vector((1, 1, 1)), 'back')


def squint(rig, f0, f1, amount=0.25, ramp=4):
    """Eyes narrow into lines (content / sun / suspicion), held f0..f1."""
    for e in rig.eyes.values():
        key(e, 'scale', f0 - ramp, Vector((1, 1, 1)))
        key(e, 'scale', f0, Vector((1.1, 1, amount)))
        key(e, 'scale', f1, Vector((1.1, 1, amount)))
        key(e, 'scale', f1 + ramp, Vector((1, 1, 1)))


def tilt(rig, f, roll_deg=0.0, pitch_deg=0.0, ease='ease'):
    """Body lean on the hip (curiosity tilt, look up/down)."""
    key(rig.hip, 'rotation_euler', f, (math.radians(pitch_deg), math.radians(roll_deg), 0.0), ease)


def turn(rig, f0, f1, yaw_deg):
    bpy.context.scene.frame_set(f0)
    key(rig.root, 'rotation_euler', f0, rig.root.rotation_euler.z, 'ease', index=2)
    key(rig.root, 'rotation_euler', f1, math.radians(yaw_deg), 'back', index=2)


def wave(rig, f0, side='R', reps=2, period=8, amp_deg=55):
    a = rig.arms[side]
    sgn = 1 if side == 'R' else -1
    key(a, 'rotation_euler', f0, (0, 0, 0))
    for i in range(reps):
        key(a, 'rotation_euler', f0 + period * i + period // 2, (0, sgn * math.radians(-amp_deg), 0))
        key(a, 'rotation_euler', f0 + period * (i + 1), (0, sgn * math.radians(-amp_deg * 0.4), 0))
    key(a, 'rotation_euler', f0 + period * reps + 6, (0, 0, 0), 'back')


def legs_pose(rig, f, swing_deg=0.0, tuck=0.0, ease='ease'):
    """swing: + moves front pair forward / back pair back; tuck 0..1 lifts all legs."""
    for k, leg in rig.legs.items():
        s = swing_deg if k in ('FL', 'BR') else -swing_deg
        key(leg, 'rotation_euler', f, (math.radians(s + tuck * 35 * (1 if k[0] == 'F' else -1)), 0, 0), ease)
        key(leg, 'scale', f, Vector((1, 1, 1 - 0.35 * tuck)), ease)


def hop(rig, f0, f1, to, height=1.2, squash_amt=0.22, yaw_deg=None, spin_deg=0.0):
    """Jump from the current root position (at f0) to `to` (landing at f1).
    Anticipation 4 frames before f0, stretch on take-off, tuck in the air,
    squash on landing, overshoot settle. height in BU above the higher end point."""
    sc = bpy.context.scene
    sc.frame_set(f0)
    p0 = rig.root.location.copy()
    p1 = Vector(to)
    mid_f = (f0 + f1) // 2
    top = max(p0.z, p1.z) + height
    mid = Vector(((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, top))
    key(rig.root, 'location', f0, p0, 'quad_out')
    key(rig.root, 'location', mid_f, mid, 'quad_in')
    key(rig.root, 'location', f1, p1, 'ease')
    if yaw_deg is not None or spin_deg:
        y0 = rig.root.rotation_euler.z
        y1 = math.radians(yaw_deg) if yaw_deg is not None else y0
        key(rig.root, 'rotation_euler', f0, y0, 'ease', index=2)
        key(rig.root, 'rotation_euler', f1, y1 + math.radians(spin_deg), 'ease', index=2)
    squash(rig, f0 - 4, 0.0)
    squash(rig, f0, squash_amt)
    squash(rig, f0 + 2, -0.15)
    squash(rig, mid_f, -0.05)
    squash(rig, f1, squash_amt * 1.1)
    squash(rig, f1 + 3, -0.06, 'ease')
    squash(rig, f1 + 8, 0.0, 'back')
    legs_pose(rig, f0, 0, 0)
    legs_pose(rig, f0 + 3, 0, 0.8)
    legs_pose(rig, f1 - 3, 0, 0.6)
    legs_pose(rig, f1, 0, 0)
    tilt(rig, f0, 0, 0)
    tilt(rig, mid_f, 0, -8)
    tilt(rig, f1, 0, 4)
    tilt(rig, f1 + 8, 0, 0, 'back')


def walk(rig, f0, path, speed=4.0, step=6, swing=28.0, bob=0.04, face=True):
    """Walk through world points `path` (feet z taken from each point) at `speed` BU/s.
    Diagonal leg pairs alternate every `step` frames; hip bobs and rolls slightly."""
    fps = bpy.context.scene.render.fps
    pts = [Vector(p) for p in path]
    f = f0
    key(rig.root, 'location', f, pts[0], 'linear')
    for a, b in zip(pts, pts[1:]):
        d = (b - a)
        n = max(1, round(d.length / speed * fps))
        if face:
            key(rig.root, 'rotation_euler', f, heading(d.x, d.y), 'ease', index=2)
        f += n
        key(rig.root, 'location', f, b, 'linear')
    f_end = f
    i = 0
    for fr in range(f0, f_end + 1, step):
        sgn = 1 if i % 2 == 0 else -1
        legs_pose(rig, fr, swing * sgn, 0.0, 'sine')
        key(rig.hip, 'location', fr, Vector((0, 0, HIP_Z * rig.px)), 'sine')
        key(rig.hip, 'location', fr + step // 2, Vector((0, 0, HIP_Z * rig.px + bob)), 'sine')
        tilt(rig, fr, 2.5 * sgn, -3.0, 'sine')
        i += 1
    legs_pose(rig, f_end + 3, 0, 0, 'back')
    tilt(rig, f_end + 6, 0, 0, 'back')
    return f_end


def idle(rig, f0, f1, period=30, amount=0.015):
    """Breathing: tiny vertical squash cycle so a held character never looks frozen."""
    f = f0
    up = True
    while f <= f1:
        squash(rig, f, -amount if up else amount * 0.5, 'sine')
        f += period // 2
        up = not up


def ease01(f, f0, f1):
    return smooth01((f - f0) / max(1, f1 - f0))
