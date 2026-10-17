"""S18 59.0-60.0 s  Black. (Silence or the last tail of the music.)"""
from mfilm import camera as CAM
from mfilm import lighting as L


def build(ctx):
    L.world_color(ctx.sc, '#000000', 0.0)
    CAM.camera('Cam', (0, -10, 0), (0, 0, 0), lens=50, fstop=8.0)
