# Runs inside Blender: builds one 3D shot from a JSON plan and renders its frames as PNG.
# blender -b --factory-startup --python blender_scene.py -- plan.json
import bpy, sys, json, math, os, re
from mathutils import Vector

plan = json.load(open(sys.argv[sys.argv.index('--') + 1:][0]))
LIB = plan['lib']
CAM_DIST, CAM_H, LOOK_H, LENS = 9.0, 1.6, 0.9, 35.0
WIDTH = 2 * CAM_DIST * math.tan(math.atan(18 / LENS))  # visible width at the stage line (y=0)
YAW = {'animals2': -90}  # packs whose models face a different axis
ALIAS = {'walking': 'walk', 'flying': 'fly', 'running': 'run', 'recievehit': 'hit', 'sitdown': 'sit', 'standup': 'stand_up'}
SETS = {  # sky colour, sun colour, sun strength, sun elevation (deg), world strength
    'day': ((0.35, 0.58, 0.92), (1.0, 0.95, 0.85), 4.0, 45, 1.0),
    'dawn': ((0.95, 0.62, 0.45), (1.0, 0.7, 0.45), 2.5, 12, 0.8),
    'sunset': ((0.85, 0.42, 0.35), (1.0, 0.55, 0.3), 2.2, 8, 0.7),
    'night': ((0.04, 0.06, 0.18), (0.6, 0.7, 1.0), 1.8, 35, 1.0),
}
GROUNDS = {'meadow': (0.13, 0.30, 0.08), 'road': (0.12, 0.12, 0.13), 'sand': (0.55, 0.42, 0.24), 'snow': (0.80, 0.83, 0.88)}
fps = plan['fps']
scn = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
TOON = plan.get('look') == 'toon'
scn.render.engine = 'BLENDER_EEVEE_NEXT'
if TOON:  # cartoon look: banded light, dark outlines (Freestyle)
    scn.render.use_freestyle = True
    scn.render.line_thickness_mode = 'ABSOLUTE'
    scn.render.line_thickness = 0.9
    ls = scn.view_layers[0].freestyle_settings.linesets[0] if scn.view_layers[0].freestyle_settings.linesets else scn.view_layers[0].freestyle_settings.linesets.new('l')
    ls.select_by_visibility, ls.select_silhouette, ls.select_border, ls.select_crease = True, True, True, False
    ls.linestyle.color = (0.1, 0.07, 0.05)
scn.eevee.taa_render_samples = 16
scn.render.fps = fps
scn.render.resolution_x, scn.render.resolution_y = plan['size']
scn.render.image_settings.file_format = 'PNG'
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Punchy'


def norm(a):
    a = re.sub(r'[^a-z0-9]+', '_', a.split('|')[-1].lower()).strip('_')
    return ALIAS.get(a, a)


def frame(t):
    return int(round((t - plan['t0']) * fps)) + 1


def xpos(x):
    return (x - 0.5) * WIDTH


def mat(col):
    m = bpy.data.materials.new('m')
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*col, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    return m


_found = {}


def relink(path):
    """Some packs keep textures in a sibling Textures folder while the .blend expects them next to itself."""
    parts = os.path.relpath(path, LIB).split(os.sep)
    pack_root = os.path.join(LIB, *parts[:2])
    for img in bpy.data.images:
        if img.source != 'FILE' or img.packed_file is not None:
            continue
        if os.path.exists(bpy.path.abspath(img.filepath, library=img.library)):
            continue
        base = os.path.basename(img.filepath.replace('\\', '/'))
        if (pack_root, base) not in _found:
            _found[(pack_root, base)] = next((os.path.join(d, base) for d, _, fs in os.walk(pack_root) if base in fs), None)
        if _found[(pack_root, base)]:
            img.filepath = _found[(pack_root, base)]
            img.reload()


