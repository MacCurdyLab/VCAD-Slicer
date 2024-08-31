import json
import time
import slicer
import outline_slicer
import demo_objects as do
import gcode_writer as gw

import os
plugin_path = os.path.join(os.path.dirname(__file__), "plugins")
os.environ["QT_PLUGIN_PATH"] = plugin_path

# Paths
settings_path = "settings/offset_demo.json"

# Load json into dictionary
with open(settings_path, 'r') as file:
    print("Loading settings from {}".format(settings_path))
    settings = json.load(file)

output_file = "output/" + settings["object_settings"]["name"] + ".gcode"

# Object to slice
meta, root = do.parse_from_file(settings["object_settings"]["vcad_script_path"],
                                settings["object_settings"]["vcad_config_path"])

def generate_linear_ranges(num_ranges, min, max):
    ranges = []
    step = (max - min) / num_ranges
    for i in range(num_ranges):
        ranges.append((min + i * step, min + (i + 1) * step))
    return ranges


if meta is None or root is None:
    print("Error parsing vcad script. Quitting...")
    exit()

# Compute the total number of voxels based on the dimensions of the OpenVCAD object and the voxel size
x_dim = int((meta.max.x - meta.min.x) / meta.voxel_size.x)
y_dim = int((meta.max.y - meta.min.y) / meta.voxel_size.y)
z_dim = int((meta.max.z - meta.min.z) / meta.voxel_size.z)
total_voxels = x_dim * y_dim * z_dim

# Print info about the OpenVCAD object
print("Starting slice of OpenVCAD object with dimensions: ")
print("Min: ({},{},{})".format(meta.min.x, meta.min.y, meta.min.z))
print("Max: ({},{},{})".format(meta.max.x, meta.max.y, meta.max.z))
print("Voxel size: ({},{},{})".format(meta.voxel_size.x, meta.voxel_size.y, meta.voxel_size.z))
print("With total number of voxels: {}".format(total_voxels))
print("\nSlicing...")

# Make gradient ranges
num_regions = settings["gradient_settings"]["num_regions"]
ranges = generate_linear_ranges(num_regions, 0.0, 1.0)

# Start timer for slicing
start = time.time()

# Perform slice
# slicer = slicer.Slicer(root, meta.min, meta.max, meta.voxel_size, settings)
# slicer.slice(ranges=ranges)

slicer = outline_slicer.OutlineSlicer(root, meta.min, meta.max, meta.voxel_size, settings)
slicer.slice(ranges=ranges)

# Optional: visualize the paths
visualize_paths = settings["slicer_settings"]["visualize_paths"]
if visualize_paths:
    pmin = settings["printer_settings"]["dimensions"]["min"]
    pmax = settings["printer_settings"]["dimensions"]["max"]
    printer_bounds = [pmin[0], pmin[1], pmax[0], pmax[1]]
    slicer.visualize_paths(printer_bounds)

# Write the gcode
gcode_writer = gw.GCodeWriter(output_file, settings)
slicer.write_gcode(gcode_writer)

print("GCode written to {}".format(output_file))
print("Done! Slicing took {} seconds".format(time.time() - start))

