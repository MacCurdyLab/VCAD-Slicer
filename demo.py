import json
import time
import slicer
import pyvcad as pv
import outline_slicer
import demo_objects as do
import gcode_writer as gw

# Paths
settings_path = "demos/vase_continuous/vase_continuous_mixing_36_regions.json"

# Load json into dictionary
with open(settings_path, 'r') as file:
    print("Loading settings from {}".format(settings_path))
    settings = json.load(file)

output_file = "output/" + settings["object_settings"]["name"] + ".gcode"

voxel_size = pv.Vec3(settings["object_settings"]["voxel_size"][0], settings["object_settings"]["voxel_size"][1], settings["object_settings"]["voxel_size"][2])
min = pv.Vec3(settings["object_settings"]["min"][0], settings["object_settings"]["min"][1], settings["object_settings"]["min"][2])
max = pv.Vec3(settings["object_settings"]["max"][0], settings["object_settings"]["max"][1], settings["object_settings"]["max"][2])

# Object to slice
root = do.parse_from_file(voxel_size,
                          settings["object_settings"]["vcad_script_path"],
                          settings["object_settings"]["vcad_config_path"])

# Report actual VCAD bounding box
[actual_min, actual_max] = root.bounding_box()
print("Actual VCAD bounding box: ")
print("Min: ({},{},{})".format(actual_min.x, actual_min.y, actual_min.z))
print("Max: ({},{},{})".format(actual_max.x, actual_max.y, actual_max.z))

def generate_linear_ranges(num_ranges, min, max):
    ranges = []
    step = (max - min) / num_ranges
    for i in range(num_ranges):
        ranges.append((min + i * step, min + (i + 1) * step))
    return ranges


if root is None:
    print("Error parsing vcad script. Quitting...")
    exit()

# Compute the total number of voxels based on the dimensions of the OpenVCAD object and the voxel size
x_dim = int((max.x - min.x) / voxel_size.x)
y_dim = int((max.y - min.y) / voxel_size.y)
z_dim = int((max.z - min.z) / voxel_size.z)
total_voxels = x_dim * y_dim * z_dim

# Print info about the OpenVCAD object
print("Starting slice of OpenVCAD object with dimensions: ")
print("Min: ({},{},{})".format(min.x, min.y, min.z))
print("Max: ({},{},{})".format(max.x, max.y, max.z))
print("Voxel size: ({},{},{})".format(voxel_size.x, voxel_size.y, voxel_size.z))
print("With total number of voxels: {}".format(total_voxels))
print("\nSlicing...")

# Make gradient ranges
num_regions = settings["gradient_settings"]["num_regions"]
ranges = generate_linear_ranges(num_regions, 0.0, 1.0)

# Print ranges
print("Gradient ranges: ")
for r in ranges:
    print("\t{}".format(r))

# Start timer for slicing
start = time.time()

# Check if s["slicer_settings"]["mode"] mode is present
if "mode" not in settings["slicer_settings"]:
    print("Error: No slicer mode specified. Please use 'outline' or 'cutting'")
    exit()

if settings["slicer_settings"]["mode"] == "outline":
    print("Using outline slicer")
    slicer = outline_slicer.OutlineSlicer(root, min, max, voxel_size, settings)
    slicer.slice(ranges=ranges)
elif settings["slicer_settings"]["mode"] == "cutting":
    print("Using cutting slicer")
    slicer = slicer.Slicer(root, min, max, voxel_size, settings)
    slicer.slice(ranges=ranges)
else:
    print("Error: Unknown slicer mode. Please use 'outline' or 'cutting'")
    exit()

# Optional: visualize the paths
visualize_paths = settings["slicer_settings"]["visualize_paths"]
if visualize_paths:
    pmin = settings["printer_settings"]["dimensions"]["min"]
    pmax = settings["printer_settings"]["dimensions"]["max"]
    printer_bounds = [pmin[0], pmin[1], pmax[0], pmax[1]]
    slicer.visualize_paths(printer_bounds, "output/overlap/render.png")

# Write the gcode
gcode_writer = gw.GCodeWriter(output_file, settings)
slicer.write_gcode(gcode_writer)

print("GCode written to {}".format(output_file))
print("Done! Slicing took {} seconds".format(time.time() - start))