def load(entry):
    """Append a library model; returns (root empty, armature or None, {action name: action})."""
    path = os.path.join(LIB, entry['file'])
    before = set(bpy.data.objects)
    if entry['fmt'] == 'gltf':
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        acts = {}
    else:
        with bpy.data.libraries.load(path) as (src, dst):
            dst.objects = src.objects
            dst.actions = src.actions
            names = list(src.actions)
        new = [o for o in dst.objects if o is not None and o.type in ('MESH', 'ARMATURE', 'EMPTY')]
        for o in new:
            if o.name not in scn.collection.objects:
                scn.collection.objects.link(o)
        by = {n: a for n, a in zip(names, dst.actions) if a is not None}  # original names: Blender renames clashes to .001
        acts = {k: by[v] for k, v in entry.get('action_map', {}).items() if v in by} or {norm(a.name): a for a in by.values()}
    relink(path)
    root = bpy.data.objects.new('root', None)
    scn.collection.objects.link(root)
    for o in new:
        if o.parent is None and o is not root:
            o.parent = root
    arm = next((o for o in new if o.type == 'ARMATURE'), None)
    return root, arm, acts, [o for o in new if o.type == 'MESH']


def height(meshes):
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]
    return (max(zs) - min(zs)) if zs else 1.0


def show(objs, t_on, t_off):
    for o in objs:
        for f, v in ((1, True), (frame(t_on), False), (frame(t_off), True)):
            o.hide_render = v
            o.keyframe_insert('hide_render', frame=max(1, f))
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves:
                if fc.data_path != 'hide_render':
                    continue
                for k in fc.keyframe_points:
                    k.interpolation = 'CONSTANT'


# set: sky, light, ground
sky, ground = 'day', None
for name, p in plan['elements']:
    if name in SETS:
        sky = name
    if name in GROUNDS:
        ground = name
col, sun_col, strength, elev, world = SETS[sky]
scn.world = bpy.data.worlds.new('w')
scn.world.use_nodes = True
bg = scn.world.node_tree.nodes['Background']
nt = scn.world.node_tree
if sky == 'night':
    bg.inputs[0].default_value = (*col, 1)
else:
    skyt = nt.nodes.new('ShaderNodeTexSky')
    skyt.sky_type = 'NISHITA'
    skyt.sun_elevation = math.radians(elev)
    skyt.sun_rotation = math.radians(35 + 180)
    skyt.air_density, skyt.dust_density = 1.0, 2.0 if sky != 'day' else 0.5
    skyt.sun_disc = False
    nt.links.new(skyt.outputs['Color'], bg.inputs[0])
    world = {'day': 0.35, 'dawn': 0.6, 'sunset': 0.7}[sky]

sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
scn.collection.objects.link(sun)
bg.inputs[1].default_value = world
sun.data.energy, sun.data.color = strength, sun_col
sun.rotation_euler = (math.radians(90 - elev), 0, math.radians(35))
if ground:
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 60, 0))
    bpy.context.object.data.materials.append(mat(GROUNDS[ground]))

# props
for name, p in plan['elements']:
    if name in SETS or name in GROUNDS:
        continue
    root, arm, acts, meshes = load(plan['catalog'][name])
    root.location = (xpos(p.get('x', 0.5)), p.get('z', 4.0), 0)
    root.scale = [p.get('s', 1.0)] * 3
    root.rotation_euler.z = math.radians(p.get('rot', 0))

# actors: one instance per actor name within the shot
inst = {}
for a in plan['actors']:
    name = a['name']
    if name not in inst:
        root, arm, acts, meshes = load(plan['catalog'][name])
        h = height(meshes)
        inst[name] = dict(root=root, arm=arm, acts=acts, objs=[root] + meshes, scale=a['size'] / max(h, 1e-3), segs=[])
    inst[name]['segs'].append(a)
