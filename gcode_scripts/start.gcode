; Sliced with MACLab Gradient Slicer version 1.0.0 from an OpenVCAD model


; Set temperature
M104 S[extruder_temperature] ; set extruder temp
M140 S[bed_temperature]      ; set bed temp
M190 S[bed_temperature]      ; wait for bed temp
M109 S[extruder_temperature] ; wait for extruder temp

; Startup
G92 E0 ; Reset Extruder
G28    ; Home all axes
M107   ; Off Fan
G90    ; use absolute coordinates
M83    ; use relative distances for extrusion

; Set initial mixture
M163 S0 P0.0
M163 S1 P1.0
M164 S0

; Purging
G1 Z5.0 F3000                 ;Move Z Axis up little to prevent scratching of Heat Bed
G1 X0.1 Y20 Z0.8 F5000        ; Move to start position
G1 X0.1 Y200.0 Z1.2 F1500 E30 ; Draw the first line
G92 E0                        ; Reset Extruder
G1 X0.4 Y200.0 Z1.2 F3000     ; Move to side a little
G1 X0.4 Y20 Z1.2 F1500 E25    ; Draw the second line
G92 E0                        ; Reset Extruder
G1 Z2.0 F3000                 ; Move Z Axis up little to prevent scratching of Heat Bed
G1 X5 Y20 Z0.4 F3000.0        ; Move over to prevent blob squish
G1 X10 Y10 Z0.2 F600          ; Set feedrate
M221 S30                      ; Set flowrate
M207 F2100 S6 Z1              ; Set retraction settings

G92 E0