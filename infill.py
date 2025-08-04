import pyvcad as pv


def get_global_bounding_box(outlines):
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')
    for outline in outlines:
        for point in outline:
            min_x = min(min_x, point.x())
            min_y = min(min_y, point.y())
            max_x = max(max_x, point.x())
            max_y = max(max_y, point.y())
    return min_x, min_y, max_x, max_y


# This function fills the outlines with a rectilinear infill pattern
def generate_rectilinear_infill(outlines, spacing):
    min_x, min_y, max_x, max_y = get_global_bounding_box(outlines)
    infill_lines = []
    # Generate horizontal lines from min_y to max_y with spacing
    y = min_y
    while y <= max_y:
        infill_lines.append(pv.Polyline2([pv.Point2(min_x, y), pv.Point2(max_x, y)]))
        y += spacing

    # Now we need to clip the infill lines with the outlines
    result = pv.Polygon2.Clip(outlines, infill_lines)[1]

    return result
