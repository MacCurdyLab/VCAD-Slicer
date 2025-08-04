import matplotlib.pyplot as plt
import pyvcad as pv
import infill
import visualization as vis


class OutlineLayer:
    def __init__(self, outline, z_height, bead_width, layer_num, fill_with_infill, purge_tower_centers = None, purge_tower_x_size = None, purge_tower_y_size = None):
        self.z_height = z_height
        self.bead_width = bead_width

        self.outline = outline

        self.walls = []

        self.ranged_walls = []

        self.connected_paths = []

        self.layer_num = layer_num

        self.fill_with_infill = fill_with_infill

        if purge_tower_centers == None:
            self.use_purge_tower = False
        else:
            self.use_purge_tower = True
            self.purge_tower_walls = 100
            self.purge_tower_centers = purge_tower_centers
            self.purge_tower_x_size = purge_tower_x_size
            self.purge_tower_y_size = purge_tower_y_size

        self.ranged_wall = []

    def get_z_height(self):
        return self.z_height

    def get_layer_num(self):
        return self.layer_num

    def get_paths(self):
        return self.connected_paths

    def write_layer(self, gcode_writer, future_layers):
        gcode_writer.write_layer(self, future_layers)

    def generate_walls(self, desired_ranges, slicer, reverse):
        # Iterate over the desired ranges switch any value that is zero to -1 and value that is 1 to 2
        # This is a workaround
        copied_ranges = desired_ranges.copy()
        for i in range(len(copied_ranges)):
            if copied_ranges[i][0] == 0:
                copied_ranges[i] = (-1, copied_ranges[i][1])
            if copied_ranges[i][1] == 1:
                copied_ranges[i] = (copied_ranges[i][0], 2)

        ranges = slicer.slice_material(self.z_height, 1, copied_ranges)

        # Undo the -1 and 2 values on the result ranges
        for i in range(len(ranges)):
            lower, higher, polygons = ranges[i]
            if lower == -1:
                lower = 0
            if higher == 2:
                higher = 1
            ranges[i] = (lower, higher, polygons)

        num_wall_to_try = 100

        if reverse:
            ranges.reverse()

        for lower, higher, polygons in ranges:
            paths = []
            for poly in polygons:
                # Offset polygon by half the bead width inwards
                # Note, this might generate multiple polygons so we will need to iterate over them
                base_polygons = poly.offset(-self.bead_width / 2.0)

                for polygon in base_polygons:
                    polyline = polygon.to_polyline()
                    if self.fill_with_infill:
                        paths.append(polyline)
                        # Also add the holes
                        for hole in polygon.holes():
                            hole_polyline = hole.to_polyline()
                            paths.append(hole_polyline)

                        # Offset polygon by half the bead width inwards
                        inset_polygon = polygon.offset(-self.bead_width / 2.0)
                        new_infill =  infill.generate_rectilinear_infill(inset_polygon, self.bead_width)
                        paths.extend(new_infill)
                    else:
                        for i in range(num_wall_to_try):
                            offset_poly = polygon.offset(-self.bead_width * i)
                            new_area = 0
                            for p in offset_poly:
                                new_area += p.double_area()

                            # If the area is decreasing, and not near zero
                            if len(offset_poly) > 0 and abs(new_area) > 0.05:
                                for result in offset_poly:
                                    result_polyline = result.to_polyline()
                                    paths.append(result_polyline)
                                    # If the polygon had holes, we need to add them as well
                                    for hole in result.holes():
                                        hole_polyline = hole.to_polyline()
                                        paths.append(hole_polyline)
                            else:
                                break
            self.ranged_walls.append((lower, higher, paths))

    def generate_purge_tower(self, start_pt, desired_range):
        # If the purge tower size is zero, skip this step
        if self.purge_tower_x_size == 0 or self.purge_tower_y_size == 0:
            return

        # Get the center of the purge tower for this range
        center = None
        for lower, higher, c in self.purge_tower_centers:
            if lower == desired_range[0] and higher == desired_range[1]:
                center = c
                break

        # Create a box around the center
        half_size_x = self.purge_tower_x_size / 2.0
        half_size_y = self.purge_tower_y_size / 2.0
        box = pv.Polygon2([pv.Point2(center.x() - half_size_x, center.y() - half_size_y),
                           pv.Point2(center.x() + half_size_x, center.y() - half_size_y),
                           pv.Point2(center.x() + half_size_x, center.y() + half_size_y),
                           pv.Point2(center.x() - half_size_x, center.y() + half_size_y),
                           pv.Point2(center.x() - half_size_x, center.y() - half_size_y)])

        walls = []
        for i in range(0, self.purge_tower_walls):
            walls.append(pv.Polygon2.Offset([box], -self.bead_width * i))

        polylines = []
        for wall in walls:
            if len(wall) == 0:
                continue

            polyline = wall[0].to_polyline()
            # Add travel from the start point to the first point
            travel = pv.Polyline2([start_pt, polyline.points()[0]])
            polylines.append((0, 0, False, travel))
            polylines.append((desired_range[0], desired_range[1], True, polyline))
            start_pt = polyline.points()[-1]

        # Calculate total length of purge tower extrusion
        total_length = 0
        for lower, higher, is_extrusion, polyline in polylines:
            if is_extrusion:
                total_length += polyline.length()
        # print("Purge tower extrusion length: {:.4f}".format(total_length))

        self.connected_paths.extend(polylines)

    # Static method to compute the distance between two points
    @staticmethod
    def distance(p1, p2):
        return ((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2) ** 0.5

    def connect_paths_in_range(self, start_point, desired_range):
        available_paths = []
        for lower, higher, walls in self.ranged_walls:
            if lower < desired_range[0] or higher > desired_range[1]:
                continue
            for wall in walls:
                available_paths.append((lower, higher, True, wall))  # True indicates that this is an extrusion path

        if len(available_paths) == 0:
            return

        current_path = available_paths[0]
        available_paths.remove(current_path)

        # Add a travel move to the first path
        travel = pv.Polyline2([start_point, current_path[3].points()[0]])
        self.connected_paths.append((0, 0, False, travel))
        self.connected_paths.append(current_path)

        # Connect the paths by adding travel moves
        # This is done by finding the closest path to the current path and adding a travel move to it.
        # We need to check the start point and end point of each polyline. If the end is closer we need to
        # reverse the polyline
        # Once the nearest path is found, we add a travel move to it and remove it from the available paths
        # This process is repeated until all paths are connected
        while len(available_paths) > 0:
            current_end = current_path[3].points()[-1]
            min_distance = float('inf')
            nearest_path = None
            needs_reversal = False
            for path in available_paths:
                start = path[3].points()[0]
                end = path[3].points()[-1]
                distance_to_start = OutlineLayer.distance(current_end, start)
                distance_to_end = OutlineLayer.distance(current_end, end)
                if distance_to_start < min_distance:
                    min_distance = distance_to_start
                    nearest_path = path
                    needs_reversal = False
                if distance_to_end < min_distance:
                    min_distance = distance_to_end
                    nearest_path = path
                    needs_reversal = True
            if needs_reversal:
                nearest_path[3].reverse()

            # Add travel segment if the min distance is non-zero
            if min_distance > 0.05:
                travel = pv.Polyline2([current_end, nearest_path[3].points()[0]])
                self.connected_paths.append((0, 0, False, travel))  # False indicates that this is a travel move
            self.connected_paths.append(nearest_path)
            available_paths.remove(nearest_path)
            current_path = nearest_path

    def connect_paths(self):
        # If the layer is empty, return
        if len(self.ranged_walls) == 0:
            return

        ranges = []
        for lower, higher, walls in self.ranged_walls:
            ranges.append((lower, higher))

        previous_end = pv.Point2(-8, 10)  # Start at the origin
        for lower, higher in ranges:
            if self.use_purge_tower:
                self.generate_purge_tower(previous_end, (lower, higher))

            self.connect_paths_in_range(previous_end, (lower, higher))
            if len(self.connected_paths) > 0:
                previous_end = self.connected_paths[-1][3].points()[-1]

    def get_bounds(self):
        min = [float('inf'), float('inf')]
        max = [-float('inf'), -float('inf')]
        # Iterate over all of the paths to find the min and max x and y values
        for lower, higher, is_extrusion, polyline in self.connected_paths:
            for point in polyline.points():
                if point.x() < min[0]:
                    min[0] = point.x()
                if point.y() < min[1]:
                    min[1] = point.y()
                if point.x() > max[0]:
                    max[0] = point.x()
                if point.y() > max[1]:
                    max[1] = point.y()

        return min, max

    def translate_paths(self, xy_translation, z_translation):
        for lower, higher, is_extrusion, polyline in self.connected_paths:
            polyline.translate(xy_translation)
        self.z_height += z_translation

    def visualize_geometry(self):
        polygons = []
        polyline = []
        for wall in self.walls:
            polygons.extend(wall)
        for line in self.infill:
            polyline.append(line)
        vis.plot_polygons_and_polylines(polygons, polyline, figsize=(20, 12))

    def visualize_ranged_geometry(self, ranges=None):
        lines = []
        for lower, higher, walls in self.ranged_walls:
            # Skip any lower, higher ranges that are not in the desired ranges
            if ranges is not None and (lower, higher) not in ranges:
                continue

            for wall in walls:
                lines.append((wall, (lower + higher) / 2.0))
        for lower, higher, infill in self.ranged_infill:
            # Skip any lower, higher ranges that are not in the desired ranges
            if ranges is not None and (lower, higher) not in ranges:
                continue

            for line in infill:
                lines.append((line, (lower + higher) / 2.0))
        vis.plot_labeled_polygons_and_polylines([], lines, figsize=(20, 12))

    def visualize_paths(self, printer_bounds=None, name=None, figsize=(15, 15)):
        vis.plot_labeled_paths(self.connected_paths, printer_bounds, name, figsize)
