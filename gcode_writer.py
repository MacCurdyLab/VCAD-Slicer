import math


class GCodeWriter:
    def __init__(self, filename, filament_diameter, layer_height, bead_width, flow_rate=1.0):
        # Make a new file for writing
        self.file = open(filename, "w")

        self.filament_diameter = filament_diameter
        self.layer_height = layer_height
        self.bead_width = bead_width
        self.flow_rate = flow_rate
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.current_lower = 0
        self.current_higher = 0
        self.current_layer_number = 0

    def write_header(self, extruder_temperature=200, bed_temperature=60):
        file_path = "gcode_scripts/start.gcode"

        replacement_dict = {
            "[bed_temperature]": str(bed_temperature),
            "[extruder_temperature] ": str(extruder_temperature)
        }

        # Read the start gcode from the file
        with open(file_path, "r") as start_gcode_file:
            start_gcode = start_gcode_file.read()
            # Replace the placeholders with the actual values
            for key, value in replacement_dict.items():
                start_gcode = start_gcode.replace(key, value)
            # Write the start gcode to the file
            self.file.write(start_gcode)

    def write_footer(self):
        file_path = "gcode_scripts/end.gcode"
        # Read the end gcode from the file
        with open(file_path, "r") as end_gcode_file:
            end_gcode = end_gcode_file.read()
            # Write the end gcode to the file
            self.file.write(end_gcode)

    def calculate_extrusion_amount(self, segment):
        """ Calculate the amount of extrusion needed for the segment using the capsule model."""
        source = segment.source()
        end = segment.target()
        segment_length = math.sqrt((end.x() - source.x()) ** 2 + (end.y() - source.y()) ** 2)
        bead_width = self.bead_width
        layer_height = self.layer_height
        filament_diameter = self.filament_diameter

        # Calculate the amount of filament needed for this segment. This can be done using the capsule model.
        # The capsule model is a simplification of the actual extrusion process, but it is a good approximation.
        # The capsule model assumes that the extruded filament has a squished circular cross-section that forms a
        # capsule shape. The capsule shape has a height of the layer height.
        area_of_rectangle = bead_width * layer_height
        area_of_circle = math.pi * (layer_height / 2) ** 2
        cross_sectional_area = area_of_rectangle + area_of_circle
        segment_volume = segment_length * cross_sectional_area

        filament_radius = filament_diameter / 2
        filament_length = segment_volume / (math.pi * filament_radius ** 2)

        return filament_length * self.flow_rate

    def write_travel(self, segment):
        start = segment.source()
        end = segment.target()
        self.current_x = end.x()
        self.current_y = end.y()

        length = math.sqrt((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2)

        retract = False
        if length > 6.0:
            retract = True

        if retract:
            self.file.write("G10 ; retract\n")

        # Write the gcode for a travel move
        self.file.write("G0 X{} Y{} Z{}\n".format(self.current_x, self.current_y, self.current_z))

        if retract:
            self.file.write("G11 ; un-retract\n")

    def write_extrusion_line(self, segment):
        end = segment.target()
        self.current_x = end.x()
        self.current_y = end.y()
        extrusion_amount = self.calculate_extrusion_amount(segment)

        # Write the gcode for an extrusion move
        self.file.write("G1 X{} Y{} Z{} E{}\n".format(self.current_x, self.current_y, self.current_z, extrusion_amount))

    def write_layer(self, layer):
        self.current_layer_number += 1
        self.current_z = layer.get_z_height()

        # Write the z change
        self.write_comment("Layer {}".format(self.current_layer_number))
        self.file.write("G0 Z{}\n".format(self.current_z))

        for lower, higher, is_extrusion, polyline in layer.get_paths():
            for segment in polyline.segments():
                if is_extrusion:
                    if self.do_mixing_ratios_diff((lower, higher)):
                        self.write_mixing_ratios((lower, higher))
                    self.write_extrusion_line(segment)
                else:
                    self.write_travel(segment)

    def write_comment(self, comment):
        self.file.write("; {}\n".format(comment))

    def do_mixing_ratios_diff(self, new_ranges):
        if new_ranges[0] != self.current_lower or new_ranges[1] != self.current_higher:
            return True
        return False

    def write_mixing_ratios(self, new_range):
        assert new_range[0] != 0.0 or new_range[1] != 1.0
        self.current_lower = new_range[0]
        self.current_higher = new_range[1]
        self.write_comment("Starting material range: {} to {}".format(self.current_lower, self.current_higher))
        middle_point = (self.current_lower + self.current_higher) / 2.0
        # Write the gcode for a mixing ratio change using the M163 command for extruder 0 and 1
        self.file.write("M163 S0 P{}\n".format(middle_point))
        self.file.write("M163 S1 P{}\n".format(1.0 - middle_point))

        # Save the new mixing ratios using the M164 command
        self.file.write("M164 S0\n")