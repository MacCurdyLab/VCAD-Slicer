from libvcad import pyvcad as pv
import layer


class Slicer:
    def __init__(self, root, min, max, voxel_size, center_point=pv.Vec2(0, 0),
                 purge_min=pv.Point2(0.0, 0.0), purge_max=pv.Point2(260.0, 260.0),
                 purge_tower_x_spacing=12.0, purge_tower_y_spacing=12.0,
                 purge_tower_x_size=12.0, purge_tower_y_size=12.0):

        self.cross_sectioner = pv.CrossSectionSlicer(root, min, max, voxel_size)
        self.min = min
        self.max = max
        self.voxel_size = voxel_size
        self.model_bottom_z = min.z
        self.center_point = center_point
        self.purge_min = purge_min
        self.purge_max = purge_max
        self.purge_tower_x_spacing = purge_tower_x_spacing
        self.purge_tower_y_spacing = purge_tower_y_spacing
        self.purge_tower_x_size = purge_tower_x_size
        self.purge_tower_y_size = purge_tower_y_size
        self.purge_tower_centers = []

        self.layers = []

    def slice(self, ranges, layer_height, bead_width, num_walls=1, infill_density=0):
        print("1. Generating purge tower base locations")
        self.compute_purge_tower_centers(ranges)
        print("2. Generating paths")
        self.generate_paths(layer_height, bead_width, num_walls, infill_density)
        print("3. Cutting into ranges")
        self.cut_into_ranges(ranges)
        print("4. Connecting paths")
        self.connect_paths()
        print("5.Centering paths on the bed")
        self.center_paths()

    def compute_purge_tower_centers(self, ranges):
        self.purge_tower_centers = []
        min_x = self.purge_min.x()
        min_y = self.purge_min.y()
        max_x = self.purge_max.x()
        max_y = self.purge_max.y()

        anchor = pv.Point2(min_x + self.purge_tower_x_spacing / 2, min_y + self.purge_tower_y_spacing / 2)
        possible_centers = []
        while anchor.y() < max_y:
            while anchor.x() < max_x:
                possible_centers.append(anchor)
                anchor = pv.Point2(anchor.x() + self.purge_tower_x_spacing, anchor.y())
            anchor = pv.Point2(min_x + self.purge_tower_x_spacing / 2, anchor.y() + self.purge_tower_y_spacing)

        if len(possible_centers) < len(ranges):
            raise ValueError("Not enough possible centers for the number of ranges. Please adjust the purge tower settings")

        for i in range(len(ranges)):
            self.purge_tower_centers.append((ranges[i][0], ranges[i][1], possible_centers[i]))

    def generate_paths(self, layer_height, bead_width, num_walls=1, infill_density=0):
        min_z = self.min.z
        max_z = self.max.z
        z = min_z
        layer_num = 1
        while z <= max_z:
            outlines = self.cross_sectioner.slice_geometry(z)
            if layer_num == 1:
                self.model_bottom_z = z

            if len(outlines) > 0:
                print("\t-> Generating paths for layer {} at z = {}".format(layer_num, z))
                new_layer = layer.Layer(outlines, z, bead_width, self.purge_tower_centers,
                                        self.purge_tower_x_size, self.purge_tower_y_size)
                if num_walls > 0:
                    new_layer.generate_walls(num_walls)
                if infill_density > 0:
                    new_layer.generate_infill(infill_density)
                self.layers.append(new_layer)
                layer_num += 1
            else:
                print("\t-> Skipping layer at z = {}, not geometry found".format(z))
            z += layer_height

    def cut_into_ranges(self, desired_ranges):
        index = 1
        for l in self.layers:
            print("\t-> Cutting layer {} into ranges".format(index))
            l.cut_into_ranges(desired_ranges, self.cross_sectioner)
            index += 1

    def connect_paths(self):
        index = 1
        for l in self.layers:
            print("\t-> Connecting paths for layer {}".format(index))
            l.connect_paths()
            index += 1

    def center_paths(self):
        xy_translation = pv.Point2(self.center_point.x() - (self.max.x - self.min.x) / 2,
                                   self.center_point.y() - (self.max.y - self.min.y) / 2)
        z_translation = -self.model_bottom_z + 0.2
        for l in self.layers:
            l.translate_paths(xy_translation, z_translation)

    def write_gcode(self, gcode_writer, extruder_temperature=200, bed_temperature=60):
        print("6. Writing GCode")
        gcode_writer.write_header(extruder_temperature, bed_temperature)
        i = 1
        for l in self.layers:
            print("\t-> Writing layer {}".format(i))
            l.write_layer(gcode_writer)
            i += 1
        gcode_writer.write_footer()

    def visualize_geometry(self):
        for l in self.layers:
            l.visualize_geometry()

    def visualize_ranged_geometry(self, ranges=None):
        for l in self.layers:
            l.visualize_ranged_geometry(ranges)

    def visualize_paths(self):
        for l in self.layers:
            l.visualize_paths()
