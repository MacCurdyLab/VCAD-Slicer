import pyvcad as pv
import pyvcad_compilers as pvc
import outline_layer


class OutlineSlicer:
    def __init__(self, root, min, max, voxel_size, settings):
        self.settings = settings
        self.cross_sectioner = pvc.CrossSectionSlicer(root, min, max, voxel_size)
        self.min = min
        self.max = max
        self.voxel_size = voxel_size
        self.model_bottom_z = min.z

        # Compute the centering point based on the bed size
        printer_min = settings["printer_settings"]["dimensions"]["min"]
        printer_max = settings["printer_settings"]["dimensions"]["max"]
        self.center_point = ((printer_max[0] - printer_min[0]) / 2, (printer_max[1] - printer_min[1]) / 2)

        if settings["purge_tower_settings"]["use"]:
            self.use_purge_tower = True
            self.purge_min = settings["purge_tower_settings"]["min"]
            self.purge_max = settings["purge_tower_settings"]["max"]
            self.purge_tower_x_size = settings["purge_tower_settings"]["size"][0]
            self.purge_tower_y_size = settings["purge_tower_settings"]["size"][1]
            self.purge_tower_x_spacing = self.purge_tower_x_size + settings["purge_tower_settings"]["spacing"][0]
            self.purge_tower_y_spacing = self.purge_tower_y_size + settings["purge_tower_settings"]["spacing"][1]
            self.purge_tower_centers = []
        else:
            self.use_purge_tower = False
            self.purge_min = None
            self.purge_max = None
            self.purge_tower_x_size = None
            self.purge_tower_y_size = None
            self.purge_tower_x_spacing = None
            self.purge_tower_y_spacing = None
            self.purge_tower_centers = None

        self.layers = []

    def slice(self, ranges):
        if self.use_purge_tower:
            print("0. Generating purge tower base locations")
            self.compute_purge_tower_centers(ranges)
        print("1. Generating outlines")
        self.generate_outlines()
        print("2. Generating paths")
        self.generate_paths(ranges)
        print("3. Connecting paths")
        self.connect_paths()
        print("4.Centering paths on the bed")
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
            raise ValueError(
                "Not enough possible centers for the number of ranges. Please adjust the purge tower settings")

        for i in range(len(ranges)):
            self.purge_tower_centers.append((ranges[i][0], ranges[i][1], possible_centers[i]))

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
                new_layer = outline_layer.OutlineLayer(geometry_outlines, z, bead_width, layer_num, self.settings["slicer_settings"]["fill_with_infill"],self.purge_tower_centers,self.purge_tower_x_size, self.purge_tower_y_size)
                self.layers.append(new_layer)
                layer_num += 1
            else:
                print("\t-> Skipping layer at z = {}, no geometry found".format(z))
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
        i = 0
        for l in self.layers:
            future_layers = self.layers[i+1:]
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

    def visualize_paths(self, printer_bounds=None, name=None, figsize=(15, 15)):
        for l in self.layers:
            l.visualize_paths(printer_bounds, name, figsize)
