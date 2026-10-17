"""S03 9.0-10.5 s  Back inside: Clawd on the screen's floor; a reflection sweeps its face.

Low medium shot, slow push. A narrow white light slides across the clay (the screen glass
reflecting something moving) so a nearly static shot still has an event. The far cursor
stays in the background.
"""
from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import lighting as L

from . import common as S


def build(ctx):
    f = ctx.f
    S.terminal_set(ctx, cursor=False)
    S.far_cursor((5.5, 1.6, 0.0))
    rig = S.clawd((0, 0, 0), yaw=-8)
    C.idle(rig, 1, ctx.last)
    C.blink(rig, f(1.0))
    sweep = L.light('Sweep', 'AREA', (-6, -3.2, 2.4), (0, 0, 0.7), energy=0.0, color='#ffffff', size=0.5,
                    c=core.coll('Lights'))
    CAM.move(sweep, [(f(0.15), (-5.0, -3.2, 2.4)), (f(1.25), (5.0, -3.2, 2.4))])
    L.pulse(sweep, [(f(0.1), 0.0), (f(0.35), 6000.0), (f(1.05), 6000.0), (f(1.3), 0.0)])
    cam, tgt = CAM.camera('Cam', (0.9, -6.2, 0.55), (0, 0, 0.75), lens=50, fstop=2.2)
    CAM.move(cam, [(f(0) - ctx.H, (0.9, -6.2, 0.55)), (f(1.5) + ctx.H, (0.6, -5.0, 0.6))])
    CAM.handheld(cam, tgt, 1, 0.008, 0.004)
