"""SPECIMEN 84 — the graft mass, rendered for MORPHOTOMY.

A suspended organic mass held open by sutures, threaded with fibre-optic
cables, lit by a single arterial-red rim. Rendered on black so the graphic
layer (labels, grid, bloom, grain) can be composited on top.

Usage: blender -b -P render-specimen.py -- <out.png> <res> <samples>
"""
import math
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/specimen84.png"
RES = int(argv[1]) if len(argv) > 1 else 1280
SAMPLES = int(argv[2]) if len(argv) > 2 else 32

random.seed(84)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene


def sock(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return True
    return False


def material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return mat, nt, bsdf


# ---------------------------------------------------------------- materials
flesh, nt, bsdf = material("Flesh")
sock(bsdf, ["Base Color"], (0.030, 0.006, 0.007, 1))
sock(bsdf, ["Roughness"], 0.42)
sock(bsdf, ["Subsurface Weight", "Subsurface"], 0.55)
sock(bsdf, ["Subsurface Radius"], (0.35, 0.045, 0.03))
sock(bsdf, ["Coat Weight", "Clearcoat"], 0.25)
sock(bsdf, ["Coat Roughness"], 0.3)

noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 7.5
noise.inputs["Detail"].default_value = 12.0
noise.inputs["Roughness"].default_value = 0.7
coord = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.6
bump.inputs["Distance"].default_value = 0.03
nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

# wet highlight veins
vein_ramp = nt.nodes.new("ShaderNodeValToRGB")
vein_ramp.color_ramp.elements[0].position = 0.55
vein_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
vein_ramp.color_ramp.elements[1].position = 0.72
vein_ramp.color_ramp.elements[1].color = (0.35, 0.02, 0.02, 1)
nt.links.new(noise.outputs["Fac"], vein_ramp.inputs["Fac"])
mix = nt.nodes.new("ShaderNodeMixRGB")
mix.blend_type = "ADD"
mix.inputs["Fac"].default_value = 0.55
mix.inputs["Color1"].default_value = (0.030, 0.006, 0.007, 1)
nt.links.new(vein_ramp.outputs["Color"], mix.inputs["Color2"])
nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

bone, nt, bsdf = material("Suture")
sock(bsdf, ["Base Color"], (0.55, 0.50, 0.44, 1))
sock(bsdf, ["Roughness"], 0.55)
sock(bsdf, ["Subsurface Weight", "Subsurface"], 0.15)

cable, nt, bsdf = material("Cable")
sock(bsdf, ["Base Color"], (0.012, 0.010, 0.011, 1))
sock(bsdf, ["Roughness"], 0.32)

glow_red, nt, bsdf = material("Fibre")
sock(bsdf, ["Base Color"], (1.0, 0.06, 0.08, 1))
sock(bsdf, ["Emission Color"], (1.0, 0.07, 0.09, 1))
sock(bsdf, ["Emission Strength"], 9.0)

steel, nt, bsdf = material("Steel")
sock(bsdf, ["Base Color"], (0.03, 0.03, 0.035, 1))
sock(bsdf, ["Metallic"], 1.0)
sock(bsdf, ["Roughness"], 0.45)

# ---------------------------------------------------------------- the mass
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=0.52, location=(0.55, 0.0, 0.62))
mass = bpy.context.object
mass.name = "Specimen84"
mass.data.materials.append(flesh)
disp = mass.modifiers.new("lumps", "DISPLACE")
tex = bpy.data.textures.new("lumps", "CLOUDS")
tex.noise_scale = 0.42
tex.noise_depth = 4
disp.texture = tex
disp.strength = 0.11
mass.rotation_euler = (0.1, 0.2, 0.4)
bpy.ops.object.shade_smooth()

