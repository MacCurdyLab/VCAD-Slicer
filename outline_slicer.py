from libvcad import pyvcad as pv
import outline_layer


class OutlineSlicer:
    def __init__(self, root, min, max, voxel_size, settings):
        self.settings = settings
        self.cross_sectioner = pv.CrossSectionSlicer(root, min, max, voxel_size)
        self.min = min
        self.max = max
        self.voxel_size = voxel_size
        self.model_bottom_z = min.z

        # Compute the centering point based on the bed size
        printer_min = settings["printer_settings"]["dimensions"]["min"]
        printer_max = settings["printer_settings"]["dimensions"]["max"]
        self.center_point = ((printer_max[0] - printer_min[0]) / 2, (printer_max[1] - printer_min[1]) / 2)

        self.layers = []

    def slice(self, ranges):
        print("1. Generating outlines")
        self.generate_outlines()
        print("2. Generating paths")
        self.generate_paths(ranges)
        print("3. Connecting paths")
        self.connect_paths()
        print("4.Centering paths on the bed")
        self.center_paths()

    def generate_outlines(self):
        layer_height = self.settings["slicer_settings"]["layer_height"]
        bead_width = self.settings["printer_settings"]["nozzle_diameter"]
        num_walls = self.settings["slicer_settings"]["num_walls"]

        min_z = self.min.z
        max_z = self.max.z
        z = min_z
        layer_num = 1
        while z <= max_z:
            geometry_outlines = self.cross_sectioner.slice_geometry(z)
            if layer_num == 1:
                self.model_bottom_z = z

            if len(geometry_outlines) > 0:
                print("\t-> Generating paths for layer {} at z = {}".format(layer_num, z))
                new_layer = outline_layer.OutlineLayer(geometry_outlines, z, bead_width, layer_num)
                self.layers.append(new_layer)
                layer_num += 1
            else:
                print("\t-> Skipping layer at z = {}, not geometry found".format(z))
            z += layer_height

    def generate_paths(self ,ranges):
        for l in self.layers:
            layer_number = l.get_layer_num()
            print("\t-> Generating paths for layer {}".format(layer_number))
            l.generate_walls(ranges, self.cross_sectioner, layer_number % 2 == 0)

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
        print("5. Writing GCode")
        pmin, pmax = self.get_bounds()
        gcode_writer.write_header(pmin, pmax)
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

    def visualize_paths(self, printer_bounds=None):
        for l in self.layers:
            l.visualize_paths(printer_bounds)
