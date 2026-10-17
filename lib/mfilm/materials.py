"""mfilm.materials: every surface in the film as a factory function.

Palette (sRGB hex, measured from the benchmark film):
  clawd orange #cc6549 lit / #ac553c shade   terminal void #05080d-#191d24
  resin tint   #4d6472 (seen) / #a9bfcc (base) sky #82ade9 top, #c8d8e7 horizon
  grass fg     #518e26  far trees #9cb8e2
Rule: orange belongs to the character system only (Clawd, cursor, minis, fruit).
"""
import bpy

from .core import hexcol, inp, outp, setin, sset

PAL = {
    'clawd': '#cc6549', 'clawd_eye': '#120c0b', 'cursor': '#d4694c',
    'void': '#05080d', 'void_hi': '#191d24', 'floor': '#0b1017', 'code': '#9aa4ae', 'chevron': '#b8c0c8',
    'rail': '#5c6670', 'resin': '#a9bfcc', 'plate': '#0d1419', 'case': '#1a2027',
    'grass': '#4f8a2a', 'grass_dark': '#2f5a1a', 'grass_lit': '#8fca4a', 'dirt': '#6b4a30', 'stone': '#7b8088',
    'water': '#3d8fb8', 'water_deep': '#1d4f7a', 'foam': '#e8f4f8', 'snow': '#eef3f6', 'ice': '#b9dbea',
    'sand': '#d9c7a0', 'rock_dark': '#2a2c31', 'lava': '#ff3a22', 'leaf': '#3f8f2e', 'leaf_lit': '#77c84a',
    'bark': '#3d3833', 'daisy': '#f4f1e8', 'daisy_eye': '#f2c230', 'flower_blue': '#8fb3ff',
    'sky_top': '#82ade9', 'sky_hor': '#c8d8e7', 'far_tree': '#9cb8e2', 'city_light': '#f6efd2',
    'membrane': '#e8f0ff', 'seed_glow': '#ff8a3c', 'beam': '#7dff5a',
}


def col(name_or_hex, a=1.0):
    return hexcol(PAL.get(name_or_hex, name_or_hex), a)


def _new(name):
    m = bpy.data.materials.get(name)
    if m:
        return m, None
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree


def _principled(nt):
    return nt.nodes.get('Principled BSDF')


def principled(name, base='#808080', rough=0.5, metal=0.0, spec=0.5, sss=0.0, sss_radius=(1.0, 0.45, 0.25),
               sss_scale=0.05, coat=0.0, transmission=0.0, ior=1.45, emission=None, emission_strength=0.0,
               alpha=1.0, glow_attr=None, glow_strength=4.0):
    """Generic Principled BSDF. glow_attr='glow' adds an object-property driven emission
    (keyframe obj['glow'] 0..1 to light a keycap, a seed, a sprite ...)."""
    m, nt = _new(name)
    if nt is None:
        return m
    p = _principled(nt)
    base_c = col(base)
    setin(p, base_c, 'Base Color')
    setin(p, rough, 'Roughness')
    setin(p, metal, 'Metallic')
    setin(p, spec, 'Specular IOR Level', 'Specular')
    setin(p, ior, 'IOR')
    setin(p, sss, 'Subsurface Weight', 'Subsurface')
    setin(p, sss_radius, 'Subsurface Radius')
    setin(p, sss_scale, 'Subsurface Scale')
    setin(p, coat, 'Coat Weight', 'Clearcoat')
    setin(p, transmission, 'Transmission Weight', 'Transmission')
    setin(p, alpha, 'Alpha')
    if emission is not None:
        setin(p, col(emission), 'Emission Color', 'Emission')
        setin(p, emission_strength, 'Emission Strength')
    if glow_attr:
        a = nt.nodes.new('ShaderNodeAttribute')
        a.attribute_type, a.attribute_name = 'OBJECT', glow_attr
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = glow_strength
        nt.links.new(outp(a, 'Fac'), mul.inputs[0])
        nt.links.new(mul.outputs[0], inp(p, 'Emission Strength'))
        setin(p, col(emission or base), 'Emission Color', 'Emission')
    if transmission > 0 or alpha < 1:
        transparent_settings(m)
    return m