# sutures: bone rings pulled tight across the surface
for i in range(6):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.535 + random.uniform(-0.01, 0.01),
        minor_radius=0.006,
        major_segments=96,
        minor_segments=8,
        location=(0.55, 0.0, 0.62),
    )
    ring = bpy.context.object
    ring.name = f"Suture{i}"
    ring.rotation_euler = (random.uniform(-1.2, 1.2), random.uniform(-1.2, 1.2), random.uniform(0, 3.14))
    ring.data.materials.append(bone)
    # pull the thread onto the tissue so it cuts in instead of hovering
    shrink = ring.modifiers.new("hug", "SHRINKWRAP")
    shrink.target = mass
    shrink.wrap_method = "NEAREST_SURFACEPOINT"
    shrink.offset = 0.004

# stitch ticks around two of the rings
for i in range(14):
    angle = i / 14 * math.tau
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.004,
        depth=0.055,
        location=(0.55 + 0.53 * math.cos(angle), 0.0 + 0.53 * math.sin(angle), 0.62 + random.uniform(-0.05, 0.05)),
    )
    tick = bpy.context.object
    tick.rotation_euler = (math.pi / 2, 0, angle)
    tick.data.materials.append(bone)

# ---------------------------------------------------------------- cabling
def cable_from(points, radius, mat, name):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


for i in range(7):
    top = (0.55 + random.uniform(-0.7, 0.7), random.uniform(-0.4, 0.4), 2.4)
    entry = (
        0.55 + 0.42 * math.cos(i / 7 * math.tau),
        0.42 * math.sin(i / 7 * math.tau) * 0.8,
        0.62 + random.uniform(-0.35, 0.35),
    )
    mid = ((top[0] + entry[0]) / 2 + random.uniform(-0.15, 0.15), (top[1] + entry[1]) / 2, 1.5)
    cable_from([top, mid, entry], 0.020, cable, f"Cable{i}")

# fibre-optic strands that pierce the mass, glowing arterial
for i in range(9):
    a = i / 9 * math.tau + 0.3
    p0 = (0.55 + 0.62 * math.cos(a), 0.62 * math.sin(a), 0.62 + 0.2 * math.sin(a * 2))
    p1 = (0.55 + 0.20 * math.cos(a + 0.6), 0.20 * math.sin(a + 0.6), 0.62 + 0.1)
    cable_from([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 0.06, (p0[2] + p1[2]) / 2 + 0.08), p1], 0.0025, glow_red, f"Fibre{i}")

# ---------------------------------------------------------------- rig / room
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.55, 0.0, 2.5))
clamp = bpy.context.object
clamp.scale = (0.9, 0.9, 0.12)
clamp.data.materials.append(steel)

bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.02))
floor = bpy.context.object
floor.data.materials.append(steel)

# steel bay frame behind the specimen
for x, y, z, sx, sy, sz in [
    (1.95, 1.1, 1.2, 0.05, 0.05, 2.4),
    (0.575, 1.1, 2.35, 2.6, 0.05, 0.05),
]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    bar = bpy.context.object
    bar.scale = (sx, sy, sz)
    bar.data.materials.append(steel)

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.002, 0.002, 1)


def area(name, loc, rot, power, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


# a cold, thin key from the left; arterial rim from behind
area("Rim", (2.9, 1.6, 1.6), (math.radians(66), 0, math.radians(148)), 420, 1.6, (1.0, 0.09, 0.11))
area("RimBack", (0.1, 2.4, 1.9), (math.radians(58), 0, math.radians(190)), 260, 2.0, (1.0, 0.16, 0.14))
area("Fill", (-1.6, -1.5, 1.2), (math.radians(72), 0, math.radians(-50)), 14, 2.4, (0.42, 0.48, 0.56))

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 62
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (1.85, -3.55, 1.45)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0.42, 0.0, 0.82)
track = cam.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
scene.render.resolution_x = RES
scene.render.resolution_y = int(RES * 9 / 16)
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = OUT
try:
    scene.view_settings.view_transform = "AgX"
except Exception:
    pass

bpy.ops.render.render(write_still=True)
print("RENDER_DONE", OUT)
