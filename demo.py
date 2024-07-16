import time
import slicer
import demo_objects as do
import gcode_writer as gw
from libvcad import pyvcad as pv

# Object to slice
# meta, root = do.double_diff_bar()
meta, root = do.parse_from_file("test.vcad")

# Output
output_file = "output.gcode"

# Settings for slicing
layer_height = 0.2
filament_diameter = 1.75
bead_width = 0.4
num_walls = 12
infill_density_percentage = 0.90
num_regions = 4
center_point = pv.Point2(175.0, 100.0)
visualize_paths = False

# Purge tower settings
min_coord = pv.Point2(-50, 15.0)
max_coord = pv.Point2(50.0, 200.0)
x_size = 22.0
y_size = 45.0
x_spacing = x_size + 4
y_spacing = y_size + 4


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
print("\nUsing the following slicing parameters:")
print("Layer height: {}".format(layer_height))
print("Bead width: {}".format(bead_width))
print("Number of walls: {}".format(num_walls))
print("Infill density: {}%".format(infill_density_percentage))
print("\nSlicing...")

# Make gradient ranges
# ranges = [(0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0)]
ranges = generate_linear_ranges(num_regions, 0.0, 1.0)

# Start timer for slicing
start = time.time()

# Perform slice
slicer = slicer.Slicer(root, meta.min, meta.max, meta.voxel_size, center_point=center_point,
                       purge_min=min_coord, purge_max=max_coord,
                       purge_tower_x_spacing=x_spacing, purge_tower_y_spacing=y_spacing,
                       purge_tower_x_size=x_size, purge_tower_y_size=y_size)
slicer.slice(ranges=ranges,
             layer_height=layer_height, bead_width=bead_width,
             num_walls=num_walls, infill_density=infill_density_percentage)

# Optional: visualize the paths
if visualize_paths:
    slicer.visualize_paths()

# Write the gcode
gcode_writer = gw.GCodeWriter(output_file, filament_diameter=filament_diameter, layer_height=layer_height,
                              bead_width=bead_width, flow_rate=1.0)
slicer.write_gcode(gcode_writer)

print("GCode written to {}".format(output_file))
print("Done! Slicing took {} seconds".format(time.time() - start))

