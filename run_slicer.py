import json
import time
import slicer
import pyvcad as pv
import outline_slicer
import gcode_writer as gw

# STARTING POINT: Import the object to slice
from examples.linear_gradient_prusa_mk4s.linear_gradient_vcad_object import vcad_object, materials
settings_path = "examples/linear_gradient_prusa_mk4s/settings.json"

# The rest of the code handles the slicing
# Load json into dictionary
with open(settings_path, 'r') as file:
    print("Loading settings from {}".format(settings_path))
    settings = json.load(file)

output_file = "output/" + settings["object_settings"]["name"] + ".gcode"

voxel_size = pv.Vec3(settings["object_settings"]["voxel_size"][0], settings["object_settings"]["voxel_size"][1], settings["object_settings"]["voxel_size"][2])

# Report actual VCAD bounding box
[bbox_min, bbox_max] = vcad_object.bounding_box()

if vcad_object is None:
    print("Error with VCAD Object. Make sure it is valid. Quitting...")
    exit()

# Compute the total number of voxels based on the dimensions of the OpenVCAD object and the voxel size
x_dim = int((bbox_max.x - bbox_min.x) / voxel_size.x)
y_dim = int((bbox_max.y - bbox_min.y) / voxel_size.y)
z_dim = int((bbox_max.z - bbox_min.z) / voxel_size.z)
total_voxels = x_dim * y_dim * z_dim

# Print info about the OpenVCAD object
print("Starting slice of OpenVCAD object with dimensions: ")
print("Bounding Box Min: ({},{},{})".format(bbox_min.x, bbox_min.y, bbox_min.z))
print("Bounding Box Max: ({},{},{})".format(bbox_max.x, bbox_max.y, bbox_max.z))
print("Voxel size: ({},{},{})".format(voxel_size.x, voxel_size.y, voxel_size.z))
print("With total number of voxels: {}".format(total_voxels))
print("\nSlicing...")

# Make gradient ranges
def generate_linear_ranges(num_ranges, min, max):
    ranges = []
    step = (max - min) / num_ranges
    for i in range(num_ranges):
        ranges.append((min + i * step, min + (i + 1) * step))
    return ranges

num_regions = settings["gradient_settings"]["num_regions"]
ranges = generate_linear_ranges(num_regions, 0.0, 1.0)
print("Gradient ranges: ") # Print ranges
for r in ranges:
    print("\t{}".format(r))

# Start timer for slicing
start = time.time()

# Check if settings["slicer_settings"]["mode"] mode is present
if "mode" not in settings["slicer_settings"]:
    print("Error: No slicer mode specified. Please use 'outline' or 'cutting'")
    exit()

# Pick which slicer to use (Cutting is strategy 1 in the paper, and Outline is strategy 2)
if settings["slicer_settings"]["mode"] == "outline":
    print("Using outline slicer")
    slicer = outline_slicer.OutlineSlicer(vcad_object, bbox_min, bbox_max, voxel_size, settings)
    slicer.slice(ranges=ranges)
elif settings["slicer_settings"]["mode"] == "cutting":
    print("Using cutting slicer")
    slicer = slicer.Slicer(vcad_object, bbox_min, bbox_max, voxel_size, settings)
    slicer.slice(ranges=ranges)
else:
    print("Error: Unknown slicer mode. Please use 'outline' or 'cutting'")
    exit()

# Write the gcode
gcode_writer = gw.GCodeWriter(output_file, settings)
slicer.write_gcode(gcode_writer)

print("GCode written to {}".format(output_file))
print("Done! Slicing took {} seconds".format(time.time() - start))
