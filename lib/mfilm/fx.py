"""mfilm.fx: the interface effects that turn every change of world into a physical event.

  membrane()     glowing lens-shaped skin = the screen glass Clawd walks through
  ripple()       expanding concentric rings on a surface (screen exit, keycap dive)
  glow_seed()    small warm light left in the ground where the cursor was planted
  beam()         green light shaft through the canopy (magic happens)
  lens_bubble()  glass sphere that grows from a glint (the pull-out reveal)
  burst()        flash + flying cubes (Clawd pops out of the keycap)
  splash()       water/foam cubes kicked up inside a keycap on landing
"""
import math

import bpy
from mathutils import Vector

from . import materials as M
from .core import box, key, key_visible, link, rng, shade_smooth


def _relink(o, c):
    for cl in list(o.users_collection):
        cl.objects.unlink(o)
    (c or bpy.context.scene.collection).objects.link(o)
    return o


def _sphere(name, loc, radius, c, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.active_object
    o.name = name
    shade_smooth(o)
    return _relink(o, c)


def membrane(name, loc, radius=2.2, flatten=0.3, axis='X', c=None):
    """A lens of light standing across the path (normal along `axis`). Starts invisible."""
    o = _sphere(name, loc, radius, c)
    o.scale = {'X': (flatten, 1, 1), 'Y': (1, flatten, 1), 'Z': (1, 1, flatten)}[axis]
    mat = M.fresnel_glow(name + '_Mat', strength=7.0, power=3.0, alpha=0.0)
    o.data.materials.append(mat)
    o.visible_shadow = False
    return o


def membrane_pass(o, f_in, f_hold, f_out, peak=1.0):
    a = M.value_node(o.active_material, 'Alpha')
    key(a, 'default_value', f_in, 0.0)
    key(a, 'default_value', f_hold, peak, 'ease')
    key(a, 'default_value', f_out, 0.0)


def ripple(name, loc, radius, f0, dur, normal='Z', rings=4.0, strength=5.0, c=None):
    """Rings racing outward from loc on a plane facing `normal` ('Z' floor/keycap, 'Y' screen)."""
    bpy.ops.mesh.primitive_plane_add(size=2 * radius, location=loc)
    o = bpy.context.active_object
    o.name = name
    _relink(o, c)
    if normal == 'Y':
        o.rotation_euler.x = math.radians(90)
    elif normal == 'X':
        o.rotation_euler.y = math.radians(90)
    mat = M.ripple(name + '_Mat', strength=strength, rings=rings)
    o.data.materials.append(mat)
    o.visible_shadow = False
    ph, al = M.value_node(mat, 'Phase'), M.value_node(mat, 'Alpha')
    key(ph, 'default_value', f0, 0.0, 'quad_out')
    key(ph, 'default_value', f0 + dur, 1.0)
    key(al, 'default_value', f0, 1.0)
    key(al, 'default_value', f0 + int(dur * 0.55), 1.0, 'ease')
    key(al, 'default_value', f0 + dur, 0.0)
    key_visible(o, f0 - 1, False)
    key_visible(o, f0, True)
    key_visible(o, f0 + dur + 1, False)
    return o


def glow_seed(name, loc, f_on, color='seed_glow', energy=80.0, size=0.5, c=None):
    """A small warm light in the grass: emissive disc + point light, fades up at f_on."""
    disc = box(name, (-size / 2, -size / 2, 0.0), (size / 2, size / 2, 0.04), c,
               M.emission(name + '_Mat', color, 8.0, glow_attr='glow'), bevel=size * 0.4, segs=4)
    disc.location = loc
    disc['glow'] = 0.0
    key(disc, '["glow"]', f_on - 1, 0.0)
    key(disc, '["glow"]', f_on + 6, 1.4, 'expo_out')
    key(disc, '["glow"]', f_on + 20, 1.0)
    from .lighting import light
    lp = light(name + '_Light', 'POINT', Vector(loc) + Vector((0, 0, 0.6)), energy=0.0, color=color, size=0.3,
               c=c)
    key(lp.data, 'energy', f_on - 1, 0.0)
    key(lp.data, 'energy', f_on + 6, energy * 1.4, 'expo_out')
    key(lp.data, 'energy', f_on + 20, energy)
    return disc, lp


def beam(name, loc, height=60.0, radius=3.0, tilt_deg=(18, 0), f0=1, f1=30, c=None):
    """Volumetric light shaft (cylinder with emissive volume) that flares and fades."""
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, vertices=32,
                                        location=(loc[0], loc[1], loc[2] + height / 2))
    o = bpy.context.active_object
    o.name = name
    _relink(o, c)
    o.rotation_euler = (math.radians(tilt_deg[0]), math.radians(tilt_deg[1]), 0)
    o.data.materials.append(M.volume_beam(name + '_Mat'))
    o.visible_shadow = False
    key(o, 'scale', f0, Vector((0.2, 0.2, 1)), 'expo_out')
    key(o, 'scale', f0 + (f1 - f0) // 3, Vector((1, 1, 1)))
    key(o, 'scale', f1, Vector((0.6, 0.6, 1)))
    key_visible(o, f0 - 1, False)
    key_visible(o, f0, True)
    key_visible(o, f1 + 1, False)
    return o


def lens_bubble(name, loc, r1, f_glint, f_open, f_full, c=None):
    """Pull-out reveal: a glint at f_glint grows into a ring, then a glass sphere of radius r1
    by f_full. Put the miniature (keycap world) inside/behind it for the LOD swap."""
    glint = _sphere(name + '_Glint', loc, 1.0, c, 24)
    glint.data.materials.append(M.emission(name + '_GlintMat', '#ffffff', 25.0))
    key(glint, 'scale', f_glint, Vector((0.01, 0.01, 0.01)), 'expo_out')
    key(glint, 'scale', f_open, Vector((r1 * 0.08,) * 3), 'ease')
    key(glint, 'scale', f_open + 3, Vector((0.01, 0.01, 0.01)))
    ball = _sphere(name, loc, 1.0, c)
    ball.data.materials.append(M.glass(name + '_Glass', 0.0, 1.35))
    rim = _sphere(name + '_Rim', loc, 1.03, c)
    rim.data.materials.append(M.fresnel_glow(name + '_RimMat', strength=4.0, power=2.0, alpha=1.0))
    for o in (ball, rim):
        o.visible_shadow = False
        key(o, 'scale', f_open, Vector((0.02, 0.02, 0.02)), 'expo_out')
        key(o, 'scale', f_full, Vector((r1, r1, r1)))
        key_visible(o, f_open - 1, False)
        key_visible(o, f_open, True)
    key_visible(glint, f_glint - 1, False)
    key_visible(glint, f_glint, True)
    key_visible(glint, f_open + 4, False)
    return ball, rim, glint


def ballistic(objs, f0, vels, life, g=-60.0, ground_z=None, shrink=True, step=2):
    """Key simple projectile motion for a list of objects (velocities in BU/s)."""
    fps = bpy.context.scene.render.fps
    for o, v in zip(objs, vels):
        p0 = o.location.copy()
        for k in range(0, life + 1, step):
            t = k / fps
            p = p0 + Vector(v) * t + Vector((0, 0, 0.5 * g * t * t))
            if ground_z is not None:
                p.z = max(p.z, ground_z)
            key(o, 'location', f0 + k, p, 'linear')
            if shrink:
                s = max(0.0, 1 - (k / life) ** 2)
                key(o, 'scale', f0 + k, Vector((s, s, s)), 'linear')
        key_visible(o, f0 - 1, False)
        key_visible(o, f0, True)
        key_visible(o, f0 + life + 1, False)


def _cubes(name, loc, n, size, mat, c):
    out = []
    for i in range(n):
        h = size / 2
        o = box(f'{name}_{i}', (-h, -h, -h), (h, h, h), c, mat, bevel=size * 0.15, segs=1)
        o.location = loc
        out.append(o)
    return out


def splash(name, loc, f, n=24, speed=6.0, size=0.06, mat=None, seed=1, c=None):
    r = rng(seed)
    mat = mat or M.matte('Foam', 'foam', 0.4)
    objs = _cubes(name, loc, n, size, mat, c)
    vels = [(r.uniform(-1, 1) * speed * 0.4, r.uniform(-1, 1) * speed * 0.4, r.uniform(0.5, 1) * speed)
            for _ in objs]
    ballistic(objs, f, vels, 14, g=-90.0, ground_z=loc[2])
    return objs


def burst(name, loc, f, n=30, speed=10.0, size=0.08, color='membrane', energy=400.0, seed=2, c=None):
    """Pop-out flash: point-light spike + emissive cubes + a ring on the surface."""
    r = rng(seed)
    mat = M.emission(name + '_Mat', color, 8.0)
    objs = _cubes(name, loc, n, size, mat, c)
    vels = []
    for _ in objs:
        a = r.uniform(0, 2 * math.pi)
        e = r.uniform(0.2, 1.2)
        vels.append((math.cos(a) * math.cos(e) * speed, math.sin(a) * math.cos(e) * speed, math.sin(e) * speed))
    ballistic(objs, f, vels, 16, g=-40.0)
    from .lighting import light
    lp = light(name + '_Flash', 'POINT', Vector(loc) + Vector((0, 0, 0.5)), energy=0.0, color=color, size=0.5, c=c)
    key(lp.data, 'energy', f - 1, 0.0)
    key(lp.data, 'energy', f + 2, energy, 'expo_out')
    key(lp.data, 'energy', f + 14, 0.0)
    ring = ripple(name + '_Ring', loc, 2.5, f, 18, 'Z', rings=2.0, c=c)
    return objs, lp, ring
