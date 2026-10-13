"""Angela Clay Figurine — procedural modeling build script.

Task: 建立一個 Angela 黏土人建模 (Angela clay-person modeling).

Builds a detailed claymation-style chibi figurine of Angela (canonical look:
pink hair, blue eyes) standing on a display pedestal with an embossed
"ANGELA" nameplate, then:
  1. Saves  models/angela_clay/angela_clay.blend   (full editable scene)
  2. Exports models/angela_clay/angela_clay.glb    (portable model)
  3. Renders 4 preview stills into models/angela_clay/render/

Run headless:
    blender -b --python scripts/build_angela_clay_model.py

Exit code 0 = success; non-zero with traceback = failure (no silent errors).
"""

import math
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Vector

# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδ] [A/B/C] [L0-L11]
# =============================================================================

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "models", "angela_clay")
RENDER_DIR = os.path.join(OUT_DIR, "render")
BLEND_PATH = os.path.join(OUT_DIR, "angela_clay.blend")
GLB_PATH = os.path.join(OUT_DIR, "angela_clay.glb")

# ---------------------------------------------------------------------------
# Design spec (decided by task breakdown — canonical Angela clay figure)
# ---------------------------------------------------------------------------
# Chibi proportion (~3 heads), claymation style:
#   * Pedestal with embossed ANGELA nameplate + rope trim
#   * Teal pleated skirt, cream hoodie (pocket, drawstrings, collar)
#   * Skin legs, white socks with teal stripe, dark clay shoes
#   * Big head, pink hair: carved scalp cap as volume base, all visible hair
#     as tapered bezier strands (bangs/temple/locks/back/ahoge)
#   * Layered anime eyes, tapered curve brows, button nose, curve smile,
#     rosy cheeks, hair clip, heart pendant
#   * Curved-strand arms/legs with fabric folds, pleats, drawstrings, straps;
#     mitten hands with tapered thumbs; right arm waving
PREFIX = "AngelaClay_"

SKIN = (0.97, 0.67, 0.54)
HAIR = (0.96, 0.30, 0.50)
SWEATER = (0.93, 0.87, 0.77)
SKIRT = (0.09, 0.42, 0.42)
SOCK = (0.95, 0.95, 0.93)
SHOE = (0.26, 0.15, 0.10)
EYE_BLUE = (0.10, 0.38, 0.90)
PUPIL = (0.02, 0.03, 0.07)
BROW = (0.82, 0.36, 0.50)
MOUTH = (0.78, 0.24, 0.28)
CHEEK = (0.99, 0.48, 0.50)
PEDESTAL = (0.74, 0.68, 0.63)
GROUND = (0.86, 0.83, 0.79)
GOLD = (0.92, 0.66, 0.20)
CLIP = (0.97, 0.78, 0.26)
HEART = (0.92, 0.35, 0.44)

HEAD_C = (0.0, 0.0, 1.56)  # head center
HEAD_R = 0.40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def set_in(node, key, value):
    """Set a shader input defensively (Blender version tolerant)."""
    if key in node.inputs:
        node.inputs[key].default_value = value


