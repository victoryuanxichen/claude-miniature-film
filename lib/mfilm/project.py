"""mfilm.project: shots.json -> one Blender scene per shot.

Timing model
  * shots.json holds GLOBAL times in seconds (film timeline) and the BPM grid.
  * every shot is built as its own .blend with `handles` extra frames on both sides
    (for edit slack and motion blur): local frame 1 = shot start - handles.
  * ctx.f(t)      local seconds after the cut-in -> frame
    ctx.g(t)      global film seconds            -> frame
    ctx.beat(n)   global beat n (0 = film start)  -> frame
    ctx.cut_in / ctx.cut_out                      -> first / last frame that ends up in the film
"""
import json
import os

import bpy

from .core import Clock, beat_markers, reset, set_range

PRESETS = {
    #            engine      res%  samples  raytrace motion-blur  bloom
    'clay':   dict(engine='WORKBENCH', pct=50, samples=1, raytrace=False, mb=False, bloom=False),
    'previs': dict(engine='EEVEE', pct=50, samples=16, raytrace=False, mb=False, bloom=False),
    'look':   dict(engine='EEVEE', pct=100, samples=64, raytrace=True, mb=True, bloom=True),
    'final':  dict(engine='EEVEE', pct=100, samples=128, raytrace=True, mb=True, bloom=True),
    'cycles_draft': dict(engine='CYCLES', pct=50, samples=64, raytrace=True, mb=True, bloom=True),
    'cycles': dict(engine='CYCLES', pct=100, samples=512, raytrace=True, mb=True, bloom=True),
}


def _sset(o, a, v):
    try:
        if hasattr(o, a):
            setattr(o, a, v)
    except (TypeError, AttributeError, ValueError):
        pass