def transparent_settings(m):
    """EEVEE refraction/transparency flags across versions (no-ops on Cycles)."""
    sset(m, 'surface_render_method', 'DITHERED')
    sset(m, 'use_raytrace_refraction', True)
    sset(m, 'use_screen_refraction', True)
    sset(m, 'blend_method', 'HASHED')
    sset(m, 'use_transparency_overlap', True)
    sset(m, 'refraction_depth', 0.3)
    sset(m, 'thickness_mode', 'SLAB')
    sset(m, 'use_transparent_shadow', True)


def _bump(nt, p, scale=300.0, strength=0.04):
    n = nt.nodes.new('ShaderNodeTexNoise')
    setin(n, scale, 'Scale')
    setin(n, 8.0, 'Detail')
    b = nt.nodes.new('ShaderNodeBump')
    setin(b, strength, 'Strength')
    nt.links.new(outp(n, 'Fac'), inp(b, 'Height'))
    nt.links.new(outp(b, 'Normal'), inp(p, 'Normal'))
    return n


# --------------------------------------------------------------------------- character


def clay(name='Clay_Clawd', color='clawd', rough=0.62, glow_attr=None):
    """Matte soft-vinyl / polymer clay: subtle SSS (warm edges), micro grain, faint coat."""
    if bpy.data.materials.get(name):
        return bpy.data.materials[name]
    m = principled(name, color, rough=rough, spec=0.35, sss=0.12, sss_radius=(1.0, 0.35, 0.2),
                   sss_scale=0.08, coat=0.06, glow_attr=glow_attr, glow_strength=2.0)
    _bump(m.node_tree, _principled(m.node_tree), 260.0, 0.03)
    return m


def eye(name='Clawd_Eye'):
    return principled(name, 'clawd_eye', rough=0.35, spec=0.6)


# --------------------------------------------------------------------------- glass / water


def resin(name='Resin', tint='resin', rough=0.03, absorb=0.18, frost=False):
    """Clear cast resin for keycaps. frost=True gives the satin top surface."""
    m = principled(name, tint, rough=0.22 if frost else rough, transmission=1.0, ior=1.5, spec=0.5)
    nt = m.node_tree
    if absorb > 0 and not nt.nodes.get('Volume Absorption'):
        va = nt.nodes.new('ShaderNodeVolumeAbsorption')
        setin(va, col('#7f9aa8'), 'Color')
        setin(va, absorb, 'Density')
        out = nt.nodes.get('Material Output')
        nt.links.new(outp(va, 'Volume'), inp(out, 'Volume'))
    return m


def water(name='Water', tint='water', rough=0.02):
    if bpy.data.materials.get(name):
        return bpy.data.materials[name]
    m = principled(name, tint, rough=rough, transmission=1.0, ior=1.33, spec=0.5)
    nt = m.node_tree
    p = _principled(nt)
    w = nt.nodes.new('ShaderNodeTexWave')
    setin(w, 40.0, 'Scale')
    setin(w, 3.0, 'Distortion')
    b = nt.nodes.new('ShaderNodeBump')
    setin(b, 0.08, 'Strength')
    nt.links.new(outp(w, 'Fac'), inp(b, 'Height'))
    nt.links.new(outp(b, 'Normal'), inp(p, 'Normal'))
    return m


def glass(name='Glass', rough=0.0, ior=1.45):
    return principled(name, '#ffffff', rough=rough, transmission=1.0, ior=ior)


# --------------------------------------------------------------------------- emissive


