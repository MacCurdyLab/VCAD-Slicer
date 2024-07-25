from libvcad import pyvcad as pv

def parse_from_file(file_path, config_path):
    # Load the vcad script text from the file
    with open(file_path, "r") as vcad_file:
        vcad_script = vcad_file.read()
        # Parse the vcad script
        try:
            [meta, root] = pv.parse_vcad_text(vcad_script, config_path)
            root.prepare()
            return meta, root
        except Exception as e:
            print("Error parsing vcad script: ", e)
            return None, None

# Bar with linear gradient
def linear_gradient_bar():
    meta = pv.Meta()
    meta.min = pv.Vec3(-10, -10, -1)
    meta.max = pv.Vec3(10, 10, 1)
    meta.voxel_size = pv.Vec3(0.1, 0.1, 0.1)

    r = pv.RectPrism(pv.Vec3(0, 0, 0), pv.Vec3(16, 8, 3), 1)
    fg = pv.FGrade(["(x/16)+0.5"], [1], True)
    fg.set_child(r)
    root = fg
    root.prepare()

    return meta, root


def linear_gradient_bar_with_big_hole():
    meta = pv.Meta()
    meta.min = pv.Vec3(-10, -10, -1)
    meta.max = pv.Vec3(10, 10, 1)
    meta.voxel_size = pv.Vec3(0.1, 0.1, 0.1)

    r = pv.RectPrism(pv.Vec3(0, 0, 0), pv.Vec3(16, 8, 3), 1)
    hole = pv.Sphere(pv.Vec3(0, 0, 0), 5, 1)
    diff = pv.Difference()
    diff.set_left(r)
    diff.set_right(hole)
    fg = pv.FGrade(["(x/16)+0.5"], [1], True)
    fg.set_child(diff)
    root = fg
    root.prepare()

    return meta, root


def linear_gradient_bar_with_hole():
    meta = pv.Meta()
    meta.min = pv.Vec3(-10, -10, -1)
    meta.max = pv.Vec3(10, 10, 1)
    meta.voxel_size = pv.Vec3(0.5, 0.5, 0.5)

    r = pv.RectPrism(pv.Vec3(0, 0, 0), pv.Vec3(16, 8, 3), 1)
    hole = pv.Sphere(pv.Vec3(0, 0, 0), 2, 1)
    diff = pv.Difference()
    diff.set_left(r)
    diff.set_right(hole)
    fg = pv.FGrade(["(x/16)+0.5"], [1], True)
    fg.set_child(diff)
    root = fg
    root.prepare()

    return meta, root


# Bar with v-shaped gradient
def v_gradient_bar():
    meta = pv.Meta()
    meta.min = pv.Vec3(-10, -10, -1)
    meta.max = pv.Vec3(10, 10, 1)
    meta.voxel_size = pv.Vec3(0.1, 0.1, 0.1)

    r = pv.RectPrism(pv.Vec3(0, 0, 0), pv.Vec3(16, 8, 3), 1)
    fg = pv.FGrade(["abs(x/8)"], [1], True)
    fg.set_child(r)
    root = fg
    root.prepare()

    return meta, root


def sphere():
    meta = pv.Meta()
    meta.min = pv.Vec3(-10, -10, -10)
    meta.max = pv.Vec3(10, 10, 10)
    meta.voxel_size = pv.Vec3(0.1, 0.1, 0.1)

    s = pv.Sphere(pv.Vec3(0, 0, 0), 5, 1)
    fg = pv.FGrade(["r / 10"], [1], True)
    fg.set_child(s)
    root = fg
    root.prepare()

    return meta, root


# Double difference object
def double_diff_bar():
    meta = pv.Meta()
    meta.min = pv.Vec3(-10, -10, -1)
    meta.max = pv.Vec3(10, 10, 1)
    meta.voxel_size = pv.Vec3(0.1, 0.1, 0.1)

    r1 = pv.RectPrism(pv.Vec3(0, 0, 0), pv.Vec3(16, 8, 3), 1)
    r2 = pv.RectPrism(pv.Vec3(0, 0, 0), pv.Vec3(10, 4, 3), 1)
    r3 = pv.RectPrism(pv.Vec3(0, 0, 0), pv.Vec3(2, 2, 3), 1)
    diff = pv.Difference()
    diff.set_left(r2)
    diff.set_right(r3)
    diff2 = pv.Difference()
    diff2.set_left(r1)
    diff2.set_right(diff)
    fg = pv.FGrade(["(x/16)+0.5"], [1], True)
    fg.set_child(diff2)
    root = fg
    root.prepare()

    return meta, root