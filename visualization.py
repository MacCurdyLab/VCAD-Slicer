import matplotlib.pyplot as plt
import matplotlib.cm as cm


def plot_polygons(polygons=None):
    for polygon in polygons:
        points = [(p.x(), p.y()) for p in polygon]
        # Add the first point to the end to close the polygon
        points.append(points[0])
        for i in range(len(points) - 1):
            plt.arrow(points[i][0], points[i][1], points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1],
                      head_width=0.125, length_includes_head=True, linewidth=3.5)


def plot_labeled_polygons(labeled_polygons=None):
    for polygon, value in labeled_polygons:
        points = [(p.x(), p.y()) for p in polygon]
        # Add the first point to the end to close the polygon
        points.append(points[0])
        color = cm.viridis(value)  # Map the value to a color
        for i in range(len(points) - 1):
            plt.arrow(points[i][0], points[i][1], points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1],
                      head_width=0.125, length_includes_head=True, color=color, linewidth=3.5)


def plot_polylines(polylines=None):
    for polyline in polylines:
        points = [(p.x(), p.y()) for p in polyline.points()]
        for i in range(len(points) - 1):
            plt.arrow(points[i][0], points[i][1], points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1],
                      head_width=0.125, length_includes_head=True)


def plot_labeled_polylines(labeled_polylines=None):
    for polyline, value in labeled_polylines:
        points = [(p.x(), p.y()) for p in polyline.points()]
        color = cm.viridis(value)  # Map the value to a color
        for i in range(len(points) - 1):
            plt.arrow(points[i][0], points[i][1], points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1],
                      head_width=0.0, length_includes_head=True, color=color, linewidth=3.5)


def plot_labeled_polygons_and_polylines(labeled_polygons, polylines, figsize=(15, 15)):
    plt.figure(figsize=figsize)

    # Set x and y limits to be from 0 to 260
    plt.xlim(0, 260)
    plt.ylim(0, 260)


    plot_labeled_polygons(labeled_polygons)
    plot_labeled_polylines(polylines)

    plt.axis('equal')
    plt.show()


def plot_polygons_and_polylines(polygons, polylines, figsize=(15, 15)):
    plt.figure(figsize=figsize)

    # Set x and y limits to be from 0 to 260
    plt.xlim(0, 260)
    plt.ylim(0, 260)

    plot_polygons(polygons)
    plot_polylines(polylines)

    plt.axis('equal')
    plt.show()


def plot_labeled_paths(labeled_paths, printer_bounds=None, name=None, figsize=(15, 15)):
    plot_travels = False
    plt.figure(figsize=figsize)

    for lower, higher, is_extrusion, path in labeled_paths:
        points = [(p.x(), p.y()) for p in path.points()]
        color = cm.viridis((lower + higher) / 2.0)
        # Plot extrusion paths as arrows. Plot travels as dashed lines
        if is_extrusion:
            for i in range(len(points) - 1):
                plt.arrow(points[i][0], points[i][1], points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1],
                          head_width=0.0, length_includes_head=True, color=color, linewidth=6)
        elif plot_travels:
            for i in range(len(points) - 1):
                plt.plot([points[i][0], points[i + 1][0]], [points[i][1], points[i + 1][1]], color=color,
                         linestyle='--', linewidth=6)

    # Set x and y of the plot to be from 0 to 260
    # if printer_bounds:
    #     plt.xlim(printer_bounds[0], printer_bounds[2])
    #     plt.ylim(printer_bounds[1], printer_bounds[3])

    # Set axis to be equal
    plt.axis('equal')

    # Set axis to be between (0,0) an (175,150)
    plt.xlim(0, 175)
    plt.ylim(0, 175)

    plt.savefig(name, format='png')
    plt.show()


# def plot_labeled_paths(labeled_paths, printer_bounds=None, figsize=(18, 18)):
#
#     ranges = [(0.0, 0.125), (0.125, 0.25), (0.25, 0.375), (0.375, 0.5), (0.5, 0.625), (0.625, 0.75), (0.75, 0.875),
#               (0.875, 1.0)]
#
#     index = 0
#     for r in ranges:
#         plt.figure(figsize=figsize)
#         for lower, higher, is_extrusion, path in labeled_paths:
#             if lower == r[0]:
#                 points = [(p.x(), p.y()) for p in path.points()]
#                 color = cm.viridis((lower + higher) / 2.0)
#                 # Plot extrusion paths as arrows. Plot travels as dashed lines
#                 if is_extrusion:
#                     for i in range(len(points) - 1):
#                         plt.arrow(points[i][0], points[i][1], points[i + 1][0] - points[i][0],
#                                   points[i + 1][1] - points[i][1],
#                                   head_width=0.0, length_includes_head=True, color=color, linewidth=3.5)
#
#         plt.xlim(100, 155)
#         plt.ylim(100, 155)
#
#         # Save plot as SVG
#         plt.savefig('output/graph/part_{}.svg'.format(index), format='svg')
#         plt.show()
#         index += 1
#
#     exit(0)
