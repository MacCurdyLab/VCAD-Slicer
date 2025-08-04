import json
import time
import slicer
import pyvcad as pv
import outline_slicer
import demo_objects as do
import gcode_writer as gw

def slice_demo(settings_path, name, setting_override=None):
    # Load json into dictionary
    with open(settings_path, 'r') as file:
        print("Loading settings from {}".format(settings_path))
        settings = json.load(file)

    def deep_update(original, override):
        for key, value in override.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                deep_update(original[key], value)
            else:
                original[key] = value

    if setting_override is not None:
        print("Overriding settings with {}".format(setting_override))
        deep_update(settings, setting_override)

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
        slcr = outline_slicer.OutlineSlicer(root, min, max, voxel_size, settings)
        slcr.slice(ranges=ranges)
    elif settings["slicer_settings"]["mode"] == "cutting":
        print("Using cutting slicer")
        slcr = slicer.Slicer(root, min, max, voxel_size, settings)
        slcr.slice(ranges=ranges)
    else:
        print("Error: Unknown slicer mode. Please use 'outline' or 'cutting'")
        exit()

    # Optional: visualize the paths
    visualize_paths = settings["slicer_settings"]["visualize_paths"]
    if visualize_paths:
        pmin = settings["printer_settings"]["dimensions"]["min"]
        pmax = settings["printer_settings"]["dimensions"]["max"]
        printer_bounds = [pmin[0], pmin[1], pmax[0], pmax[1]]
        slcr.visualize_paths(printer_bounds, name, figsize=(24, 24))

    # Write the gcode
    gcode_writer = gw.GCodeWriter(output_file, settings)
    slcr.write_gcode(gcode_writer)

    print("GCode written to {}".format(output_file))
    print("Done! Slicing took {} seconds".format(time.time() - start))

directory = "demos/dogbone/xl/strat_1/zipper/"

# Iterate over all the json files in the directory recursively
import os
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith(".json"):
            settings_path = os.path.join(root, file)
            name = os.path.join("output", root.replace(directory, ""), file.replace(".json", ".gcode"))
            print(f"Slicing {settings_path} to {name}")
            slice_demo(settings_path, name, setting_override={"object_settings": {"vcad_script_path": "demos/dogbone/5_dogbones.vcad"}})


