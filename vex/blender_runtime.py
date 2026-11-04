"""Trusted Blender-side interpreter; input is validated by the parent application.

Run only with Blender's embedded Python. No user-supplied code is evaluated.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def material(color):
    rgb = tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))
    mat = bpy.data.materials.get(color)
    if not mat:
        mat = bpy.data.materials.new(color)
        mat.diffuse_color = (*rgb, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*rgb, 1)
        shader.inputs["Metallic"].default_value = .25
        shader.inputs["Roughness"].default_value = .4
    return mat


def mesh(parent, name, pos, dimensions, color, sphere=False):
    if sphere:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=pos)
        obj = bpy.context.object
        obj.scale = tuple(v / 2 for v in dimensions)
    else:
        bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
        obj = bpy.context.object
        obj.scale = dimensions
        bevel = obj.modifiers.new("Soft edges", "BEVEL")
        bevel.width = .06
        bevel.segments = 2
    obj.name = name
    obj.parent = parent
    obj.data.materials.append(material(color))
    return obj


def build(node):
    root = bpy.data.objects.new(node["id"], None)
    bpy.context.collection.objects.link(root)
    w, h = node["width"] / 100, node["height"] / 100
    color, accent = node["color"], node["stroke"]
    kind = node["kind"]
    if kind == "robot":
        mesh(root, "body", (0, 0, 0), (w*.5, w*.4, h*.36), color)
        mesh(root, "head", (0, 0, h*.31), (w*.68, w*.5, h*.28), color)
        for side in (-1, 1):
            mesh(root, "eye", (side*w*.13, -w*.27, h*.33), (w*.1, .05, h*.07), accent, True)
            mesh(root, "arm", (side*w*.38, 0, -h*.03), (w*.13, w*.17, h*.3), color)
            mesh(root, "leg", (side*w*.15, 0, -h*.32), (w*.18, w*.23, h*.25), color)
    elif kind == "tower":
        mesh(root, "tower", (0, 0, 0), (w*.55, w*.55, h), color)
        mesh(root, "beacon", (0, 0, h*.5), (w, w, w), accent, True)
        bpy.ops.object.light_add(type="POINT", location=(0, -w, h*.5))
        light = bpy.context.object
        light.parent = root
        light.data.energy = 80
        light.data.color = (.5, .8, 1)
    elif kind == "building":
        mesh(root, "building", (0, 0, 0), (w, w, h), color)
        for row in range(1, 6):
            for col in (-1, 0, 1):
                mesh(root, "window", (col*w*.25, -w*.51, -h*.5+row*h/7), (.08, .02, .12), accent)
    elif kind == "text":
        curve = bpy.data.curves.new("Text", "FONT")
        curve.body = node["text"]
        curve.align_x = "CENTER"
        curve.size = h*.6
        curve.extrude = .01
        obj = bpy.data.objects.new("Text", curve)
        bpy.context.collection.objects.link(obj)
        obj.parent = root
        obj.rotation_euler.x = math.pi / 2
        curve.materials.append(material(color))
    elif kind == "polygon":
        data = bpy.data.meshes.new("Polygon")
        data.from_pydata([(x/100, 0, -y/100) for x, y in node["points"]], [], [list(range(len(node["points"])) )])
        obj = bpy.data.objects.new("Polygon", data)
        bpy.context.collection.objects.link(obj)
        obj.parent = root
        data.materials.append(material(color))
    elif kind != "group":
        mesh(root, kind, (0, 0, 0), (w, max(.03, min(w, h)*.25), h), color, kind == "ellipse")
    return root


def evaluate(keys, time):
    if time <= keys[0]["time"]:
        return keys[0]["value"]
    for a, b in zip(keys, keys[1:]):
        if time <= b["time"]:
            u = (time-a["time"])/(b["time"]-a["time"])
            if b["easing"] == "smooth":
                u = u*u*(3-2*u)
            elif b["easing"] == "in":
                u *= u
            elif b["easing"] == "out":
                u = 1-(1-u)**2
            return a["value"]+(b["value"]-a["value"])*u
    return keys[-1]["value"]


def main():
    source, output = map(Path, sys.argv[sys.argv.index("--")+1:])
    settings = json.loads(source.read_text(encoding="utf-8"))
    scene = settings["scene"]
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    world = bpy.context.scene
    world.render.engine = "BLENDER_EEVEE_NEXT"
    world.render.resolution_x = settings["width"]
    world.render.resolution_y = settings["height"]
    world.render.resolution_percentage = 100
    world.render.image_settings.file_format = "PNG"
    world.world.color = (.045, .05, .09)
    roots = {node["id"]: build(node) for node in scene["nodes"]}
    for node in scene["nodes"]:
        if node["parent"]:
            roots[node["id"]].parent = roots[node["parent"]]
    mesh(None, "Floor", (0, 0, -.9), (25, 20, .2), "#22273c")
    bpy.ops.object.light_add(type="AREA", location=(1, -4, 8))
    bpy.context.object.data.energy = 1500
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 8
    bpy.ops.object.camera_add(location=(7, -15, 7))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0, 0, 1.5))-camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 15 / scene["camera"]["zoom"]
    world.camera = camera
    frames = math.ceil(scene["duration"]*settings["fps"])
    output.mkdir(parents=True, exist_ok=True)
    for index in range(frames):
        time = index/settings["fps"]
        for node in scene["nodes"]:
            values = {key: node[key] for key in ("x", "y", "rotation", "scale", "opacity")}
            for track in node["tracks"]:
                values[track["property"]] = evaluate(track["keys"], time)
            root = roots[node["id"]]
            offset_x, offset_y = (0, 0) if node["parent"] else (640, 560)
            root.location = ((values["x"]-offset_x)/100, node["layer"]*.05, (offset_y-values["y"])/100)
            root.scale = (values["scale"],)*3
            root.rotation_euler.y = math.radians(values["rotation"])
            root.hide_render = values["opacity"] <= 0
        camera.location.x = 7 + (scene["camera"]["x"]+scene["camera"]["pan_x"]*time/scene["duration"])/100
        world.render.filepath = str(output / f"{index:06}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
