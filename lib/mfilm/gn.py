"""mfilm.gn: small Geometry Nodes builder plus the three node setups the film relies on.

  reveal  - instances pop in one by one following a per-point 'order' attribute
            (pixel type-on, voxel extrusion, tree canopy growth, fruit appearing)
  flock   - instances fly from 'start' to 'target' in 'order' (swarm -> giant, fruit fall)
  scatter - instances of a collection scattered on a surface with a 'density' attribute
            (grass, daisies, clover, distant trees)

Animated inputs (Progress etc.) are modifier inputs: animate them with set_input(...).
"""
import bpy

from .core import inp, key, link, outp, sset


class GN:
    def __init__(self, name):
        self.ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
        sset(self.ng, 'is_modifier', True)
        self.n = self.ng.nodes
        self.gin = self.n.new('NodeGroupInput')
        self.gout = self.n.new('NodeGroupOutput')
        self.socket('Geometry', 'INPUT', 'NodeSocketGeometry')
        self.socket('Geometry', 'OUTPUT', 'NodeSocketGeometry')

    # sockets / nodes -------------------------------------------------------
    def socket(self, name, io, stype, default=None, lo=None, hi=None):
        s = self.ng.interface.new_socket(name=name, in_out=io, socket_type=stype)
        if default is not None:
            s.default_value = default
        if lo is not None:
            sset(s, 'min_value', lo)
        if hi is not None:
            sset(s, 'max_value', hi)
        return s

    def node(self, idname, **props):
        nd = self.n.new(idname)
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def link(self, a, b):
        self.ng.links.new(a, b)
        return b

    def feed(self, sock, v):
        """Socket <- link (if v is a socket) or default value."""
        if v is None:
            return
        if hasattr(v, 'is_output') and v.is_output:
            self.link(v, sock)
        else:
            sock.default_value = v

    def gi(self, name):
        return self.gin.outputs[name]

    def go(self, name):
        return self.gout.inputs[name]

    # math helpers ------------------------------------------------------------
    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b, c)):
            self.feed(nd.inputs[i], v)
        return nd.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        nd = self.node('ShaderNodeVectorMath', operation=op)
        self.feed(nd.inputs[0], a)
        if b is not None:
            self.feed(nd.inputs[1], b)
        if scale is not None:
            self.feed(inp(nd, 'Scale'), scale)
        return outp(nd, 'Value') if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else outp(nd, 'Vector')

    def xyz(self, x=0.0, y=0.0, z=0.0):
        nd = self.node('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)):
            self.feed(nd.inputs[i], v)
        return nd.outputs[0]

    def attr(self, name, dtype='FLOAT'):
        nd = self.node('GeometryNodeInputNamedAttribute', data_type=dtype)
        inp(nd, 'Name').default_value = name
        return outp(nd, 'Attribute')

    def maprange(self, value, a, b, lo=0.0, hi=1.0, interp='SMOOTHERSTEP'):
        nd = self.node('ShaderNodeMapRange', data_type='FLOAT', interpolation_type=interp, clamp=True)
        for i, v in enumerate((value, a, b, lo, hi)):
            self.feed(nd.inputs[i], v)
        return nd.outputs[0]

    def obj_geo(self, obj):
        nd = self.node('GeometryNodeObjectInfo', transform_space='ORIGINAL')
        inp(nd, 'Object').default_value = obj
        return outp(nd, 'Geometry')

    def coll_geo(self, coll, separate=True):
        nd = self.node('GeometryNodeCollectionInfo', transform_space='ORIGINAL')
        inp(nd, 'Collection').default_value = coll
        inp(nd, 'Separate Children').default_value = separate
        inp(nd, 'Reset Children').default_value = True
        return outp(nd, 'Instances', 'Geometry')

    def instance(self, points, inst, rotation=None, scale=None, selection=None, pick=False, index=None):
        nd = self.node('GeometryNodeInstanceOnPoints')
        self.link(points, inp(nd, 'Points'))
        self.link(inst, inp(nd, 'Instance'))
        self.feed(inp(nd, 'Rotation'), rotation)
        self.feed(inp(nd, 'Scale'), scale)
        self.feed(inp(nd, 'Selection'), selection)
        if pick:
            inp(nd, 'Pick Instance').default_value = True
            self.feed(inp(nd, 'Instance Index'), index)
        return outp(nd, 'Instances')

    def set_position(self, geo, position=None, offset=None):
        nd = self.node('GeometryNodeSetPosition')
        self.link(geo, inp(nd, 'Geometry'))
        self.feed(inp(nd, 'Position'), position)
        self.feed(inp(nd, 'Offset'), offset)
        return outp(nd, 'Geometry')

    def position(self):
        return outp(self.node('GeometryNodeInputPosition'), 'Position')

    def random(self, lo, hi, seed=0, dtype='FLOAT'):
        nd = self.node('FunctionNodeRandomValue', data_type=dtype)
        t = {'FLOAT': 'VALUE', 'FLOAT_VECTOR': 'VECTOR', 'INT': 'INT'}[dtype]
        inp(nd, 'Min', type=t).default_value = lo
        inp(nd, 'Max', type=t).default_value = hi
        inp(nd, 'Seed').default_value = seed
        return outp(nd, 'Value', type=t)

    def realize(self, geo):
        nd = self.node('GeometryNodeRealizeInstances')
        self.link(geo, nd.inputs[0])
        return nd.outputs[0]

    def join(self, *geos):
        nd = self.node('GeometryNodeJoinGeometry')
        for g in geos:
            self.link(g, nd.inputs[0])
        return nd.outputs[0]

    def output(self, geo):
        self.link(geo, self.go('Geometry'))
        return self.ng


# --------------------------------------------------------------------------- modifier inputs


def add_modifier(obj, ng, name='GN'):
    m = obj.modifiers.new(name, 'NODES')
    m.node_group = ng
    return m


def input_id(mod, name):
    return mod.node_group.interface.items_tree[name].identifier


def set_input(mod, name, value, frame=None, ease='ease'):
    """Set (and optionally keyframe) a Geometry Nodes modifier input by its interface name."""
    ident = input_id(mod, name)
    if frame is None:
        mod[ident] = value
    else:
        key(mod, f'["{ident}"]', frame, value, ease)


# --------------------------------------------------------------------------- point clouds


def points_object(name, positions, attrs=None, c=None):
    """Vertex-only mesh. attrs: {name: list of floats or 3-tuples} stored on the POINT domain."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in positions], [], [])
    for an, vals in (attrs or {}).items():
        if not vals:
            continue
        vec = isinstance(vals[0], (tuple, list))
        a = me.attributes.new(an, 'FLOAT_VECTOR' if vec else 'FLOAT', 'POINT')
        flat = [x for v in vals for x in v] if vec else list(vals)
        a.data.foreach_set('vector' if vec else 'value', flat)
    me.update()
    return link(bpy.data.objects.new(name, me), c)


# --------------------------------------------------------------------------- setups


def reveal_group(name, source, width=0.08, overshoot=1.0, gap=1.0):
    """Instances of `source` (object) on points; each scales in when Progress passes its
    'order' (0..1). Inputs: Progress, Width (how many orders overlap), Gap (instance scale),
    Squash (0..1 flattens instances along Y, used for 2D->3D extrusion)."""
    g = GN(name)
    g.socket('Progress', 'INPUT', 'NodeSocketFloat', 0.0)
    g.socket('Width', 'INPUT', 'NodeSocketFloat', width)
    g.socket('Gap', 'INPUT', 'NodeSocketFloat', gap)
    g.socket('Squash', 'INPUT', 'NodeSocketFloat', 0.0)
    order = g.attr('order')
    hi = g.math('ADD', order, g.gi('Width'))
    t = g.maprange(g.gi('Progress'), order, hi)
    # overshoot pop: s = t * (1 + overshoot * sin(pi * t) * 0.25)
    bump = g.math('MULTIPLY', g.math('SINE', g.math('MULTIPLY', t, 3.14159)), 0.25 * overshoot)
    s = g.math('MULTIPLY', g.math('MULTIPLY', t, g.math('ADD', bump, 1.0)), g.gi('Gap'))
    sy = g.math('MULTIPLY', s, g.math('SUBTRACT', 1.0, g.math('MULTIPLY', g.gi('Squash'), 0.9)))
    scale = g.xyz(s, sy, s)
    inst = g.instance(g.gi('Geometry'), g.obj_geo(source), scale=scale,
                      rotation=g.attr('rot', 'FLOAT_VECTOR'))
    return g.output(inst)


def flock_group(name, source, collection=False, arc=2.0, gravity=False, width=0.15):
    """Instances travel from attribute 'start' to 'target' when Progress passes 'order'.
    'spin' (vector, radians) tumbles them in flight; 'size' scales each one.
    gravity=True uses t^2 (falling); otherwise smootherstep with an arc of `arc` BU."""
    g = GN(name)
    g.socket('Progress', 'INPUT', 'NodeSocketFloat', 0.0)
    g.socket('Width', 'INPUT', 'NodeSocketFloat', width)
    g.socket('Arc', 'INPUT', 'NodeSocketFloat', arc)
    start, target = g.attr('start', 'FLOAT_VECTOR'), g.attr('target', 'FLOAT_VECTOR')
    order = g.attr('order')
    t = g.maprange(g.gi('Progress'), order, g.math('ADD', order, g.gi('Width')),
                   interp='LINEAR' if gravity else 'SMOOTHERSTEP')
    if gravity:
        t = g.math('POWER', t, 2.0)
    pos = g.vmath('ADD', start, g.vmath('SCALE', g.vmath('SUBTRACT', target, start), scale=t))
    lift = g.math('MULTIPLY', g.math('SINE', g.math('MULTIPLY', t, 3.14159)), g.gi('Arc'))
    pos = g.vmath('ADD', pos, g.xyz(0.0, 0.0, lift))
    geo = g.set_position(g.gi('Geometry'), position=pos)
    rot = g.vmath('ADD', g.attr('rot', 'FLOAT_VECTOR'),
                  g.vmath('SCALE', g.attr('spin', 'FLOAT_VECTOR'), scale=g.math('SUBTRACT', 1.0, t)))
    src = g.coll_geo(source) if collection else g.obj_geo(source)
    inst = g.instance(geo, src, rotation=rot, scale=g.attr('size'),
                      pick=collection, index=g.attr('variant') if collection else None)
    return g.output(inst)


def scatter_group(name, collection, density=1.0, seed=0, scale=(0.7, 1.3), tilt=0.25, yaw=True):
    """Collection instances scattered on the mesh faces. Uses face/point attribute 'density'
    (0..1) as a mask if present. Inputs: Density (points per BU^2), Seed, Scale Min/Max."""
    g = GN(name)
    g.socket('Density', 'INPUT', 'NodeSocketFloat', density)
    g.socket('Seed', 'INPUT', 'NodeSocketInt', seed)
    g.socket('Scale Min', 'INPUT', 'NodeSocketFloat', scale[0])
    g.socket('Scale Max', 'INPUT', 'NodeSocketFloat', scale[1])
    dist = g.node('GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM')
    g.link(g.gi('Geometry'), inp(dist, 'Mesh'))
    g.link(g.gi('Density'), inp(dist, 'Density'))
    g.link(g.gi('Seed'), inp(dist, 'Seed'))
    g.link(g.attr('density'), inp(dist, 'Density Factor'))
    pts = outp(dist, 'Points')
    rot = g.xyz(g.random(-tilt, tilt, 11), g.random(-tilt, tilt, 12),
                g.random(0.0, 6.2832, 13) if yaw else 0.0)
    nd = g.node('FunctionNodeRandomValue', data_type='FLOAT')
    g.link(g.gi('Scale Min'), inp(nd, 'Min', type='VALUE'))
    g.link(g.gi('Scale Max'), inp(nd, 'Max', type='VALUE'))
    inp(nd, 'Seed').default_value = 14
    sc = outp(nd, 'Value', type='VALUE')
    idx = g.random(0, 999, 15, 'INT')
    inst = g.instance(pts, g.coll_geo(collection), rotation=rot, scale=sc, pick=True, index=idx)
    return g.output(inst)