def make_clay_mat(
    name, color, roughness=0.5, subsurface=0.0, metallic=0.0, noise_scale=11.0, bump_strength=0.22
):
    """Principled material with subtle hand-pressed clay micro-bump."""
    mat = bpy.data.materials.new(PREFIX + "Mat_" + name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    set_in(bsdf, "Base Color", (color[0], color[1], color[2], 1.0))
    set_in(bsdf, "Roughness", roughness)
    set_in(bsdf, "Metallic", metallic)
    if subsurface > 0.0:
        set_in(bsdf, "Subsurface Weight", subsurface)
        set_in(bsdf, "Subsurface Radius", (0.08, 0.03, 0.02))
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.55
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.018
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def scene():
    return bpy.context.scene


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_list in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for block in list(block_list):
            if block.users == 0:
                block_list.remove(block)


def smooth(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    if hasattr(obj.data, "use_auto_smooth"):  # Blender 4.0
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(40)
    obj.select_set(False)


def add_sphere(name, loc, scale, mat, seg=48, ring=24, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=seg, ring_count=ring, radius=1.0, location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = PREFIX + name
    obj.scale = scale
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def add_cyl(name, loc, radius, depth, mat, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = PREFIX + name
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def add_cone(name, loc, r1, r2, depth, mat, rot=(0, 0, 0), verts=64):
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = PREFIX + name
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def add_torus(
    name, loc, major, minor, mat, rot=(0, 0, 0), scale=(1, 1, 1), major_seg=64, minor_seg=16
):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major,
        minor_radius=minor,
        major_segments=major_seg,
        minor_segments=minor_seg,
        location=loc,
        rotation=rot,
    )
    obj = bpy.context.active_object
    obj.name = PREFIX + name
    obj.scale = scale
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def add_plane(name, loc, size, mat):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    obj = bpy.context.active_object
    obj.name = PREFIX + name
    obj.data.materials.append(mat)
    return obj


def aim(obj, target=(0.0, 0.0, 1.0)):
    """Point object (-Z) at target."""
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def dir_rot(start, end):
    """Euler rotation aligning local +Z along start->end."""
    d = Vector(end) - Vector(start)
    return d.to_track_quat("Z", "Y").to_euler()


def front_y(x, z, r=HEAD_R):
    """Y of the front surface of the head sphere at (x, z)."""
    v = r * r - x * x - (z - HEAD_C[2]) ** 2
    d = math.sqrt(v) if v > 0.0004 else 0.02
    return -d


def back_y(x, z, r):
    """Y of the back surface of a sphere (radius r, center HEAD_C) at (x, z)."""
    v = r * r - x * x - (z - HEAD_C[2]) ** 2
    d = math.sqrt(v) if v > 0.0004 else 0.02
    return d


def torso_y(x, z):
    """Front surface Y of the sweater torso ellipsoid at (x, z)."""
    dz = z - 0.94
    t = 1.0 - (x / 0.25) ** 2 - (dz / 0.25) ** 2
    return -0.20 * math.sqrt(t) if t > 0.0004 else -0.04


def skirt_r(z):
    """Skirt cone radius at height z (0.76 -> 0.19, 0.56 -> 0.34)."""
    return 0.34 - 0.15 * (z - 0.56) / 0.20


def carve(obj, pred_world):
    """Delete mesh vertices whose WORLD position satisfies pred_world."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    doomed = [v for v in bm.verts if pred_world(mw @ v.co)]
    bmesh.ops.delete(bm, geom=doomed, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()


def add_curve_obj(name, points, bevel_depth, mat, radii=None, bevel_resolution=4):
    """Bezier strand with optional per-point radius (taper), converted to mesh."""
    cu = bpy.data.curves.new(PREFIX + name + "Curve", "CURVE")
    cu.dimensions = "3D"
    cu.fill_mode = "FULL"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for i, bp in enumerate(sp.bezier_points):
        bp.co = points[i]
        if radii is not None:
            bp.radius = radii[i]
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    cu.bevel_depth = bevel_depth
    cu.bevel_resolution = bevel_resolution
    cu.resolution_u = 16
    cu.use_fill_caps = True
    obj = bpy.data.objects.new(PREFIX + name, cu)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    # Convert to mesh so GLB export is geometry-only.
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    smooth(obj)
    return obj


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def build_materials():
    return {
        "skin": make_clay_mat("Skin", SKIN, roughness=0.55, subsurface=0.12),
        "hair": make_clay_mat(
            "Hair", HAIR, roughness=0.5, subsurface=0.06, noise_scale=9.0, bump_strength=0.26
        ),
        "sweater": make_clay_mat(
            "Sweater", SWEATER, roughness=0.62, noise_scale=26.0, bump_strength=0.30
        ),
        "skirt": make_clay_mat(
            "Skirt", SKIRT, roughness=0.58, noise_scale=20.0, bump_strength=0.26
        ),
        "sock": make_clay_mat("Sock", SOCK, roughness=0.65),
        "shoe": make_clay_mat("Shoe", SHOE, roughness=0.45),
        "eye_white": make_clay_mat("EyeWhite", (0.97, 0.97, 0.96), roughness=0.18),
        "iris": make_clay_mat("Iris", EYE_BLUE, roughness=0.15),
        "pupil": make_clay_mat("Pupil", PUPIL, roughness=0.2),
        "brow": make_clay_mat("Brow", BROW, roughness=0.55),
        "mouth": make_clay_mat("Mouth", MOUTH, roughness=0.5),
        "cheek": make_clay_mat("Cheek", CHEEK, roughness=0.6, subsurface=0.1),
        "pedestal": make_clay_mat(
            "Pedestal", PEDESTAL, roughness=0.6, noise_scale=8.0, bump_strength=0.30
        ),
        "ground": make_clay_mat("Ground", GROUND, roughness=0.75),
        "gold": make_clay_mat(
            "Gold", GOLD, roughness=0.3, metallic=0.55, noise_scale=20.0, bump_strength=0.05
        ),
        "clip": make_clay_mat("Clip", CLIP, roughness=0.35),
        "heart": make_clay_mat("Heart", HEART, roughness=0.4),
    }


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
def build_pedestal(m):
    add_cyl("Pedestal", (0, 0, 0.09), 1.05, 0.18, m["pedestal"], verts=96)
    ped = bpy.context.active_object
    bev = ped.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.035
    bev.segments = 6
    # Rope trim around the top edge
    add_torus("PedestalTrim", (0, 0, 0.175), 1.02, 0.032, m["gold"], major_seg=96, minor_seg=16)
    # Embossed nameplate
    bpy.ops.object.text_add(location=(0, -1.057, 0.09), rotation=(math.radians(90), 0, 0))
    txt = bpy.context.active_object
    txt.name = PREFIX + "NameText"
    txt.data.body = "ANGELA"
    txt.data.size = 0.155
    txt.data.extrude = 0.014
    txt.data.align_x = "CENTER"
    txt.data.align_y = "CENTER"
    txt.data.materials.append(m["gold"])
    bpy.ops.object.select_all(action="DESELECT")
    txt.select_set(True)
    bpy.context.view_layer.objects.active = txt
    bpy.ops.object.convert(target="MESH")
    # Ground
    add_plane("Ground", (0, 0, 0.0), 30.0, m["ground"])


def build_legs_feet(m):
    for side, sx in (("L", -1), ("R", 1)):
        x = sx * 0.135
        # Shoe (bottom rests on pedestal top z=0.18)
        add_sphere(f"Shoe{side}", (x, -0.05, 0.27), (0.13, 0.21, 0.09), m["shoe"])
        # Lace strap arcing over the instep
        add_curve_obj(
            f"ShoeStrap{side}",
            [(x - 0.10, -0.16, 0.30), (x, -0.115, 0.356), (x + 0.10, -0.16, 0.30)],
            0.018,
            m["sock"],
            radii=[0.7, 1.0, 0.7],
        )
        # Skin leg: tapered curve (thigh -> ankle)
        add_curve_obj(
            f"Leg{side}",
            [(x, 0.0, 0.64), (x, 0.0, 0.48), (x, 0.01, 0.30)],
            0.064,
            m["skin"],
            radii=[1.0, 0.9, 0.78],
        )
        # Sock: curve over the leg, cuff tucked under the stripe
        add_curve_obj(
            f"Sock{side}",
            [(x, 0.0, 0.485), (x, 0.0, 0.39), (x, 0.005, 0.30)],
            0.072,
            m["sock"],
            radii=[1.0, 1.0, 1.02],
        )
        # Teal sock stripe
        add_torus(f"SockStripe{side}", (x, 0, 0.468), 0.071, 0.013, m["skirt"])


def build_torso_outfit(m):
    # Sweater body
    add_sphere("Torso", (0, 0, 0.94), (0.25, 0.20, 0.25), m["sweater"])
    # Skirt (top z 0.76 r 0.19, bottom z 0.56 r 0.34)
    add_cone("Skirt", (0, 0, 0.66), 0.34, 0.19, 0.20, m["skirt"])
    # Hem ring
    add_torus("SkirtHem", (0, 0, 0.565), 0.335, 0.026, m["skirt"])
    # Pleat ridges: tapered curve folds flowing waist -> hem
    for i in range(8):
        th = 2 * math.pi * i / 8.0
        dirx, diry = math.sin(th), -math.cos(th)
        pts = []
        for z in (0.75, 0.66, 0.578):
            r = skirt_r(z) + 0.012
            pts.append((r * dirx, r * diry, z))
        add_curve_obj(f"Pleat{i}", pts, 0.026, m["skirt"], radii=[0.4, 0.8, 1.0])
    # Fabric fold ridges on the sweater
    for side, sx in (("L", -1), ("R", 1)):
        pts = [
            (sx * 0.175, torso_y(sx * 0.175, 1.06) - 0.006, 1.06),
            (sx * 0.14, torso_y(sx * 0.14, 0.95) - 0.006, 0.95),
            (sx * 0.115, torso_y(sx * 0.115, 0.85) - 0.006, 0.85),
        ]
        add_curve_obj(f"Fold{side}", pts, 0.022, m["sweater"], radii=[0.3, 0.8, 0.15])
    # Collar
    add_torus("Collar", (0, 0, 1.14), 0.12, 0.05, m["sweater"], scale=(1, 0.9, 1))
    # Neck
    add_cyl("Neck", (0, 0, 1.18), 0.085, 0.16, m["skin"])
    # Hoodie pocket (rounded bump)
    add_sphere("Pocket", (0, -0.175, 0.85), (0.135, 0.05, 0.085), m["sweater"])
    # Drawstrings: gently curving tapered cords
    for sx in (-1, 1):
        add_curve_obj(
            f"Drawstring{'L' if sx < 0 else 'R'}",
            [(sx * 0.05, -0.150, 1.155), (sx * 0.055, -0.178, 1.08), (sx * 0.05, -0.192, 1.03)],
            0.009,
            m["sock"],
            radii=[1.0, 0.9, 0.75],
        )
        add_sphere(
            f"DrawstringTip{'L' if sx < 0 else 'R'}",
            (sx * 0.05, -0.195, 1.025),
            (0.014, 0.014, 0.014),
            m["gold"],
            seg=16,
            ring=8,
        )
    # Heart pendant on chest
    add_sphere("HeartL", (-0.026, -0.19, 1.075), (0.03, 0.018, 0.03), m["heart"], seg=24, ring=12)
    add_sphere("HeartR", (0.026, -0.19, 1.075), (0.03, 0.018, 0.03), m["heart"], seg=24, ring=12)
    add_cone("HeartTip", (0, -0.19, 1.043), 0.004, 0.04, 0.05, m["heart"], verts=24)


def build_arms(m):
    # Right arm raised in a wave — tapered sleeve strand
    add_curve_obj(
        "ArmR",
        [(0.21, 0.01, 1.04), (0.335, -0.03, 1.24), (0.465, -0.065, 1.435)],
        0.06,
        m["sweater"],
        radii=[1.0, 0.93, 0.8],
    )
    add_sphere("ShoulderR", (0.235, 0.0, 1.06), (0.08, 0.08, 0.08), m["sweater"])
    add_sphere("HandR", (0.47, -0.07, 1.44), (0.075, 0.07, 0.075), m["skin"])
    add_curve_obj(
        "ThumbR",
        [(0.45, -0.11, 1.46), (0.435, -0.14, 1.43)],
        0.028,
        m["skin"],
        radii=[1.0, 0.45],
    )
    add_curve_obj(
        "FingersR",
        [(0.44, -0.13, 1.475), (0.47, -0.142, 1.44), (0.495, -0.125, 1.41)],
        0.009,
        m["skin"],
        radii=[0.5, 1.0, 0.5],
    )
    # Left arm relaxed down — tapered sleeve strand
    add_curve_obj(
        "ArmL",
        [(-0.21, 0.01, 1.04), (-0.315, -0.02, 0.93), (-0.405, -0.05, 0.795)],
        0.06,
        m["sweater"],
        radii=[1.0, 0.93, 0.8],
    )
    add_sphere("ShoulderL", (-0.235, 0.0, 1.06), (0.08, 0.08, 0.08), m["sweater"])
    add_sphere("HandL", (-0.41, -0.05, 0.79), (0.075, 0.07, 0.075), m["skin"])
    add_curve_obj(
        "ThumbL",
        [(-0.39, -0.09, 0.81), (-0.375, -0.12, 0.785)],
        0.028,
        m["skin"],
        radii=[1.0, 0.45],
    )
    add_curve_obj(
        "FingersL",
        [(-0.435, -0.11, 0.815), (-0.41, -0.125, 0.785), (-0.385, -0.11, 0.76)],
        0.009,
        m["skin"],
        radii=[0.5, 1.0, 0.5],
    )


def build_head_face(m):
    add_sphere("Head", HEAD_C, (HEAD_R, HEAD_R, HEAD_R), m["skin"], seg=64, ring=32)
    # Eyes: layered sclera / iris / pupil / highlight (domed clay eyes)
    for side, sx in (("L", -1), ("R", 1)):
        x = sx * 0.15
        add_sphere(
            f"EyeWhite{side}",
            (x, -0.33, 1.53),
            (0.085, 0.05, 0.105),
            m["eye_white"],
            seg=32,
            ring=16,
        )
        add_sphere(
            f"Iris{side}", (x, -0.375, 1.53), (0.055, 0.02, 0.072), m["iris"], seg=32, ring=16
        )
        add_sphere(
            f"Pupil{side}", (x, -0.392, 1.53), (0.026, 0.012, 0.036), m["pupil"], seg=24, ring=12
        )
        add_sphere(
            f"EyeHighlight{side}",
            (x + sx * 0.018, -0.404, 1.56),
            (0.014, 0.008, 0.018),
            m["eye_white"],
            seg=16,
            ring=8,
        )
        # Brow: tapered curve arc (thick inner, thin outer)
        add_curve_obj(
            f"Brow{side}",
            [
                (sx * 0.07, front_y(sx * 0.07, 1.668) - 0.006, 1.668),
                (sx * 0.15, front_y(sx * 0.15, 1.682) - 0.006, 1.682),
                (sx * 0.23, front_y(sx * 0.23, 1.668) - 0.006, 1.668),
            ],
            0.018,
            m["brow"],
            radii=[0.5, 1.0, 0.2],
        )
    # Button nose
    add_sphere("Nose", (0, -0.375, 1.46), (0.03, 0.03, 0.028), m["skin"], seg=24, ring=12)
    # Smile: tapered curve arc (thin lifted corners, fuller middle)
    add_curve_obj(
        "Mouth",
        [(-0.055, -0.340, 1.378), (0.0, -0.350, 1.343), (0.055, -0.340, 1.378)],
        0.015,
        m["mouth"],
        radii=[0.4, 1.0, 0.4],
    )
    # Rosy cheeks
    for side, sx in (("L", -1), ("R", 1)):
        add_sphere(
            f"Cheek{side}",
            (sx * 0.245, -0.288, 1.42),
            (0.07, 0.015, 0.045),
            m["cheek"],
            seg=24,
            ring=12,
        )


def build_hair(m):
    # Scalp cap: head shell with the face region carved open
    cap = add_sphere("HairCap", HEAD_C, (0.425, 0.425, 0.425), m["hair"], seg=64, ring=32)
    # Open only the face plate + a narrow under-chin band:
    #   rule_face: front face oval (covered by bangs + temple + side locks)
    #   rule_chin: hair directly between chin and collar, center only |x|<0.18
    # Side shells (|x|>=0.18) stay intact so no hard-edged hole is ever
    # visible from the side view.
    carve(
        cap,
        lambda co: (
            (co.y < -0.16 and abs(co.x) < 0.33 and 1.18 < co.z < 1.70)
            or (co.y < 0.08 and abs(co.x) < 0.18 and co.z < 1.42)
        ),
    )
    sol = cap.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.03
    sol.offset = -1.0
    # --- Bangs: 11 tapered strands lying over the forehead ---
    for i in range(11):
        x = -0.30 + 0.06 * i
        tip_z = 1.62 - 0.07 * (1.0 - abs(x) / 0.30) + 0.012 * ((i % 3) - 1)
        pts = [
            (x * 0.40, -0.10, 1.86),
            (x * 0.75, front_y(x * 0.75, 1.74) - 0.01, 1.74),
            (x, front_y(x, tip_z) - 0.015, tip_z),
        ]
        add_curve_obj(f"Bang{i}", pts, 0.05, m["hair"], radii=[1.0, 0.9, 0.08])

    # --- Temple + side locks: 4 strands per side ---
    # (root inside the cap; first two lie on the face edge, outer two hang free)
    lock_specs = [
        (0.24, 1.80, 0.305, 1.66, 0.33, 1.44, True),
        (0.27, 1.78, 0.345, 1.58, 0.355, 1.34, True),
        (0.30, 1.76, 0.40, 1.52, 0.41, 1.26, False),
        (0.28, 1.74, 0.42, 1.46, 0.42, 1.34, False),
    ]
    for side, sx in (("L", -1), ("R", 1)):
        for j, (rx, rz, mx, mz, tx, tz, on_face) in enumerate(lock_specs):
            if on_face:
                my = front_y(sx * mx, mz) - 0.015
                ty = front_y(sx * tx, tz) - 0.02
            else:
                my, ty = -0.20, -0.24
            pts = [(sx * rx, -0.06, rz), (sx * mx, my, mz), (sx * tx, ty, tz)]
            add_curve_obj(f"Lock{side}{j}", pts, 0.055, m["hair"], radii=[1.0, 0.85, 0.08])

    # Neck-side hair patches: hide the solidify rim of the carved face plate
    # (visible as a dark strand from the front) and seal the jaw/neck gap
    # seen from the side.
    for side, sx in (("L", -1), ("R", 1)):
        add_sphere(
            f"NeckHair{side}",
            (sx * 0.24, -0.09, 1.30),
            (0.10, 0.09, 0.16),
            m["hair"],
            seg=32,
            ring=16,
            rot=(0, math.radians(sx * 5), 0),
        )

    # --- Back bob: 9 tapered strands flowing crown -> nape (pointed tips) ---
    for i in range(9):
        x = -0.32 + 0.08 * i
        tip_z = 1.34 - 0.12 * (1.0 - abs(x) / 0.32) + 0.015 * ((i % 3) - 1)
        pts = [
            (x * 0.35, 0.10, 1.86),
            (x * 0.85, back_y(x * 0.85, 1.55, 0.425) - 0.01, 1.55),
            (x, back_y(x, tip_z, 0.425) - 0.01, tip_z),
        ]
        add_curve_obj(f"BackHair{i}", pts, 0.06, m["hair"], radii=[1.0, 0.95, 0.1])

    # Ahoge (curl on top), tapered to a point
    add_curve_obj(
        "Ahoge",
        [(0, 0.02, 1.94), (0.05, 0.0, 2.10), (0.18, -0.05, 2.02)],
        0.03,
        m["hair"],
        radii=[1.0, 0.8, 0.05],
    )
    # Star-ish hair clip (round candy button on right bangs)
    add_sphere("HairClip", (0.30, -0.335, 1.66), (0.05, 0.025, 0.05), m["clip"], seg=24, ring=12)


def build_lights_camera(m):
    sc = scene()
    # World
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.95, 0.93, 0.90, 1.0)
    bg.inputs[1].default_value = 0.30

    lights = [
        ("Key", (-3.0, -4.0, 4.0), 480, 3.0),
        ("Fill", (3.5, -2.5, 2.0), 150, 4.0),
        ("Rim", (1.5, 3.5, 3.0), 280, 2.0),
    ]
    for name, loc, energy, size in lights:
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.active_object
        lamp.name = PREFIX + "Light" + name
        lamp.data.energy = energy
        lamp.data.size = size
        aim(lamp, (0, 0, 1.1))

    bpy.ops.object.camera_add(location=(0, -4.0, 1.5))
    cam = bpy.context.active_object
    cam.name = PREFIX + "Camera"
    cam.data.lens = 45
    aim(cam, (0, 0, 1.0))
    sc.camera = cam


def parent_to_root():
    root = bpy.data.objects.new(PREFIX + "Root", None)
    bpy.context.scene.collection.objects.link(root)
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(PREFIX) and obj is not root:
            obj.parent = root
    return root


# ---------------------------------------------------------------------------
# Render / export
# ---------------------------------------------------------------------------
def setup_render():
    sc = scene()
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 192
    # This Blender build has no OpenImageDenoiser — compensate with samples.
    sc.cycles.use_denoising = False
    sc.render.resolution_x = 700
    sc.render.resolution_y = 900
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        sc.view_settings.exposure = -0.6
    except (TypeError, ValueError):
        pass  # keep default if Standard unavailable


VIEWS = [
    ("front", (0.0, -4.0, 1.5)),
    ("three_quarter", (2.8, -2.8, 1.7)),
    ("side", (4.0, 0.0, 1.5)),
    ("back", (0.0, 4.0, 1.5)),
]


def render_views():
    sc = scene()
    cam = bpy.data.objects[PREFIX + "Camera"]
    for name, loc in VIEWS:
        cam.location = loc
        aim(cam, (0, 0, 1.0))
        path = os.path.join(RENDER_DIR, f"preview_{name}.png")
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        size = os.path.getsize(path)
        print(f"[render] {name} -> {path} ({size} bytes)")
        if size < 10_000:
            raise RuntimeError(f"Render output suspiciously small: {path}")


def export_glb():
    bpy.ops.object.select_all(action="DESELECT")
    count = 0
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(PREFIX):
            obj.select_set(True)
            count += 1
    if count < 20:
        raise RuntimeError(f"Only {count} model objects selected for GLB")
    bpy.context.view_layer.objects.active = bpy.data.objects[PREFIX + "Root"]
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
    )
    print(f"[export] GLB -> {GLB_PATH} ({os.path.getsize(GLB_PATH)} bytes)")


def main():
    os.makedirs(RENDER_DIR, exist_ok=True)
    clear_scene()
    m = build_materials()
    build_pedestal(m)
    build_legs_feet(m)
    build_torso_outfit(m)
    build_arms(m)
    build_head_face(m)
    build_hair(m)
    build_lights_camera(m)
    parent_to_root()
    setup_render()

    n_mesh = sum(1 for o in bpy.context.scene.objects if o.type == "MESH")
    n_mat = len(bpy.data.materials)
    print(f"[build] meshes={n_mesh} materials={n_mat}")
    if n_mesh < 40:
        raise RuntimeError(f"Model too simple/failed: only {n_mesh} meshes")

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"[save] BLEND -> {BLEND_PATH} ({os.path.getsize(BLEND_PATH)} bytes)")

    export_glb()
    render_views()

    print(
        f"ANGELA_CLAY_DONE meshes={n_mesh} materials={n_mat} "
        f"blend={os.path.getsize(BLEND_PATH)} "
        f"glb={os.path.getsize(GLB_PATH)}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
