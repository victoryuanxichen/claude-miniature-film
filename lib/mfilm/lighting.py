"""mfilm.lighting: world setups and the five light rigs of the film.

Every rig follows one rule: a *motivated* key (screen glow or sun), a separation light
that pulls the orange character off the background (cool rim in the dark, backlight in
daylight), and in-scene practicals (glowing keycaps, cursor, seed) that double as eye
targets. Light energies assume 1 BU = 1 cm and subjects ~1.5 BU wide; Blender does not
scale light falloff by unit_scale, so tune by rendering `look` stills, never by guessing.
"""
import math

import bpy
from mathutils import Vector

from .core import inp, key, link, outp, setin, sset, try_enum
from .materials import col


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return obj


def light(name, kind, loc, target=(0, 0, 0), energy=1000.0, color='#ffffff', size=1.0, size_y=None,
          c=None, shadow_soft=None, spread_deg=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = col(color)[:3]
    if kind == 'AREA':
        if size_y:
            ld.shape, ld.size, ld.size_y = 'RECTANGLE', size, size_y
        else:
            ld.shape, ld.size = 'DISK', size
        if spread_deg:
            ld.spread = math.radians(spread_deg)
    elif kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = shadow_soft if shadow_soft is not None else size
    elif kind == 'SUN':
        ld.angle = math.radians(size)
    o = link(bpy.data.objects.new(name, ld), c)
    o.location = loc
    if kind != 'POINT':
        aim(o, target)
    return o


def sun(name='Sun', elev_deg=38.0, az_deg=135.0, strength=4.5, color='#fff1dc', angle_deg=1.2, c=None):
    """Sun from azimuth az (0 = +Y, clockwise seen from above) at elevation elev."""
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = strength
    ld.color = col(color)[:3]
    ld.angle = math.radians(angle_deg)
    o = link(bpy.data.objects.new(name, ld), c)
    e, a = math.radians(elev_deg), math.radians(az_deg)
    to_sun = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    o.location = to_sun * 500
    aim(o, (0, 0, 0))
    return o


# --------------------------------------------------------------------------- world


def _world_nodes(sc):
    w = sc.world
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    nt.links.new(outp(bg, 'Background'), inp(out, 'Surface'))
    return nt, bg, out


def world_color(sc, color='void', strength=1.0):
    nt, bg, _ = _world_nodes(sc)
    setin(bg, col(color), 'Color')
    setin(bg, strength, 'Strength')
    return bg


def world_gradient(sc, top='sky_top', horizon='sky_hor', strength=1.0):
    """Cheap stylised sky: vertical gradient (fallback when the physical sky is unavailable)."""
    nt, bg, _ = _world_nodes(sc)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(outp(tc, 'Generated'), sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.5
    ramp.color_ramp.elements[0].color = col(horizon)
    ramp.color_ramp.elements[1].color = col(top)
    nt.links.new(outp(sep, 'Z'), inp(ramp, 'Fac'))
    nt.links.new(outp(ramp, 'Color'), inp(bg, 'Color'))
    setin(bg, strength, 'Strength')
    return bg


def world_sky(sc, elev_deg=38.0, az_deg=135.0, strength=0.3, dust=2.0, air=1.0):
    """Physical sky matching sun(). Falls back to a gradient if no sky model is available."""
    nt, bg, _ = _world_nodes(sc)
    sky = nt.nodes.new('ShaderNodeTexSky')
    used = try_enum(sky, 'sky_type', 'NISHITA', 'MULTIPLE_SCATTERING', 'SINGLE_SCATTERING')
    if not used:
        nt.nodes.remove(sky)
        return world_gradient(sc, strength=strength)
    sset(sky, 'sun_elevation', math.radians(elev_deg))
    sset(sky, 'sun_rotation', math.radians(az_deg))
    sset(sky, 'dust_density', dust)
    sset(sky, 'air_density', air)
    sset(sky, 'sun_disc', False)
    nt.links.new(outp(sky, 'Color'), inp(bg, 'Color'))
    setin(bg, strength, 'Strength')
    return bg


def world_haze(sc, density=0.0006, color='#cfdcec', anisotropy=0.2):
    """Aerial perspective as a world volume (per BU; 0.0006 -> distant trees go blue-grey).
    EEVEE handles this cheaply; in Cycles prefer haze_box() around the visible area."""
    nt = sc.world.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputWorld')
    pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    setin(pv, col(color), 'Color')
    setin(pv, density, 'Density')
    setin(pv, anisotropy, 'Anisotropy')
    nt.links.new(outp(pv, 'Volume'), inp(out, 'Volume'))
    return pv


def haze_box(name='Haze', center=(0, 0, 0), size=(4000, 4000, 600), density=0.0006, color='#cfdcec', c=None):
    from .core import box
    from .materials import _new
    m, nt = _new(name + '_Mat')
    if nt is not None:
        nt.nodes.clear()
        pv = nt.nodes.new('ShaderNodeVolumePrincipled')
        setin(pv, col(color), 'Color')
        setin(pv, density, 'Density')
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(outp(pv, 'Volume'), inp(out, 'Volume'))
    cx, cy, cz = center
    sx, sy, sz = size
    return box(name, (cx - sx / 2, cy - sy / 2, cz), (cx + sx / 2, cy + sy / 2, cz + sz), c, m)


# --------------------------------------------------------------------------- rigs
# Each returns a dict of the lights so shots can animate them.


def rig_terminal(sc, subject=(0, 0, 0.6), c=None):
    """Inside the terminal: soft top key, cool rim, near-black blue void, warm under-glow
    (energy 0; keyed up during the pixel assembly)."""
    world_color(sc, '#070b12', 1.0)
    s = Vector(subject)
    return {
        'key': light('KeyTop', 'AREA', s + Vector((-3, -5, 12)), s, 9000, '#dfe7f5', 10, c=c),
        'rim': light('RimCool', 'AREA', s + Vector((7, 9, 5)), s, 7000, '#9db6ff', 6, c=c),
        'fill': light('FillLow', 'AREA', s + Vector((0, -12, 1.5)), s, 900, '#b9c6d8', 12, c=c),
        'glow': light('UnderGlow', 'POINT', s + Vector((0, -0.6, -0.4)), energy=0.0,
                      color='#ff7a40', size=1.5, c=c),
    }


def rig_room_night(sc, screen_center=(0, 30, 25), screen_size=(56, 32), desk=(0, 0, 0), c=None):
    """Establishing shot: the monitor is the only real light; cold moonlit window behind."""
    world_color(sc, '#03050a', 1.0)
    return {
        'screen': light('ScreenGlow', 'AREA', screen_center, desk, 60000, '#cfe0ff',
                        screen_size[0], screen_size[1], c=c),
        'moon': light('WindowMoon', 'AREA', (screen_center[0] - 60, screen_center[1] + 120, 90), desk,
                      40000, '#7f9cd6', 80, 60, c=c),
        'bounce': light('DeskBounce', 'AREA', (0, -60, 20), desk, 6000, '#8fa0b8', 60, c=c),
    }


def rig_keyboard(sc, center=(0, 0, 0), monitor=(0, 60, 45), c=None):
    """On the keyboard: big cool panel from the monitor (high, behind), weak frontal fill.
    Keycap dioramas add their own light through obj['glow']."""
    world_color(sc, '#060a10', 1.0)
    ctr = Vector(center)
    return {
        'monitor': light('MonitorPanel', 'AREA', Vector(monitor), ctr, 90000, '#d9e4ff', 80, 45, c=c),
        'fill': light('FrontFill', 'AREA', ctr + Vector((0, -70, 18)), ctr, 6000, '#c2cad6', 60, c=c),
        'kick': light('SideKick', 'AREA', ctr + Vector((-80, 10, 25)), ctr, 9000, '#a9c1ff', 30, c=c),
    }


def rig_meadow(sc, elev_deg=38.0, az_deg=135.0, haze=True, c=None):
    """Inside the keycap world: warm afternoon sun, physical sky, aerial haze."""
    world_sky(sc, elev_deg, az_deg, 0.3)
    if haze:
        world_haze(sc)
    return {'sun': sun('Sun', elev_deg, az_deg, 4.5, '#fff1dc', 1.2, c=c)}


def rig_endcard(sc, screen_center=(0, 40, 30), c=None):
    """Final shot: cool screen light from front-top, everything else falls into black."""
    world_color(sc, '#05080d', 1.0)
    return {
        'screen': light('ScreenFront', 'AREA', screen_center, (0, 0, 0), 50000, '#cfdcff', 60, 30, c=c),
        'rim': light('RimLow', 'AREA', (30, 30, 8), (0, 0, 1), 5000, '#9db6ff', 10, c=c),
    }


def pulse(lamp, frames_values, ease='ease'):
    """Key a lamp's energy: [(frame, energy), ...]."""
    for f, v in frames_values:
        key(lamp.data, 'energy', f, v, ease)