def emission(name, color, strength=1.0, glow_attr=None):
    """Pure emission (code lines, screen sprite, city lights). glow_attr multiplies strength."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission')
    setin(e, col(color), 'Color')
    setin(e, strength, 'Strength')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(outp(e, 'Emission'), inp(out, 'Surface'))
    if glow_attr:
        a = nt.nodes.new('ShaderNodeAttribute')
        a.attribute_type, a.attribute_name = 'OBJECT', glow_attr
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = strength
        nt.links.new(outp(a, 'Fac'), mul.inputs[0])
        nt.links.new(mul.outputs[0], inp(e, 'Strength'))
    return m


def fresnel_glow(name='Membrane', color='membrane', strength=6.0, power=4.0, alpha=1.0):
    """Light membrane / bubble rim: emission only at grazing angles, transparent elsewhere.
    Animate material['alpha'] via the Value node named 'Alpha' (see fx.membrane)."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    setin(lw, 0.35, 'Blend')
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 1.0 / power
    nt.links.new(outp(lw, 'Facing'), pw.inputs[0])
    am = nt.nodes.new('ShaderNodeValue')
    am.name = am.label = 'Alpha'
    am.outputs[0].default_value = alpha
    fac = nt.nodes.new('ShaderNodeMath')
    fac.operation = 'MULTIPLY'
    fac.use_clamp = True
    nt.links.new(pw.outputs[0], fac.inputs[0])
    nt.links.new(am.outputs[0], fac.inputs[1])
    e = nt.nodes.new('ShaderNodeEmission')
    setin(e, col(color), 'Color')
    setin(e, strength, 'Strength')
    t = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fac.outputs[0], mix.inputs[0])
    nt.links.new(outp(t, 'BSDF'), mix.inputs[1])
    nt.links.new(outp(e, 'Emission'), mix.inputs[2])
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(mix.outputs[0], inp(out, 'Surface'))
    transparent_settings(m)
    return m


