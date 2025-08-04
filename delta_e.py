from skimage import io, color
import numpy as np
import matplotlib.pyplot as plt
import os


def visualize_delta_e_map(delta_e_map, output_path, cmap='jet'):
    """
    Saves a visualization of the delta E map using a specified colormap.

    Parameters:
        delta_e_map (np.array): A 2D array of delta E values.
        output_path (str): Path to save the visualized map image.
        cmap (str): The matplotlib colormap to use, e.g. 'jet', 'viridis'.
    """
    # Optional: You could specify a known range for delta E
    # For example, if you know the expected range:
    # vmin=0 and vmax=some upper bound. Without it, matplotlib
    # automatically scales based on min and max values in delta_e_map.

    plt.imsave(output_path, delta_e_map, cmap=cmap)


def average_delta_e_with_visual(image_path_A, image_path_B, output_visual_path):
    # Load images
    imgA = io.imread(image_path_A)
    imgB = io.imread(image_path_B)

    # If images have an alpha channel, drop it
    if imgA.shape[-1] == 4:
        imgA = imgA[..., :3]
    if imgB.shape[-1] == 4:
        imgB = imgB[..., :3]

    # Ensure the images have the same shape
    if imgA.shape != imgB.shape:
        raise ValueError("Input images must have the same dimensions and channels.")

    # Convert from RGB to LAB
    labA = color.rgb2lab(imgA)
    labB = color.rgb2lab(imgB)

    # Compute the Delta E map using CIEDE2000
    delta_e_map = color.deltaE_ciede2000(labA, labB)

    # Compute the average Delta E
    average_de = np.mean(delta_e_map)

    # Save a visualization of the delta E map
    # Here we use 'jet' colormap. You can choose other colormaps such as 'viridis' or 'plasma'.
    visualize_delta_e_map(delta_e_map, output_visual_path, cmap='jet')

    return average_de


# Example usage:
# ground_truth = "delta_e/36.png"
# a = "delta_e/4.png"
# b = "delta_e/8.png"
# c = "delta_e/12.png"
# d = "delta_e/16.png"
# e = "delta_e/12_cont.png"
# f = "delta_e/24.png"
# g = "delta_e/36.png"
# h = "delta_e/48.png"
#
#
# print("Average ΔE of 4.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, a, "delta_e/output/4_visual.png")))
# print("Average ΔE of 8.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, b, "delta_e/output/8_visual.png")))
# print("Average ΔE of 12.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, c, "delta_e/output/12_visual.png")))
# print("Average ΔE of 16.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, d, "delta_e/output/16_visual.png")))
# print("Average ΔE of 12_cont.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, e, "delta_e/output/12_cont_visual.png")))
# print("Average ΔE of 24.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, f, "delta_e/output/24_visual.png")))
# print("Average ΔE of 36.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, g, "delta_e/output/36_visual.png")))
# print("Average ΔE of 48.png: {:.2f}".format(average_delta_e_with_visual(ground_truth, h, "delta_e/output/48_visual.png")))

ground_truth_blur = "delta_e/48_blur.png"
a_blur = "delta_e/4_blur.png"
b_blur = "delta_e/8_blur.png"
c_blur = "delta_e/12_blur.png"
d_blur = "delta_e/16_blur.png"
e_blur = "delta_e/12_cont_blur.png"
f_blur = "delta_e/24_blur.png"
g_blur = "delta_e/36_blur.png"
h_blur = "delta_e/48_blur.png"


print("Average ΔE of 4_blur.png: {:.2f}".format(average_delta_e_with_visual(d_blur, a_blur, "delta_e/output/4_blur_visual.png")))
print("Average ΔE of 8_blur.png: {:.2f}".format(average_delta_e_with_visual(d_blur, b_blur, "delta_e/output/8_blur_visual.png")))
print("Average ΔE of 12_blur.png: {:.2f}".format(average_delta_e_with_visual(d_blur, c_blur, "delta_e/output/12_blur_visual.png")))
print("Average ΔE of 16_blur.png: {:.2f}".format(average_delta_e_with_visual(d_blur, d_blur, "delta_e/output/16_blur_visual.png")))
print("Average ΔE of 12_cont_blur.png: {:.2f}".format(average_delta_e_with_visual(ground_truth_blur, e_blur, "delta_e/output/12_cont_blur_visual.png")))
print("Average ΔE of 24_blur.png: {:.2f}".format(average_delta_e_with_visual(ground_truth_blur, f_blur, "delta_e/output/24_blur_visual.png")))
print("Average ΔE of 36_blur.png: {:.2f}".format(average_delta_e_with_visual(ground_truth_blur, g_blur, "delta_e/output/36_blur_visual.png")))
print("Average ΔE of 48_blur.png: {:.2f}".format(average_delta_e_with_visual(ground_truth_blur, h_blur, "delta_e/output/48_blur_visual.png")))