import demo_objects as do
from libvcad import pyvcad as pv
from libvcad import pyvcadviz as viz
import numpy as np

import os
plugin_path = os.path.join(os.path.dirname(__file__), "plugins")
os.environ["QT_PLUGIN_PATH"] = plugin_path

meta = pv.Meta()
meta.min = pv.Vec3(-5, -5, -5)
meta.max = pv.Vec3(5, 5, 5)
meta.voxel_size = pv.Vec3(0.25, 0.25, 0.25)

# Print the total number of voxels
x_dim = int((meta.max.x - meta.min.x) / meta.voxel_size.x)
y_dim = int((meta.max.y - meta.min.y) / meta.voxel_size.y)
z_dim = int((meta.max.z - meta.min.z) / meta.voxel_size.z)
total_voxels = x_dim * y_dim * z_dim
print("Total number of voxels: {}".format(total_voxels))

config_path = "vcad_configs/testing.json"


meta = pv.Meta()
meta.min = pv.Vec3(-5, -5, -5)
meta.max = pv.Vec3(5, 5, 5)
meta.voxel_size = pv.Vec3(0.25, 0.25, 0.25)

cube = pv.RectPrism(pv.Vec3(0,0,0), pv.Vec3(5,5,5), 1)

def func_a(xyz, cyl, sphere):
    return 0.5;

def func_b(xyz, cyl, sphere):
    return 0.5;

# fgrade = pv.FGrade([func_a, func_b], [1,2], True)
# fgrade.set_child(cube)
# root = fgrade

# res = root.distribution(0,0,0)
# print(res)
def func_c(x, y, z, rho, phic, r, theta, phis):
    return x**2 + y**2 + z**2 - 1

root = pv.Function(func_c, 1)

implicit = pv.Function(func_c, 1)
string_version = pv.Function("x^2+y^2+z^2-1", 1)
string_version.prepare(meta.voxel_size, 1, 1)

import time


def benchmark_evaluate(root, num_samples):
    start_time = time.time()

    for _ in range(num_samples):
        random_x = np.random.uniform(meta.min.x, meta.max.x)
        random_y = np.random.uniform(meta.min.y, meta.max.y)
        random_z = np.random.uniform(meta.min.z, meta.max.z)
        root.evaluate(random_x, random_y, random_z)

    end_time = time.time()
    elapsed_time = end_time - start_time
    samples_per_second = num_samples / elapsed_time

    print(f"Samples per second: {samples_per_second}")
    return samples_per_second

viz.BenchmarkTemp(100000000, meta.min, meta.max, string_version, implicit)

# # Example usage
# num_samples = 100000
# print("Evaluating implicit")
# benchmark_evaluate(root, num_samples)
# print("Evaluating string")
# benchmark_evaluate(string_version, num_samples)


viz.Render(config_path, meta.min, meta.max, meta.voxel_size, implicit, True)