def ripple(name='Ripple', color='membrane', strength=5.0, rings=4.0):
    """Concentric expanding rings on a disc (UV centred at 0.5). Animate the Value node
    'Phase' 0 -> 1 and 'Alpha' 1 -> 0 (see fx.ripple)."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sub = nt.nodes.new('ShaderNodeVectorMath')
    sub.operation = 'SUBTRACT'
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    nt.links.new(outp(tc, 'UV'), sub.inputs[0])
    ln = nt.nodes.new('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    nt.links.new(outp(sub, 'Vector'), ln.inputs[0])
    d = outp(ln, 'Value')                                   # 0 centre .. 0.5 rim
    ph = nt.nodes.new('ShaderNodeValue')
    ph.name = ph.label = 'Phase'
    al = nt.nodes.new('ShaderNodeValue')
    al.name = al.label = 'Alpha'
    al.outputs[0].default_value = 1.0

    def mth(op, a, b, clamp=False):
        n = nt.nodes.new('ShaderNodeMath')
        n.operation, n.use_clamp = op, clamp
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]
    # rings = sin((d - phase*0.5) * rings * 2pi), masked to d < phase*0.5 (front of wave)
    x = mth('SUBTRACT', d, mth('MULTIPLY', ph.outputs[0], 0.5))
    wave = mth('POWER', mth('ABSOLUTE', mth('SINE', mth('MULTIPLY', x, rings * 6.2832), 0), 0), 6.0)
    front = mth('LESS_THAN', d, mth('MULTIPLY', ph.outputs[0], 0.5))
    edge = mth('SUBTRACT', 1.0, mth('MULTIPLY', d, 2.0), clamp=True)
    fac = mth('MULTIPLY', mth('MULTIPLY', mth('MULTIPLY', wave, front), edge), al.outputs[0], clamp=True)
    e = nt.nodes.new('ShaderNodeEmission')
    setin(e, col(color), 'Color')
    setin(e, strength, 'Strength')
    t = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fac, mix.inputs[0])
    nt.links.new(outp(t, 'BSDF'), mix.inputs[1])
    nt.links.new(outp(e, 'Emission'), mix.inputs[2])
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(mix.outputs[0], inp(out, 'Surface'))
    transparent_settings(m)
    return m


def value_node(mat, name):
    """The Value node used as an animatable parameter inside a material."""
    return mat.node_tree.nodes[name].outputs[0]


# --------------------------------------------------------------------------- environment


def dark_gloss(name='DarkGloss', color='floor', rough=0.28):
    return principled(name, color, rough=rough, spec=0.6)


def metal(name='Metal', color='rail', rough=0.3):
    return principled(name, color, rough=rough, metal=1.0)


def matte(name, color, rough=0.85, glow_attr=None, glow_strength=3.0):
    """Voxel terrain / diorama colours. glow_attr='glow' lets a keycap light up from inside."""
    return principled(name, color, rough=rough, spec=0.3, glow_attr=glow_attr, glow_strength=glow_strength)


def grass_blade(name='GrassBlade', color='grass', tip='grass_lit'):
    """Translucent blade: Principled + Translucent mix, gradient root->tip on UV.y."""
    m, nt = _new(name)
    if nt is None:
        return m
    p = _principled(nt)
    setin(p, 0.45, 'Roughness')
    setin(p, 0.4, 'Specular IOR Level', 'Specular')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(outp(tc, 'UV'), sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = col('grass_dark')
    ramp.color_ramp.elements[1].color = col(tip)
    mid = ramp.color_ramp.elements.new(0.55)
    mid.color = col(color)
    nt.links.new(outp(sep, 'Y'), inp(ramp, 'Fac'))
    nt.links.new(outp(ramp, 'Color'), inp(p, 'Base Color'))
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
    nt.links.new(outp(ramp, 'Color'), inp(tr, 'Color'))
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.35
    out = nt.nodes.get('Material Output')
    nt.links.new(outp(p, 'BSDF'), mix.inputs[1])
    nt.links.new(outp(tr, 'BSDF'), mix.inputs[2])
    nt.links.new(mix.outputs[0], inp(out, 'Surface'))
    sset(m, 'use_backface_culling', False)
    return m


def bark(name='Bark', color='bark'):
    """Dark mottled bark like the voxel trunk: noise-driven light/dark patches."""
    m, nt = _new(name)
    if nt is None:
        return m
    p = _principled(nt)
    setin(p, 0.8, 'Roughness')
    n = nt.nodes.new('ShaderNodeTexNoise')
    setin(n, 1.6, 'Scale')
    setin(n, 6.0, 'Detail')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = col('#23211f')
    ramp.color_ramp.elements[1].color = col('#6d675f')
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.62
    nt.links.new(outp(n, 'Fac'), inp(ramp, 'Fac'))
    nt.links.new(outp(ramp, 'Color'), inp(p, 'Base Color'))
    _bump(nt, p, 12.0, 0.25)
    return m


def leaf(name='LeafVoxel', color='leaf'):
    """Voxel canopy cube: green with per-instance random brightness and slight translucency."""
    m, nt = _new(name)
    if nt is None:
        return m
    p = _principled(nt)
    setin(p, 0.55, 'Roughness')
    setin(p, 0.15, 'Subsurface Weight', 'Subsurface')
    setin(p, (0.6, 1.0, 0.3), 'Subsurface Radius')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = col('#2f7524')
    ramp.color_ramp.elements[1].color = col('leaf_lit')
    nt.links.new(outp(oi, 'Random'), inp(ramp, 'Fac'))
    nt.links.new(outp(ramp, 'Color'), inp(p, 'Base Color'))
    return m


def sky_dome(name='CloudDome', coverage=0.45, softness=0.25):
    """Soft wispy clouds on a large back-facing hemisphere (alpha from noise)."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    setin(mp, (1.0, 3.0, 1.0), 'Scale')
    nt.links.new(outp(tc, 'Generated'), inp(mp, 'Vector'))
    n = nt.nodes.new('ShaderNodeTexNoise')
    setin(n, 3.5, 'Scale')
    setin(n, 10.0, 'Detail')
    setin(n, 0.6, 'Roughness')
    nt.links.new(outp(mp, 'Vector'), inp(n, 'Vector'))
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = coverage
    ramp.color_ramp.elements[1].position = coverage + softness
    nt.links.new(outp(n, 'Fac'), inp(ramp, 'Fac'))
    e = nt.nodes.new('ShaderNodeEmission')
    setin(e, col('#f4f8fc'), 'Color')
    setin(e, 1.2, 'Strength')
    t = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(outp(ramp, 'Color'), mix.inputs[0])
    nt.links.new(outp(t, 'BSDF'), mix.inputs[1])
    nt.links.new(outp(e, 'Emission'), mix.inputs[2])
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(mix.outputs[0], inp(out, 'Surface'))
    transparent_settings(m)
    return m


def volume_beam(name='Beam', color='beam', density=0.6, strength=3.0):
    """Glowing light shaft (the green beam through the canopy at 38.5 s)."""
    m, nt = _new(name)
    if nt is None:
        return m
    nt.nodes.clear()
    pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    setin(pv, col(color), 'Color')
    setin(pv, density * 0.2, 'Density')
    setin(pv, col(color), 'Emission Color')
    setin(pv, strength, 'Emission Strength')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(outp(pv, 'Volume'), inp(out, 'Volume'))
    return m
