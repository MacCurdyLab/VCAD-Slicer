; Sliced with MACLab Gradient Slicer version 1.0.0 from an OpenVCAD model

M17													; enable steppers
M862.3 P "XL"										; printer model check
M862.5 P2											; g-code level check
M862.6 P"Input shaper"								; FW feature check
G90                                         		; use absolute coordinates
M83													; extruder relative mode
M555 X[min_x] Y[min_y] W[max_x] H[max_y]			; set print area
M862.1 T0 P0.4										; inform about nozzle diameter
M862.1 T0 P0.4										; inform about nozzle diameter

; turn off unused heaters
M104 T1 S0
M104 T2 S0
M104 T3 S0
M104 T4 S0

M217 Z2.0											; set toolchange z hop to 2mm, or zhop variable from slicer if higher

; set bed and extruder temp for MBL
M140 S[bed_temperature]								; set bed temp
G0 Z5												; add Z clearance
M109 T0 R[idle_temperature]							; wait for temp


G28 XY												; Home XY
G1 F[travel_speed]									; try picking tool(s) used in print
T0 S1 L0 D0
; TODO- add support for more tools here

T0 S1 L0 D0											; select tool that will be used to home & MBL

; home Z with MBL tool
M84 E 												; turn off E motor
G28 Z												; home Z
G0 Z5												; add Z clearance

M104 T0 S[idle_temperature]							; set idle temp
M190 S[bed_temperature]								; wait for bed temp

G29 G												; absorb heat into bed
M109 T0 R[idle_temperature]							; wait for temp

; MBL
M84 E												; turn off E motor
G29 P1												; invalidate mbl & probe print area
G29 P1 X30 Y0 W50 H20 C								; probe near purge place
G29 P3.2											; interpolate mbl probes
G29 P3.13											; extrapolate mbl outside probe area
G29 A												; activate mbl
G1 Z10 F720											; move away in Z
G1 F[travel_speed]									; set travel speed
P0 S1 L1 D0											; park the tool
M104 T0 S[extruder_temperature]						; set extruder temp

; purge initial tool
G1 F24000
P0 S1 L2 D0											; park the tool
M109 T0 R[extruder_temperature]						; wait for temp
T0 S1 L0 D0											; pick the tool
G92 E0												; reset extruder position

G0 X30 Y-7 Z10 F24000								; move close to the sheet's edge
G0 E30 X40 Z0.2 F170								; purge while moving towards the sheet
G0 X70 E9 F800										; continue purging and wipe the nozzle
G0 X73 Z0.05 F8000									; wipe, move close to the bed
G0 X76 Z0.2 F8000									; wipe, move quickly away from the bed
G92 E0												; reset extruder position

G1 E-1.2 F2400										; retract
G92 E0												; reset extruder position
G21													; set units to millimeters
G90													; use absolute coordinates
M83													; use relative distances for extrusion
M900 K0												; Filament gcode
M142 S36											; set heatbreak target temp
