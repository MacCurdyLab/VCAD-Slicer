from libvcad import pyvcad as pv
import infill
import visualization as vis


class Layer:
    def __init__(self, outline, z_height, bead_width, purge_tower_centers,
                 purge_tower_x_size, purge_tower_y_size):
        self.z_height = z_height
        self.bead_width = bead_width

        self.outline = outline

        self.walls = []
        self.infill = []

        self.ranged_walls = []
        self.ranged_infill = []

        self.connected_paths = []

        self.purge_tower_walls = 56
        self.purge_tower_centers = purge_tower_centers
        self.purge_tower_x_size = purge_tower_x_size
        self.purge_tower_y_size = purge_tower_y_size

    def get_z_height(self):
        return self.z_height

    def get_paths(self):
        return self.connected_paths

    def write_layer(self, gcode_writer):
        gcode_writer.write_layer(self)

    def generate_walls(self, number):

        if len(self.walls) == 0:  # If there are no walls yet, add the outline
            # Under-size by a small amount to ensure the walls are not touching, THIS IS A WORK AROUND
            self.walls.append(pv.Polygon2.Offset(self.outline, -self.bead_width * 0.02))
        outline = self.walls[-1]

        for i in range(1, number):
            self.walls.append(pv.Polygon2.Offset(outline, -self.bead_width * i))

    def generate_infill(self, density_percentage):
        infill_spacing = self.bead_width / density_percentage

        outline = None
        if len(self.walls) == 0:
            outline = self.outline
        else:
            outline = self.walls[-1]

        # Generate the infill outline as the outline offset by the bead width
        infill_outline = pv.Polygon2.Offset(outline, -self.bead_width)

        self.infill = infill.generate_rectilinear_infill(infill_outline, infill_spacing)

    def generate_purge_tower(self, start_pt, desired_range):
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

        self.connected_paths.extend(polylines)

    def cut_into_ranges(self, desired_ranges, slicer):
        ranges = slicer.slice_material(self.z_height, 1, desired_ranges)

        concatenated_walls = []
        for wall in self.walls:
            for polygon in wall:
                polyline = polygon.to_polyline()
                concatenated_walls.append(polyline)

        for lower, higher, polygons in ranges:
            resulting_walls = []
            resulting_infill_lines = []
            clipped_walls = pv.Polygon2.Clip(polygons, concatenated_walls)[1]
            # vis.plot_polygons_and_polylines([], clipped_walls, figsize=(20, 12))
            for polyline in clipped_walls:
                resulting_walls.append(polyline)

            clipped_infill = pv.Polygon2.Clip(polygons, self.infill)[1]
            for polyline in clipped_infill:
                resulting_infill_lines.append(polyline)

            self.ranged_walls.append((lower, higher, resulting_walls))
            self.ranged_infill.append((lower, higher, resulting_infill_lines))

            labled_polygons = []
            for lower, higher, wall in self.ranged_walls:
                for polygon in wall:
                    labled_polygons.append((polygon, (lower + higher) / 2.0))
            labled_polylines = []
            for lower, higher, infill in self.ranged_infill:
                for line in infill:
                    labled_polylines.append((line, (lower + higher) / 2.0))

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
        for lower, higher, infill in self.ranged_infill:
            if lower < desired_range[0] or higher > desired_range[1]:
                continue
            for line in infill:
                available_paths.append((lower, higher, True, line))  # True indicates that this is an extrusion path

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
                distance_to_start = Layer.distance(current_end, start)
                distance_to_end = Layer.distance(current_end, end)
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

            # Add travel segment
            travel = pv.Polyline2([current_end, nearest_path[3].points()[0]])
            self.connected_paths.append((0, 0, False, travel))  # False indicates that this is a travel move
            self.connected_paths.append(nearest_path)
            available_paths.remove(nearest_path)
            current_path = nearest_path

    def connect_paths(self):
        # If the layer is empty, return
        if len(self.ranged_walls) == 0 and len(self.ranged_infill) == 0:
            return

        ranges = []
        for lower, higher, walls in self.ranged_walls:
            ranges.append((lower, higher))

        previous_end = pv.Point2(-8, 10)  # Start at the origin
        for lower, higher in ranges:
            self.generate_purge_tower(previous_end, (lower, higher))

            self.connect_paths_in_range(previous_end, (lower, higher))
            if len(self.connected_paths) > 0:
                previous_end = self.connected_paths[-1][3].points()[-1]

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

    def visualize_paths(self):
        vis.plot_labeled_paths(self.connected_paths)
