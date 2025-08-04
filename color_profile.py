import demo_objects as do
from libvcad import pyvcad as pv
from libvcad import pyvcadviz as viz
import numpy as np
import os
import colorsys


config_path = "vcad_configs/colors.json"
vcad_script_path = "demos/vase_slice/vase_slice_yellow_blue.vcad"
z_sample_height = 100


plugin_path = os.path.join(os.path.dirname(__file__), "plugins")
os.environ["QT_PLUGIN_PATH"] = plugin_path

meta, root = do.parse_from_file(vcad_script_path, config_path)

# Visualize the object
# viz.Render(config_path, meta.min, meta.max, meta.voxel_size, root, True)

# Same the VCAD design into a single layer image
resolution = 500
min = meta.min
max = meta.max
material_def = pv.MaterialDefs(config_path)
image = np.zeros((resolution, resolution, 4), dtype=np.float32)


def rgb_to_hsv(r, g, b):
    return colorsys.rgb_to_hsv(r, g, b)  # r,g,b in [0,1]


def hsv_to_rgb(h, s, v):
    return colorsys.hsv_to_rgb(h, s, v)


def blend_colors_hsv(distribution, material_def):
    # Initialize accumulators
    total_fraction = 0.0
    hues = []
    sats = []
    vals = []

    for material_id, fraction in distribution.items():
        vcad_color = material_def.color(material_id)
        r = vcad_color.r / 255.0
        g = vcad_color.g / 255.0
        b = vcad_color.b / 255.0
        h, s, v = rgb_to_hsv(r, g, b)

        # Weighted accumulation in HSV space is tricky.
        # One naive approach is to just pick the hue of the largest fraction
        # or do a weighted average of hue angles correctly (watching out for hue wrap-around).
        # For simplicity, let's just store them in an array and we will do a weighted average below.

        hues.append((h, fraction))
        sats.append((s, fraction))
        vals.append((v, fraction))
        total_fraction += fraction

    if total_fraction > 0:
        # Weighted average of hue:
        # Hue is circular, so we should average using vector math to avoid wrap-around issues
        # But if we know colors are far apart, a simpler approach might suffice.
        # For a simple scenario, let's just do a naive weighted average:
        avg_h = sum(h * f for h, f in hues) / total_fraction
        avg_s = sum(s * f for s, f in sats) / total_fraction
        avg_v = sum(v * f for v, f in vals) / total_fraction
    else:
        avg_h, avg_s, avg_v = 0.0, 0.0, 0.0

    # Convert back to RGB
    blended_r, blended_g, blended_b = hsv_to_rgb(avg_h, avg_s, avg_v)
    return np.array([blended_r, blended_g, blended_b, 1.0], dtype=np.float32)

for x in range(resolution):
    for y in range(resolution):
        z_pos = z_sample_height
        x_pos = min.x + (max.x - min.x) * x / resolution
        y_pos = min.y + (max.y - min.y) * y / resolution

        distribution = root.distribution(x_pos, y_pos, z_pos)

        # At this point the distrbution is a map of material ID to their volumn fraction
        # We can use the material definitions to fetch the RGB color of the material
        # We then need to blend the colors based on the distribution volume fractions to get a single color
        color = blend_colors_hsv(distribution, material_def)
        image[x, y] = color

# Save the image
import matplotlib.pyplot as plt
plt.imshow(image)
plt.show()

