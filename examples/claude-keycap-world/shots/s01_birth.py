"""S01 0.0-8.0 s  Birth: cursor -> 2D pixel sprite -> voxel extrusion -> clay Clawd.

One continuous take, timed to the benchmark frames (reference/ref/S01_*): the cursor blinks on
the beat until 2.5 s, 'types' the sprite out of itself (complete by 3.6 s), the flat sprite
extrudes backwards (voxel grid visible by 4.8 s), the grid closes up and the solid clay
character is there by 6.0 s, then blinks and takes its first steps (7.5 s). A second cursor waits in the
distance (motif plant for S10/S11).
"""
from mathutils import Vector

from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import gn
from mfilm import lighting as L
from mfilm import materials as M
from mfilm import voxel as VX

from . import common as S


def build(ctx):
    g = ctx.g
    t, rig_l = S.terminal_set(ctx)
    cur = t['cursor']
    S.far_cursor((9.0, 1.8, 0.0))
    cast = core.coll('Cast')

    # 0.5-2.5 s: blink on beats 1..5, then stay on
    E.blink(cur, ctx.beat, 1, 5)
    core.key_visible(cur, g(2.9), False)

    clay = M.clay()
    n = 2
    cube = VX.cube_obj('PixelCube', C.PX / n, clay, bevel=0.06, c=cast)

    # 2.6-3.6 s: the sprite types itself out of the cursor (flat: Squash = 1)
    sprite = VX.sprite_points('Sprite', n, cursor_x=-1.0, c=cast)
    m = gn.add_modifier(sprite, gn.reveal_group('SpriteGN', cube, width=0.12, overshoot=1.4))
    gn.set_input(m, 'Squash', 1.0)
    gn.set_input(m, 'Progress', 0.0, g(2.6), 'linear')
    gn.set_input(m, 'Progress', 1.15, g(3.6))
    core.key_visible(sprite, g(4.2), False)

    # 4.2-4.8 s: extrusion, front layer first; 5.5-5.85 s grid closes (Gap > 1 hides seams)
    vox, _ = VX.voxel_points('Voxels', n, order_by='depth', c=cast, skip_eyes=True)
    vm = gn.add_modifier(vox, gn.reveal_group('VoxelGN', cube, width=0.1, overshoot=0.6))
    gn.set_input(vm, 'Progress', 0.1, g(4.2))
    gn.set_input(vm, 'Progress', 1.2, g(4.8))
    gn.set_input(vm, 'Gap', 0.9, g(5.5))
    gn.set_input(vm, 'Gap', 1.04, g(5.85))
    core.key_visible(vox, g(4.2) - 1, False)
    core.key_visible(vox, g(4.2), True)
    core.key_visible(vox, g(5.9), False)
    eyes = []
    for s_, (lo, hi) in C.EYES.items():          # dark eye backs for the voxel stage
        eyes.append(core.box(f'VoxEye{s_}', (lo[0] * C.PX, -2.0 * C.PX, lo[2] * C.PX),
                             (hi[0] * C.PX, -1.5 * C.PX, hi[2] * C.PX), cast, M.eye()))
    for e in eyes:
        core.key_visible(e, g(4.2) - 1, False)
        core.key_visible(e, g(4.2), True)
        core.key_visible(e, g(5.9), False)

    # 5.9 s: the solid character pops in, blinks, walks two steps
    rig = C.build('Clawd', (0, 0, 0), c=cast)
    C.show(rig, 1, False)
    C.show(rig, g(5.9), True)
    C.squash(rig, g(5.9), 0.14)
    C.squash(rig, g(5.9) + 8, 0.0, 'back')
    C.blink(rig, g(6.4))
    C.squint(rig, g(7.0), g(7.3), 0.2)
    C.walk(rig, g(6.8), [(0, 0, 0), (1.1, -0.25, 0)], speed=2.0, step=7)

    # warm under-glow while the pixels assemble
    L.pulse(rig_l['glow'], [(g(2.5), 0.0), (g(3.2), 250.0), (g(4.0), 400.0), (g(5.5), 120.0), (g(6.2), 0.0)])

    # camera: ECU on cursor -> pull back -> orbit to show depth -> drop to floor level
    cam, tgt = CAM.camera('Cam', (-1.9, -2.6, 0.75), (-1.2, 0, 0.62), lens=70, fstop=1.6)
    CAM.move(cam, [(g(0.0) - ctx.H, (-1.9, -2.6, 0.75)), (g(2.4), (-1.6, -3.6, 0.8)),
                   (g(3.9), (0.0, -6.8, 1.0))])
    CAM.orbit(cam, (0.2, 0.0, 0.7), 7.2, 0.3, -2, 28, g(4.2), g(5.9))
    CAM.move(cam, [(g(8.0) + ctx.H, (2.9, -6.0, 0.35))])
    CAM.move(tgt, [(g(0.0) - ctx.H, (-1.2, 0, 0.62)), (g(2.4), (-0.9, 0, 0.62)), (g(3.9), (0.1, 0, 0.75)),
                   (g(6.2), (0.2, 0, 0.7)), (g(8.0) + ctx.H, (1.0, 0, 0.6))])
    CAM.fstop_keys(cam, [(g(0.0), 1.6), (g(3.9), 2.8)])
    CAM.handheld(cam, tgt, g(0.0) - ctx.H, 0.01, 0.006)
