"""S02 8.0-9.0 s  Scale reveal: the whole room. Clawd is an orange speck on the screen.

One second, almost still. The monitor full of code is the only light, the keyboard below it
is asleep (no glow), pines stand in the night window. The cut from S01's close-up to this
wide is the first scale flip of the film.
"""
from mfilm import camera as CAM
from mfilm import character as C
from mfilm import core
from mfilm import env as E
from mfilm import lighting as L
from mfilm import materials as M


def build(ctx):
    f = ctx.f
    E.room(core.coll('Room'), screen_center=(0, 30, 26), screen_size=(56, 32))
    L.rig_room_night(ctx.sc, screen_center=(0, 27, 26), screen_size=(56, 32))
    speck = C.static_mesh('Speck', px=0.07, c=core.coll('Cast'),
                          mat=M.emission('SpeckGlow', 'clawd', 3.0))
    speck.location = (-4.0, 29.92, 10.4)
    cam, tgt = CAM.camera('Cam', (8, -95, 34), (0, 12, 18), lens=35, fstop=8.0)
    CAM.move(cam, [(f(0) - ctx.H, (8, -95, 34)), (f(1.0) + ctx.H, (7.2, -92.5, 33.6))])
