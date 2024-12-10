from libvcad import pyvcad as pv
import layer


class Slicer:
    def __init__(self, root, min, max, voxel_size, settings):
        self.settings = settings
        self.cross_sectioner = pv.CrossSectionSlicer(root, min, max, voxel_size)
        self.min = min
        self.max = max
        self.voxel_size = voxel_size
        self.model_bottom_z = min.z
        self.purge_min = settings["purge_tower_settings"]["min"]
        self.purge_max = settings["purge_tower_settings"]["max"]
        self.purge_tower_x_size = settings["purge_tower_settings"]["size"][0]
        self.purge_tower_y_size = settings["purge_tower_settings"]["size"][1]
        self.purge_tower_x_spacing = self.purge_tower_x_size + settings["purge_tower_settings"]["spacing"][0]
        self.purge_tower_y_spacing = self.purge_tower_y_size + settings["purge_tower_settings"]["spacing"][1]
        self.interlink = settings["gradient_settings"]["interlink"]
        self.purge_tower_centers = []

        # Compute the cetnering point based on the bed size
        printer_min = settings["printer_settings"]["dimensions"]["min"]
        printer_max = settings["printer_settings"]["dimensions"]["max"]
        self.center_point = ((printer_max[0] - printer_min[0]) / 2, (printer_max[1] - printer_min[1]) / 2)

        self.layers = []

    def slice(self, ranges):
        print("1. Generating purge tower base locations")
        self.compute_purge_tower_centers(ranges)
        print("2. Generating paths")
        self.generate_paths()
        print("3. Cutting into ranges")
        self.cut_into_ranges(ranges)
        print("4. Connecting paths")
        self.connect_paths()
        print("5.Centering paths on the bed")
        self.center_paths()

    def compute_purge_tower_centers(self, ranges):
        self.purge_tower_centers = []
        min_x = self.purge_min[0] - self.center_point[0]
        min_y = self.purge_min[1] - self.center_point[1]
        max_x = self.purge_max[0] - self.center_point[0]
        max_y = self.purge_max[1] - self.center_point[1]

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

    def generate_paths(self):
        layer_height = self.settings["slicer_settings"]["layer_height"]
        bead_width = self.settings["printer_settings"]["nozzle_diameter"]
        num_walls = self.settings["slicer_settings"]["num_walls"]
        infill_density = self.settings["slicer_settings"]["infill_density"] / 100.0

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
                                        self.purge_tower_x_size, self.purge_tower_y_size, layer_num)
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
        for l in self.layers:
            layer_number = l.get_layer_num()
            print("\t-> Cutting layer {} into ranges".format(layer_number))
            if self.interlink:
                l.cut_into_ranges_interdigitated(desired_ranges, self.cross_sectioner, layer_number % 2 == 0, self.settings["gradient_settings"]["overlap_amount"])
            else:
                l.cut_into_ranges(desired_ranges, self.cross_sectioner, layer_number % 2 == 0)

    def connect_paths(self):
        index = 1
        for l in self.layers:
            print("\t-> Connecting paths for layer {}".format(index))
            l.connect_paths()
            index += 1

    def center_paths(self):
        xy_translation = pv.Point2(self.center_point[0], self.center_point[1])

        user_translate = self.settings["object_settings"]["translation"]
        if user_translate is not None:
            xy_translation = pv.Point2(xy_translation.x() + user_translate[0], xy_translation.y() + user_translate[1])

        z_translation = -self.model_bottom_z + self.settings["slicer_settings"]["layer_height"]
        for l in self.layers:
            l.translate_paths(xy_translation, z_translation)

    def get_bounds(self):
        min = [float('inf'), float('inf')]
        max = [-float('inf'), -float('inf')]
        for l in self.layers:
            lmin, lmax = l.get_bounds()
            for i in range(2):
                if lmin[i] < min[i]:
                    min[i] = lmin[i]
                if lmax[i] > max[i]:
                    max[i] = lmax[i]
        return min, max

    def write_gcode(self, gcode_writer):
        print("6. Writing GCode")
        pmin, pmax = self.get_bounds()
        gcode_writer.write_header(pmin, pmax)
        i = 0
        for l in self.layers:
            future_layers = self.layers[i + 1:]
            print("\t-> Writing layer {}".format(i+1))
            l.write_layer(gcode_writer, future_layers)
            i += 1
        gcode_writer.write_footer()

    def visualize_geometry(self):
        for l in self.layers:
            l.visualize_geometry()

    def visualize_ranged_geometry(self, ranges=None):
        for l in self.layers:
            l.visualize_ranged_geometry(ranges)

    def visualize_paths(self, printer_bounds=None):
        for l in self.layers:
            l.visualize_paths(printer_bounds)