# slice_demo("demos/vase_slice/smooth/strat_1/2_region.json", "output/smooth/strat_1/2_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/3_region.json", "output/smooth/strat_1/3_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/4_region.json", "output/smooth/strat_1/4_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/5_region.json", "output/smooth/strat_1/5_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/6_region.json", "output/smooth/strat_1/6_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/7_region.json", "output/smooth/strat_1/7_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/8_region.json", "output/smooth/strat_1/8_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/9_region.json", "output/smooth/strat_1/9_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/10_region.json", "output/smooth/strat_1/10_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/11_region.json", "output/smooth/strat_1/11_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/12_region.json", "output/smooth/strat_1/12_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/13_region.json", "output/smooth/strat_1/13_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/14_region.json", "output/smooth/strat_1/14_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/15_region.json", "output/smooth/strat_1/15_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/16_region.json", "output/smooth/strat_1/16_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/17_region.json", "output/smooth/strat_1/17_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/18_region.json", "output/smooth/strat_1/18_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/19_region.json", "output/smooth/strat_1/19_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/20_region.json", "output/smooth/strat_1/20_region.png", False)
# slice_demo("demos/vase_slice/smooth/strat_1/32_region.json", "output/smooth/strat_1/32_region.png", False)
#
# def update_config(base_file, strat, num_regions):
#     with open(base_file, 'r') as file:
#         config = json.load(file)
#
#     config["object_settings"]["name"] = f"{strat}/{num_regions}_region"
#     config["gradient_settings"]["num_regions"] = num_regions
#
#     with open(base_file, 'w') as file:
#         json.dump(config, file, indent=4)
#
# strat_1_lower_region_bound = 2
# strat_1_upper_region_bound = 17
#
# strat_2_lower_region_bound = 2
# strat_2_upper_region_bound = 48
#
# # # Generate toolpaths for strat 1
# # for i in range(strat_1_lower_region_bound, strat_1_upper_region_bound + 1):
# #     update_config("demos/vase_slice/smooth/strat_1/base.json", "strat_1", i)
# #     slice_demo("demos/vase_slice/smooth/strat_1/base.json", f"output/smooth/strat_1/viz_{i}_region.png", False)
# #
# # # Generate toolpaths for strat 2
# # for i in range(strat_2_lower_region_bound, strat_2_upper_region_bound + 1):
# #     update_config("demos/vase_slice/smooth/strat_2/base.json", "strat_2", i)
# #     slice_demo("demos/vase_slice/smooth/strat_2/base.json", f"output/smooth/strat_2/viz_{i}_region.png", True)
#
# import cv2
# import numpy as np
# import matplotlib.pyplot as plt
# from skimage.color import rgb2lab, deltaE_cie76
#
# def load_image(image_path):
#     return cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
#
# def get_line_points(x1, y1, x2, y2, num_points):
#     return np.linspace((x1, y1), (x2, y2), num_points).astype(int)
#
# def extract_colors(image, points):
#     return [image[y, x] for x, y in points]
#
# def calculate_color_differences(colors):
#     differences = []
#     for i in range(len(colors) - 1):
#         diff = np.linalg.norm(np.array(colors[i]) - np.array(colors[i + 1]))
#         differences.append(diff)
#     return differences
#
# def quantify_smoothness(differences):
#     return np.sum(differences)
#
# def evaluate_gradient_smoothness(image_path, x1, y1, x2, y2, num_points):
#     image = load_image(image_path)
#     points = get_line_points(x1, y1, x2, y2, num_points)
#     colors = extract_colors(image, points)
#     differences = calculate_color_differences(colors)
#     smoothness = quantify_smoothness(differences)
#     return smoothness, differences
#
# def plot_color_differences(differences, image_name):
#     plt.plot(differences, marker='o')
#     plt.xlabel('Sample Point')
#     plt.ylabel('Color Difference')
#     plt.title(f'Color Differences along the Gradient for {image_name}')
#     plt.grid(True)
#     plt.savefig(f'output/smooth/color_differences_{image_name}.png')
#     plt.close()
#
# def plot_smoothness(smoothness_values, num_regions, strat):
#     plt.plot(num_regions, smoothness_values, marker='o')
#     plt.xlabel('Number of Regions')
#     plt.ylabel('Smoothness')
#     plt.title(f'{strat} Smoothness of Gradient vs Number of Regions')
#     plt.grid(True)
#     plt.show()
#
# def crop_image(image, top_left, bottom_right):
#     x1, y1 = top_left
#     x2, y2 = bottom_right
#     return image[y1:y2, x1:x2]
#
# def compute_delta_e(image1, image2):
#     lab1 = rgb2lab(image1)
#     lab2 = rgb2lab(image2)
#     delta_e = deltaE_cie76(lab1, lab2)
#     return delta_e
#
# from matplotlib import cm
#
# def create_delta_e_image(delta_e, output_path):
#     # Normalize delta E values to range [0, 1]
#     # delta_e_normalized = cv2.normalize(delta_e, None, 0, 1, cv2.NORM_MINMAX)
#
#     # Plot the delta E values
#     plt.imshow(delta_e, cmap='inferno')
#     # Hide the axes
#     plt.axis('off')
#     # Set size of the plot
#     plt.gcf().set_size_inches(20,20)
#     # Remove white space
#     plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
#
#     # Save the image
#     plt.savefig(output_path)
#
#     # # Apply the inferno colormap to the normalized delta E values
#     # inferno_colormap = cm.get_cmap('inferno')
#     # delta_e_colored = inferno_colormap(delta_e)
#     #
#     # # Convert to 8-bit image
#     # delta_e_image = (delta_e_colored[:, :, :3] * 255).astype(np.uint8)
#     #
#     # # Save the image
#     # cv2.imwrite(output_path, delta_e_image)
#
# def compute_average_delta_e(delta_e):
#     return np.mean(delta_e)
#
# def plot_average_delta_e(average_delta_e_values, num_regions, strat):
#     plt.plot(num_regions, average_delta_e_values, marker='o')
#     plt.xlabel('Number of Regions')
#     plt.ylabel('Average Delta E')
#     plt.title(f'{strat} Average Delta E vs Number of Regions')
#     plt.grid(True)
#     plt.show()
#
# def rgb_to_cmyk(r, g, b):
#     if (r, g, b) == (0, 0, 0):
#         return 0, 0, 0, 1
#     c = 1 - r / 255
#     m = 1 - g / 255
#     y = 1 - b / 255
#     k = min(c, m, y)
#     c = (c - k) / (1 - k)
#     m = (m - k) / (1 - k)
#     y = (y - k) / (1 - k)
#     return c, m, y, k
#
# def extract_yellow_and_blue_components(image, points):
#     yellow_values = []
#     blue_values = []
#     for x, y in points:
#         r, g, b = image[y, x]
#         _, _, y, _ = rgb_to_cmyk(r, g, b)
#         yellow_values.append(y * 100)  # Convert to percentage
#         blue_values.append(b)
#     return yellow_values, blue_values
#
# def plot_yellow_and_blue_components(yellow_values, blue_values, image_name, strat):
#     fig, ax1 = plt.subplots()
#     color = 'gold'
#     ax1.set_xlabel('Sample Point')
#     ax1.set_ylabel('Yellow Component Value (%)', color=color)
#     ax1.plot(yellow_values, color=color, marker='o')
#     ax1.tick_params(axis='y', labelcolor=color)
#     ax2 = ax1.twinx()
#     color = 'blue'
#     ax2.set_ylabel('Blue Component Value', color=color)
#     ax2.plot(blue_values, color=color, marker='x')
#     ax2.tick_params(axis='y', labelcolor=color)
#     plt.title(f'Yellow and Blue Components along the Line for {image_name}')
#     fig.tight_layout()
#     plt.grid(True)
#     plt.savefig(f'output/smooth/{strat}/yellow_blue_components_{image_name}.png')
#     plt.close()
#
# def generate_plots(strat, images, num_regions, reference_image):
#     average_delta_e_values = []
#     smoothness_values = []
#     for path in images:
#         image_name = path.split('/')[-1].split('.')[0]
#         image = load_image(path)
#         delta_e = compute_delta_e(reference_image, image)
#         # create_delta_e_image(delta_e, f'output/smooth/{strat}/delta_e_{image_name}.png')
#         average_delta_e = compute_average_delta_e(delta_e)
#         average_delta_e_values.append(average_delta_e)
#         # smoothness, differences = evaluate_gradient_smoothness(path, x1, y1, x2, y2, num_points)
#         # smoothness_values.append(smoothness)
#         # yellow_values, blue_values = extract_yellow_and_blue_components(image, get_line_points(x1, y1, x2, y2, num_points))
#         # plot_yellow_and_blue_components(yellow_values, blue_values, image_name, strat)
#     # plot_average_delta_e(average_delta_e_values, num_regions, strat)
#     return average_delta_e_values
#     # plot_smoothness(smoothness_values, num_regions, strat)
#
# strat_1_image_paths = []
# for i in range(strat_1_lower_region_bound, strat_1_upper_region_bound):
#     strat_1_image_paths.append(f'output/smooth/strat_1/viz_{i}_region.png')
# strat_2_image_paths = []
# for i in range(strat_2_lower_region_bound, strat_2_upper_region_bound):
#     strat_2_image_paths.append(f'output/smooth/strat_2/viz_{i}_region.png')
# strat_1_num_regions = list(range(strat_1_lower_region_bound, strat_1_upper_region_bound))
# strat_2_num_regions = list(range(strat_2_lower_region_bound, strat_2_upper_region_bound))
# strat_1_reference_image_path = f'output/smooth/strat_1/viz_{strat_1_upper_region_bound}_region.png'
# strat_2_reference_image_path = f'output/smooth/strat_2/viz_{strat_2_upper_region_bound}_region.png'
# strat_1_reference_image = load_image(strat_1_reference_image_path)
# strat_2_reference_image = load_image(strat_2_reference_image_path)
#
# x1, y1 = 1408, 1037  # start point (x,y)
# x2, y2 = 1003, 1654  # end point (x,y)
# num_points = 2000  # number of points to sample along the line
#
# strat_1_average_delta_e_value = generate_plots("strat_1", strat_1_image_paths, strat_1_num_regions, strat_2_reference_image)
# # strat_2_average_delta_e_value = generate_plots("strat_2", strat_2_image_paths, strat_2_num_regions, strat_2_reference_image)
#
# plt.plot(strat_1_num_regions, strat_1_average_delta_e_value, marker='o', label='Strat 1')
# # plt.plot(strat_2_num_regions, strat_2_average_delta_e_value, marker='x', label='Strat 2')
# plt.xlabel('Number of Colors in Palette')
# plt.ylabel('Average Delta E')
# plt.title('Average Delta E vs Number of Colors in Palette (Log Scale)')
# plt.xscale('log')
# plt.grid(True)
# plt.legend()
# plt.show()
# # Save as SVG
# plt.savefig('output/smooth/average_delta_e_vs_num_colors_log.svg')
#
# plt.plot(strat_1_num_regions, strat_1_average_delta_e_value, marker='o', label='Strategy 1')
# # plt.plot(strat_2_num_regions, strat_2_average_delta_e_value, marker='x', label='Strategy 2')
# plt.xlabel('Number of Colors in Palette')
# plt.ylabel('Average Delta E')
# plt.title('Average Delta E vs Number of Colors in Palette')
# plt.grid(True)
# # plt.legend()
#
# # Save as PNG
# plt.savefig('output/smooth/average_delta_e_vs_num_colors.svg')
# plt.show()
#
#
# # # Example usage
# # reference_image_path = 'output/smooth/32_region.png'
# # image_paths = [
# #     'output/smooth/strat_1/2_region.png',
# #     'output/smooth/strat_1/3_region.png',
# #     'output/smooth/strat_1/4_region.png',
# #     'output/smooth/strat_1/5_region.png',
# #     'output/smooth/strat_1/6_region.png',
# #     'output/smooth/strat_1/7_region.png',
# #     'output/smooth/strat_1/8_region.png',
# #     'output/smooth/strat_1/9_region.png',
# #     'output/smooth/strat_1/10_region.png',
# #     'output/smooth/strat_1/11_region.png',
# #     'output/smooth/strat_1/12_region.png',
# #     'output/smooth/strat_1/13_region.png',
# #     'output/smooth/strat_1/14_region.png',
# #     'output/smooth/strat_1/15_region.png',
# #     'output/smooth/strat_1/16_region.png',
# #     'output/smooth/strat_1/17_region.png',
# #     'output/smooth/strat_1/18_region.png',
# #     'output/smooth/strat_1/19_region.png',
# #     'output/smooth/strat_1/20_region.png'
# # ]
# #
# # num_regions = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 32]
# # average_delta_e_values = []
# # smoothness_values = []
# #
# # top_left = (343, 676)
# # bottom_right = (2099, 2087)
# # x1, y1 = 1408, 1037  # start point (x,y)
# # x2, y2 = 1003, 1654  # end point (x,y)
# # num_points = 2000  # number of points to sample along the line
# #
# # reference_image = load_image(reference_image_path)
# # cropped_reference_image = crop_image(reference_image, top_left, bottom_right)
# #
# # for path in image_paths:
# #     image_name = path.split('/')[-1].split('.')[0]
# #     image = load_image(path)
# #     cropped_image = crop_image(image, top_left, bottom_right)
# #     delta_e = compute_delta_e(cropped_reference_image, cropped_image)
# #     create_delta_e_image(delta_e, f'output/smooth/delta_e_{image_name}.png')
# #     average_delta_e = compute_average_delta_e(delta_e)
# #     average_delta_e_values.append(average_delta_e)
# #     smoothness, differences = evaluate_gradient_smoothness(path, x1, y1, x2, y2, num_points)
# #     smoothness_values.append(smoothness)
# #     plot_color_differences(differences, image_name)
# #     yellow_values, blue_values = extract_yellow_and_blue_components(image, get_line_points(x1, y1, x2, y2, num_points))
# #     plot_yellow_and_blue_components(yellow_values, blue_values, image_name)
# #
# # plot_average_delta_e(average_delta_e_values, num_regions)
# # plot_smoothness(smoothness_values, num_regions)