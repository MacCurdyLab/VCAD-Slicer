import math
import pyvcad as pv


class GCodeWriter:
    def __init__(self, filename, settings):
        # Make a new file for writing
        self.file = open(filename, "w")

        self.settings = settings

        self.filament_diameter = settings["printer_settings"]["filament_diameter"]
        self.bead_width = settings["printer_settings"]["nozzle_diameter"]
        self.desired_extrusion_feedrate = settings["printer_settings"]["speeds"]["first_layer_extrusion"]
        self.travel_speed = settings["printer_settings"]["speeds"]["travel"]
        self.start_script = settings["printer_settings"]["start_code_path"]
        self.end_script = settings["printer_settings"]["end_code_path"]
        self.volume_max = settings["printer_settings"]["dimensions"]["max"]
        self.volume_min = settings["printer_settings"]["dimensions"]["min"]

        self.use_retraction = settings["printer_settings"]["retraction"]["use"]
        self.retraction_required_distance = settings["printer_settings"]["retraction"]["required_distance"]
        self.retraction_length = settings["printer_settings"]["retraction"]["length"]
        self.retraction_speed = settings["printer_settings"]["retraction"]["speed"]
        self.un_retraction_length = settings["printer_settings"]["retraction"]["un_retract_length"]
        self.un_retraction_speed = settings["printer_settings"]["retraction"]["un_retract_speed"]
        self.coasting_distance = settings["printer_settings"]["coasting_distance"]
        self.lookahead_distance = settings["printer_settings"]["lookahead_distance"]
        self.z_lift_height = settings["printer_settings"].get("z_lift_height", 0.0)

        self.layer_height = settings["slicer_settings"]["layer_height"]
        self.flow_rate = settings["material_settings"]["flow_rate"] / 100.0
        self.extruder_temperature = self.settings["material_settings"]["extruder_temperature"]
        if "t0_temperature" in self.settings["material_settings"]:
            self.t0_temperature = self.settings["material_settings"]["t0_temperature"]
        else:
            self.t0_temperature = self.extruder_temperature

        if "t1_temperature" in self.settings["material_settings"]:
            self.t1_temperature = self.settings["material_settings"]["t1_temperature"]
        else:
            self.t1_temperature = self.extruder_temperature

        if "t2_temperature" in self.settings["material_settings"]:
            self.t2_temperature = self.settings["material_settings"]["t2_temperature"]
        else:
            self.t2_temperature = self.extruder_temperature

        if "t3_temperature" in self.settings["material_settings"]:
            self.t3_temperature = self.settings["material_settings"]["t3_temperature"]
        else:
            self.t3_temperature = self.extruder_temperature

        if "t4_temperature" in self.settings["material_settings"]:
            self.t4_temperature = self.settings["material_settings"]["t4_temperature"]
        else:
            self.t4_temperature = self.extruder_temperature
        self.idle_temperature = settings["material_settings"]["idle_temperature"]
        self.bed_temperature = self.settings["material_settings"]["bed_temperature"]
        self.mode = settings["gradient_settings"]["mode"]

        self.distance_to_next_mixture = -1
        self.next_lower = 0
        self.next_higher = 0

        self.num_regions = settings["gradient_settings"]["num_regions"]

        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.current_lower = 0
        self.current_higher = 0
        self.current_layer_number = 0
        self.current_feedrate = self.desired_extrusion_feedrate
        self.toolchange_inserted = False
        self.already_inserted_mixture_change = False

    def write_header(self, pmin, pmax):
        file_path = self.start_script

        replacement_dict = {
            "[bed_temperature]": str(self.bed_temperature),
            "[extruder_temperature]": str(self.extruder_temperature),
            "[t0_temperature]": str(self.t0_temperature),
            "[t1_temperature]": str(self.t1_temperature),
            "[t2_temperature]": str(self.t2_temperature),
            "[t3_temperature]": str(self.t3_temperature),
            "[t4_temperature]": str(self.t4_temperature),
            "[travel_speed]": str(self.travel_speed),
            "[idle_temperature]": str(self.idle_temperature),
            "[min_x]": str(pmin[0]),
            "[min_y]": str(pmin[1]),
            "[max_x]": str(pmax[0]),
            "[max_y]": str(pmax[1])
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
        file_path = self.end_script
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

        volume_to_extrude = segment_length * bead_width * layer_height # 2
        filament_radius = filament_diameter / 2
        filament_length = volume_to_extrude / (math.pi * filament_radius ** 2)

        return filament_length * self.flow_rate

    def write_retraction(self):
        self.file.write("G1 E-{:.4f} F{:.4f} ; Retract\n".format(self.retraction_length, self.retraction_speed))
        self.current_feedrate = self.retraction_speed

    def write_un_retraction(self):
        self.file.write("G1 E{:.4f} F{:.4f} ; Unretract\n".format(self.un_retraction_length, self.un_retraction_speed))
        self.current_feedrate = self.un_retraction_speed

    def write_big_retraction(self):
        self.file.write("G1 E-{:.4f} F{:.4f} ; Big retract\n".format(self.retraction_length * 4, self.retraction_speed))
        self.current_feedrate = self.retraction_speed

    def write_big_un_retraction(self):
        self.file.write("G1 E{:.4f} F{:.4f} ; Big unretract\n".format(self.un_retraction_length * 4, self.un_retraction_speed))
        self.current_feedrate = self.un_retraction_speed

    def write_travel(self, segment):
        start = segment.source()
        end = segment.target()
        self.current_x = end.x()
        self.current_y = end.y()

        length = math.sqrt((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2)

        should_retract = False
        if length > self.retraction_required_distance and self.use_retraction:
            should_retract = True

        if should_retract:
            self.write_retraction()

        # Only perform Z-lift if height is greater than zero and the travel distance is long enough
        if self.z_lift_height > 0 and length >= self.retraction_required_distance:
            # Step 1: Lift the nozzle
            lifted_z = self.current_z + self.z_lift_height
            self.file.write("G1 Z{:.4f} F{:.4f}; Z-lift\n".format(lifted_z, self.travel_speed))

            # Step 2: Perform XY travel move with lifted Z
            self.file.write("G1 X{:.4f} Y{:.4f} F{:.4f}; Travel XY\n".format(
                self.current_x, self.current_y, self.travel_speed))
            self.current_feedrate = self.travel_speed

            # Step 3: Lower back to printing height
            self.file.write("G1 Z{:.4f} F{:.4f}; Z-lower\n".format(self.current_z, self.travel_speed))
        else:
            # Just perform XY travel without changing Z
            self.file.write("G1 X{:.4f} Y{:.4f} F{:.4f}; Travel XY\n".format(
                self.current_x, self.current_y, self.travel_speed))
            self.current_feedrate = self.travel_speed

        if should_retract:
            self.write_un_retraction()

    def write_extrusion_line(self, segment, distance_to_next_travel):
        end = segment.target()
        self.current_x = end.x()
        self.current_y = end.y()

        current_segment_length = math.sqrt((end.x() - segment.source().x()) ** 2 + (end.y() - segment.source().y()) ** 2)
        # extrusion_amount = self.calculate_extrusion_amount(segment)
        # if self.current_feedrate != self.desired_extrusion_feedrate:
        #     self.current_feedrate = self.desired_extrusion_feedrate
        #     self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f} E{:.6f} F{:.4f}\n".format(
        #         self.current_x, self.current_y, self.current_z, extrusion_amount, self.current_feedrate))
        # else:
        #     self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f} E{:.6f}\n".format(
        #         self.current_x, self.current_y, self.current_z, extrusion_amount))

        if self.coasting_distance > 0 and distance_to_next_travel < self.coasting_distance:
            extrusion_amount = 0
        else:
            extrusion_amount = self.calculate_extrusion_amount(segment)

        if self.coasting_distance > 0 and distance_to_next_travel == current_segment_length:
            # Split the segment into two parts
            ratio = (current_segment_length - self.coasting_distance) / current_segment_length
            mid_x = segment.source().x() + ratio * (segment.target().x() - segment.source().x())
            mid_y = segment.source().y() + ratio * (segment.target().y() - segment.source().y())

            # First segment with extrusion
            if self.current_feedrate != self.desired_extrusion_feedrate:
                self.current_feedrate = self.desired_extrusion_feedrate
                self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f} E{:.6f} F{:.4f}\n".format(
                    mid_x, mid_y, self.current_z, extrusion_amount * ratio, self.current_feedrate))

                # Second segment without extrusion
                self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f} F{:.4f}; Coast\n".format(
                    self.current_x, self.current_y, self.current_z, self.current_feedrate))
            else:
                self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f} E{:.6f}\n".format(
                    mid_x, mid_y, self.current_z, extrusion_amount * ratio))

                # Second segment without extrusion
                self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f}; Coast\n".format(
                    self.current_x, self.current_y, self.current_z))
        else: # No splitting necessary of this segment
            if self.current_feedrate != self.desired_extrusion_feedrate:
                self.current_feedrate = self.desired_extrusion_feedrate
                self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f} E{:.6f} F{:.4f}\n".format(
                    self.current_x, self.current_y, self.current_z, extrusion_amount, self.current_feedrate))
            else:
                self.file.write("G1 X{:.4f} Y{:.4f} Z{:.4f} E{:.6f}\n".format(
                    self.current_x, self.current_y, self.current_z, extrusion_amount))

    def compute_distance_to_next_mixture(self, segments, paths):
        if self.distance_to_next_mixture == -1: # Must compute a new
            total_length = sum(math.sqrt((segment.target().x() - segment.source().x()) ** 2 +
                                         (segment.target().y() - segment.source().y()) ** 2)
                               for segment in segments)

            for lower, higher, is_extrusion, polyline in paths:
                if is_extrusion:
                    if lower != self.current_lower:  # This is a new mixture
                        self.distance_to_next_mixture = total_length
                        self.next_lower = lower
                        self.next_higher = higher
                        return total_length, lower, higher
                    total_length += sum(math.sqrt((segment.target().x() - segment.source().x()) ** 2 +
                                                  (segment.target().y() - segment.source().y()) ** 2)
                                        for segment in polyline.segments())
            # If we have not returned yet, there are no more mixtures
            self.distance_to_next_mixture = total_length
            return total_length, self.current_lower, self.current_higher

        else: # Return the previously computed distance minus this segment's length
            this_segment_length = math.sqrt((segments[0].target().x() - segments[0].source().x()) ** 2 +
                                            (segments[0].target().y() - segments[0].source().y()) ** 2)
            new_distance = self.distance_to_next_mixture - this_segment_length
            self.distance_to_next_mixture = new_distance
            return new_distance, self.next_lower, self.next_higher

    def write_layer(self, layer, future_layers):
        self.current_layer_number += 1
        self.current_z = layer.get_z_height()

        future_layer_paths = []
        for future_layer in future_layers:
            future_layer_paths.extend(future_layer.get_paths())

        # Write the z change
        self.write_comment("|===== Layer {} =====|".format(self.current_layer_number))
        self.write_comment("LAYER_CHANGE")
        self.write_comment("HEIGHT: {:.4f}".format(self.current_z))

        # Set the fan speed based on the layer number
        if self.current_layer_number == 1:
            self.file.write("M107 ; Turn fan off for first layer\n")
        elif self.current_layer_number == 2:
            self.file.write("M106 S80\n")
        elif self.current_layer_number == 3:
            self.file.write("M106 S160\n")
        elif self.current_layer_number == 4:
            self.file.write("M106 S230\n")
        else:
            self.file.write("M106 S255\n")

        # Set feedrate settings based on the layer number
        if self.current_layer_number == 1:
            self.desired_extrusion_feedrate = self.settings["printer_settings"]["speeds"]["first_layer_extrusion"]
        else:
            self.desired_extrusion_feedrate = self.settings["printer_settings"]["speeds"]["other_layer_extrusion"]

        # If this was the first layer, do initial un-retraction
        if self.current_layer_number == 1:
            self.file.write("G1 E1.2 F2400\t ;Initial un-retract\n")

        # if self.use_retraction:
        #     self.write_retraction()

        # Go to new z height
        self.file.write("G1 Z{:.4f}\n".format(self.current_z))

        # if self.use_retraction:
        #     self.write_un_retraction()

        def distance_to_next_travel(segments, paths):
            total_length = 0
            for segment in segments:
                total_length += math.sqrt((segment.target().x() - segment.source().x()) ** 2 + (
                        segment.target().y() - segment.source().y()) ** 2)

            for lower, higher, is_extrusion, polyline in paths:
                if not is_extrusion:
                    return total_length
                for segment in polyline.segments():
                    total_length += math.sqrt((segment.target().x() - segment.source().x()) ** 2 + (
                            segment.target().y() - segment.source().y()) ** 2)
            return total_length

        added_first_mixture = False
        range_index = 0
        paths = layer.get_paths()
        for lower, higher, is_extrusion, polyline in paths:
            segments = polyline.segments()
            index = 0
            for segment in polyline.segments():
                if is_extrusion:
                    if self.current_layer_number == 1 and not added_first_mixture:
                        self.write_mixing_ratios((lower, higher))
                        added_first_mixture = True

                    if self.distance_to_next_mixture <= 0:
                        self.distance_to_next_mixture = -1
                        self.already_inserted_mixture_change = False

                    if (self.lookahead_distance > 0):
                        # All future paths include this layer and all paths from future layers
                        all_future_paths = paths[range_index + 1:]
                        all_future_paths.extend(future_layer_paths)

                        mixture_distance, new_lower, new_higher = self.compute_distance_to_next_mixture(
                            segments[index:],
                            all_future_paths)
                        if mixture_distance < self.lookahead_distance and self.already_inserted_mixture_change == False:
                            self.write_mixing_ratios((new_lower, new_higher))
                            self.already_inserted_mixture_change = True
                    elif (self.lookahead_distance <= 0 and
                         self.do_mixing_ratios_diff((lower, higher))):
                            self.write_mixing_ratios((lower, higher))

                    if self.toolchange_inserted:
                        # Add a travel back to the segment
                        new_travel = pv.Segment2(pv.Point2(self.current_x, self.current_y), segment.source())
                        self.write_travel(new_travel)
                        self.write_big_un_retraction()
                        self.toolchange_inserted = False

                    if self.coasting_distance > 0:
                        distance = distance_to_next_travel(segments[index:], paths[range_index+1:])
                    else:
                        distance = 0
                    self.write_extrusion_line(segment, distance)
                else:
                    self.write_travel(segment)
                index += 1
            range_index += 1

    def write_comment(self, comment):
        self.file.write(";{}\n".format(comment))

    def do_mixing_ratios_diff(self, new_ranges):
        if new_ranges[0] != self.current_lower or new_ranges[1] != self.current_higher:
            return True
        return False

    def write_mixing_ratios(self, new_range):
        assert new_range[0] != 0.0 or new_range[1] != 1.0
        self.current_lower = new_range[0]
        self.current_higher = new_range[1]

        if self.mode == "mixture":
            def mixture_flow_rate_compensation(e0_pct, lower, upper):
                # Create a linear flow rate modifier based on the mixture ratio. When e0_pct is 0, the flow rate is lower.
                # When e0_pct is 1, the flow rate is upper.
                return (e0_pct * (upper - lower) + lower) * 100.0

            self.write_comment("Starting material mixture range: {:.4f} to {:.4f}".format(self.current_lower, self.current_higher))
            middle_point = (self.current_lower + self.current_higher) / 2.0

            if self.settings["gradient_settings"]["use_max_extents"]:
                if middle_point < 0.5:
                    middle_point = 0.0
                else:
                    middle_point = 1.0

            # Write the gcode for a mixing ratio change using the M163 command for extruder 0 and 1
            self.file.write("M163 S0 P{:.4f}\n".format(middle_point))
            self.file.write("M163 S1 P{:.4f}\n".format(1.0 - middle_point))

            # Save the new mixing ratios using the M164 command
            self.file.write("M164 S0\n")
        elif self.mode == "temperature":
            middle_point = (self.current_lower + self.current_higher) / 2.0
            if self.settings["gradient_settings"]["use_max_extents"]:
                if middle_point < 0.5:
                    middle_point = 0.0
                else:
                    middle_point = 1.0

            if self.settings["gradient_settings"]["material"] == "PLA":
                # Convert mixture to temperature using a linear mapping (205 to 240 degrees)
                middle_point_temperature = 210 + middle_point * 20
                # Compute new flow rate modifier based on the temperature (and therefore the foaming expansion)
                flow_rate = ((0.000008354790481 * (middle_point_temperature ** 3)) - (0.005370745309190 * (middle_point_temperature ** 2)) + (1.133743061069320 * middle_point_temperature) - 77.813511184263700) * 100.0
            elif self.settings["gradient_settings"]["material"] == "TPU":
                # Convert mixture to temperature using a linear mapping (190 to 220 degrees)
                middle_point_temperature = 190 + middle_point * 30
                # Compute new flow rate modifier based on the temperature (and therefore the foaming expansion)
                flow_rate = ((0.0003096373 * (middle_point_temperature ** 2)) - (0.1384006081 * middle_point_temperature) + 15.9560113114) * 100.0
            else:
                raise ValueError("Material not supported")

            self.write_comment("Starting temperature of {:.4f} as midpoint for range: {:.4f} to {:.4f}".format(
                middle_point_temperature, self.current_lower, self.current_higher))

            dock_extruder = self.settings["printer_settings"]["dock_extruder"]
            if dock_extruder:
                self.write_big_retraction()

                self.file.write("G1 F21000\t ; Setting travel speed\n")
                self.current_feedrate = 21000

                # Move to back left corner
                self.file.write("G1 X0 Y{:.4f} Z{:.4f} F21000\t; Move to back left corner\n".format(self.volume_max[1],self.current_z))

                # Park the tool so that the nozzle is sealed
                self.file.write("P0 S1 L2 D0\t; Park the tool\n")

                # Write the gcode for a temperature change using the M104 command and wait
                self.file.write("M109 T0 R{:.4f}\t; Set new temp and wait\n".format(middle_point_temperature))

                # Pick the tool back up
                self.file.write("T0 S1 L0 D0\t; Pick the tool back up and resume\n")
                self.file.write("G1 X0 Y{:.4f} Z{:.4f} F21000\t; Move to back left corner\n".format(self.volume_max[1], self.current_z))
                self.toolchange_inserted = True
            else:
                # Write the gcode for a temperature change using the M104 command and DO NOT wait
                self.file.write("M104 T0 S{:.4f}\t; Set new temp and DO NOT wait\n".format(middle_point_temperature))

            # Write the gcode for a flow rate change using the M221 command
            self.file.write("M221 T0 S{:.4f}\t; Set flow rate to compensate for expansion\n".format(flow_rate))
        elif self.mode == "switching":
            # Write the gcode needed to switch the extruder tool
            if self.num_regions > 5:
                raise ValueError("Switching mode only supports up to 5 regions. Please use 'mixture' or 'temperature' mode instead.")

            mid_point = (self.current_lower + self.current_higher) / 2.0
            # Map the mid_point's scale of 0.0 to 1.0 into to the extruder number integer (0 to self.num_regions)
            extruder_number = int(mid_point * (self.num_regions))

            # Park the current tool so that the nozzle is sealed
            self.file.write("P0 S1 L2 D0\t; Park the tool\n")

            # Pick the tool back up
            self.file.write(f"T{extruder_number} S1 L0 D0\t; Pick the new tool\n")