def enable_gpu():
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
    except KeyError:
        return 'CPU'
    for dt in ('METAL', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
        try:
            prefs.compute_device_type = dt
        except TypeError:
            continue
        prefs.get_devices()
        if any(d.type != 'CPU' for d in prefs.devices):
            for d in prefs.devices:
                d.use = True
            bpy.context.scene.cycles.device = 'GPU'
            return dt
    return 'CPU'


def add_bloom(sc, threshold=1.0, strength=0.35, size=7):
    """Soft glow on emissive things (EEVEE Next has no built-in bloom). Version-guarded."""
    try:
        if hasattr(sc, 'compositing_node_group'):          # Blender 5.x
            ng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
            sc.compositing_node_group = ng
            ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            out = ng.nodes.new('NodeGroupOutput')
        else:
            sc.use_nodes = True
            ng = sc.node_tree
            ng.nodes.clear()
            out = ng.nodes.new('CompositorNodeComposite')
        rl = ng.nodes.new('CompositorNodeRLayers')
        gl = ng.nodes.new('CompositorNodeGlare')
        for t in ('BLOOM', 'FOG_GLOW'):
            try:
                gl.glare_type = t
                break
            except TypeError:
                continue
        for attr, v in (('threshold', threshold), ('mix', strength * 2 - 1), ('size', size), ('quality', 'HIGH')):
            _sset(gl, attr, v)
        for nm, v in (('Threshold', threshold), ('Strength', strength), ('Size', size / 9.0)):
            s = gl.inputs.get(nm)
            if s is not None:
                try:
                    s.default_value = v
                except (TypeError, ValueError):
                    pass
        ng.links.new(rl.outputs['Image'], gl.inputs[0] if gl.inputs[0].type == 'RGBA' else gl.inputs['Image'])
        ng.links.new(gl.outputs[0], out.inputs[0])
    except Exception as e:     # bloom is a nicety; never fail a build over it
        print('[mfilm] bloom skipped:', e)


def apply_preset(sc, name, **ov):
    p = dict(PRESETS[name])
    p.update(ov)
    eng = {'EEVEE': ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'), 'CYCLES': ('CYCLES',),
           'WORKBENCH': ('BLENDER_WORKBENCH',)}[p['engine']]
    for e in eng:
        try:
            sc.render.engine = e
            break
        except TypeError:
            continue
    r = sc.render
    r.resolution_percentage = p['pct']
    _sset(r, 'use_motion_blur', p['mb'])
    _sset(r, 'motion_blur_shutter', 0.5)
    if p['engine'] == 'EEVEE':
        e = sc.eevee
        _sset(e, 'taa_render_samples', p['samples'])
        _sset(e, 'use_raytracing', p['raytrace'])
        _sset(e, 'ray_tracing_method', 'SCREEN')
        _sset(e, 'use_shadows', True)
        _sset(e, 'shadow_ray_count', 2 if p['raytrace'] else 1)
        _sset(e, 'use_volumetric_shadows', True)
        _sset(e, 'volumetric_tile_size', '4' if p['raytrace'] else '8')
        _sset(e, 'use_gtao', True)
        _sset(e, 'fast_gi_method', 'GLOBAL_ILLUMINATION')
        _sset(e, 'use_motion_blur', p['mb'])
        _sset(e, 'use_bloom', p['bloom'])
        rto = getattr(e, 'ray_tracing_options', None)
        if rto is not None:
            _sset(rto, 'resolution_scale', '1' if p['pct'] >= 100 else '2')
            _sset(rto, 'use_denoise', True)
    elif p['engine'] == 'CYCLES':
        cy = sc.cycles
        cy.samples = p['samples']
        _sset(cy, 'use_adaptive_sampling', True)
        _sset(cy, 'adaptive_threshold', 0.015)
        _sset(cy, 'use_denoising', True)
        _sset(cy, 'denoiser', 'OPENIMAGEDENOISE')
        for a, v in (('max_bounces', 16), ('transmission_bounces', 16), ('transparent_max_bounces', 32),
                     ('glossy_bounces', 6), ('diffuse_bounces', 4), ('volume_bounces', 1),
                     ('caustics_reflective', False), ('caustics_refractive', False), ('blur_glossy', 0.6)):
            _sset(cy, a, v)
        enable_gpu()
    else:
        sh = sc.display.shading
        _sset(sh, 'light', 'STUDIO')
        _sset(sh, 'color_type', 'MATERIAL')
    if p['bloom'] and p['engine'] != 'WORKBENCH':
        add_bloom(sc)
    return p


class Ctx:
    def __init__(self, project_dir, shot_id, preset='previs'):
        self.dir = project_dir
        with open(os.path.join(project_dir, 'shots.json'), encoding='utf-8') as fh:
            self.cfg = json.load(fh)
        self.shot = next(s for s in self.cfg['shots'] if s['id'] == shot_id)
        self.id = shot_id
        self.preset = preset
        self.fps = self.cfg.get('fps', 30)
        self.bpm = self.cfg.get('bpm', 120)
        self.H = self.cfg.get('handles', 6)
        self.start, self.end = float(self.shot['start']), float(self.shot['end'])
        self.clock = Clock(self.fps, self.bpm, self.start)
        self.dur = int(round((self.end - self.start) * self.fps))
        self.cut_in = self.H + 1
        self.cut_out = self.H + self.dur
        self.last = self.dur + 2 * self.H
        self.layout = self.cfg.get('layout', {})
        self.state = self.cfg.get('state', {})
        self.sc = None

    # timing ------------------------------------------------------------------
    def f(self, t):
        return self.H + 1 + int(round(t * self.fps))

    def g(self, t_global):
        return self.f(t_global - self.start)

    def beat(self, n):
        return self.g(n * 60.0 / self.bpm)

    @property
    def fpb(self):
        return self.fps * 60.0 / self.bpm

    # story state ---------------------------------------------------------------
    def lit_keys(self, t_global):
        """Keys already woken up before t_global (from state.lit_trail [[kid, t], ...])."""
        return [k for k, t in self.state.get('lit_trail', []) if t < t_global]

    def lit_events(self):
        """[(kid, local_frame)] for wake-ups that happen inside this shot."""
        return [(k, self.g(t)) for k, t in self.state.get('lit_trail', []) if self.start <= t <= self.end]

    # lifecycle -----------------------------------------------------------------
    def setup(self):
        res = tuple(self.cfg.get('res', (1920, 1080)))
        self.sc = reset(self.fps, res, self.cfg.get('unit_scale', 0.01), self.id)
        set_range(self.sc, 1, self.last)
        beat_markers(self.sc, Clock(self.fps, self.bpm, self.start - self.H / self.fps), self.last)
        self.sc.timeline_markers.new('CUT_IN', frame=self.cut_in)
        self.sc.timeline_markers.new('CUT_OUT', frame=self.cut_out)
        return self.sc

    def finish(self, save=True):
        apply_preset(self.sc, self.preset)
        out = os.path.join(self.dir, 'out', 'frames', self.id, '')
        self.sc.render.filepath = out
        self.sc.render.image_settings.file_format = 'PNG'
        _sset(self.sc.render.image_settings, 'color_depth', '16')
        self.sc.frame_set(self.cut_in)
        if save:
            os.makedirs(os.path.join(self.dir, 'blend'), exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(self.dir, 'blend', self.id + '.blend'), compress=True)


def render_stills(sc, frames, folder, prefix):
    os.makedirs(folder, exist_ok=True)
    paths = []
    for f in frames:
        sc.frame_set(int(f))
        p = os.path.join(folder, f'{prefix}_f{int(f):04d}.png')
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths


def render_range(sc, f0, f1, folder):
    os.makedirs(folder, exist_ok=True)
    sc.frame_start, sc.frame_end = int(f0), int(f1)
    sc.render.filepath = os.path.join(folder, '')
    _sset(sc.render, 'use_overwrite', False)
    _sset(sc.render, 'use_placeholder', True)
    bpy.ops.render.render(animation=True)