for name, I in inst.items():
    root, arm = I['root'], I['arm']
    root.scale = [I['scale']] * 3
    segs = sorted(I['segs'], key=lambda s: s['t0'])
    if arm is not None:
        arm.animation_data_create()
        arm.animation_data.action = None
        track = arm.animation_data.nla_tracks.new()
    for k, s in enumerate(segs):
        f0, f1 = frame(s['t0']), frame(s['t1'])
        x0, x1 = xpos(s['x0']), xpos(s['x1'])
        heading = s['facing'] if s['facing'] else (1 if x1 >= x0 else -1)
        for f, x in ((f0, x0), (f1, x1)):
            root.location = (x, s['z'], s.get('lift', 0.0))
            root.rotation_euler.z = math.radians((90 if heading > 0 else -90) + YAW.get(plan['catalog'][name]['pack'], 0) + s.get('turn', 0))
            root.keyframe_insert('location', frame=f)
            root.keyframe_insert('rotation_euler', frame=f)
        if arm is not None and s['action'] in I['acts']:
            act = I['acts'][s['action']]
            ln = max(1.0, act.frame_range[1] - act.frame_range[0])
            st = track.strips.new(s['action'], f0, act)
            st.repeat = max(1.0, (f1 - f0) / ln * s.get('speed', 1.0))
            st.scale = 1.0 / s.get('speed', 1.0)
            st.extrapolation = 'HOLD' if k == 0 else 'HOLD_FORWARD'  # hold the first pose before it starts: no T-pose
    for fc in (root.animation_data.action.fcurves if root.animation_data and root.animation_data.action else []):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    show(I['objs'], segs[0]['t0'], max(s['t1'] for s in segs) if plan.get('hide_after') else plan['t1'] + 1)

# camera
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scn.collection.objects.link(cam)
scn.camera = cam
cam.data.lens = LENS
cam.data.clip_end = 600


def place_cam(cx, lens, f):
    cam.location = (cx, -CAM_DIST, CAM_H)
    cam.rotation_euler = (Vector((cx, 0, LOOK_H)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    if f is not None:
        cam.keyframe_insert('location', frame=f)
        cam.keyframe_insert('rotation_euler', frame=f)
        cam.data.keyframe_insert('lens', frame=f)


place_cam(0, LENS, None)
for c in plan['camera']:
    f0, f1 = frame(c['t0']), frame(c['t1'])
    if c['move'] == 'pan':
        d = WIDTH * c.get('amount', 0.12) * (1 if c['dir'] == 'right' else -1)
        place_cam(-d / 2, LENS, f0)
        place_cam(d / 2, LENS, f1)
    elif c['move'] == 'zoom':
        place_cam(0, LENS * c['range'][0], f0)
        place_cam(0, LENS * c['range'][1], f1)

def toonify(m):
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if bsdf is None or out is None:
        return
    base = bsdf.inputs['Base Color']
    diff = nt.nodes.new('ShaderNodeBsdfDiffuse')
    s2r = nt.nodes.new('ShaderNodeShaderToRGB')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.55, 0.55, 0.6, 1)
    e[1].position, e[1].color = 0.12, (1, 1, 1, 1)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    emi = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(diff.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs['Color'], ramp.inputs['Fac'])
    if base.is_linked:
        nt.links.new(base.links[0].from_socket, mul.inputs[6])
    else:
        mul.inputs[6].default_value = base.default_value
    nt.links.new(ramp.outputs['Color'], mul.inputs[7]); nt.links.new(mul.outputs[2], emi.inputs['Color'])
    alpha = bsdf.inputs['Alpha']
    if alpha.is_linked:  # leaves: keep the cut-out
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(alpha.links[0].from_socket, mix.inputs['Fac'])
        nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(emi.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
    else:
        nt.links.new(emi.outputs[0], out.inputs['Surface'])


if TOON:
    for m in bpy.data.materials:
        if m.use_nodes:
            toonify(m)
    scn.view_settings.view_transform, scn.view_settings.look = 'Standard', 'None'
    flat = {'day': (0.62, 0.82, 0.97), 'dawn': (0.99, 0.80, 0.62), 'sunset': (0.98, 0.66, 0.50), 'night': (0.10, 0.12, 0.30)}[sky]
    for n in list(nt.nodes):
        if n.type == 'TEX_SKY':
            nt.nodes.remove(n)
    bg.inputs[0].default_value = (*flat, 1)
    bg.inputs[1].default_value = 1.0
scn.frame_start, scn.frame_end = 1, frame(plan['t1']) - 1
for f in range(scn.frame_start, scn.frame_end + 1):
    scn.frame_set(f)
    scn.render.filepath = os.path.join(plan['out'], f"{plan['first'] + f - 1:05d}.png")
    bpy.ops.render.render(write_still=True)
print('SHOT_DONE', plan['t0'], plan['t1'])
