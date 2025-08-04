; Sliced with MACLab Gradient Slicer version 1.0.0 from an OpenVCAD model

M17													; enable steppers
M862.3 P "XL"										; printer model check
M862.5 P2											; g-code level check
M862.6 P"Input shaper"								; FW feature check
G90                                         		; use absolute coordinates
M83													; extruder relative mode
M555 X[min_x] Y[min_y] W[max_x] H[max_y]			; set print area
M862.1 T0 P0.4										; inform about nozzle diameter
M862.1 T1 P0.4										; inform about nozzle diameter
M862.1 T2 P0.4										; inform about nozzle diameter
M862.1 T3 P0.4										; inform about nozzle diameter
M862.1 T4 P0.4										; inform about nozzle diameter

M217 Z2.0											; set toolchange z hop to 2mm, or zhop variable from slicer if higher

; set bed and extruder temp for MBL
M140 S[bed_temperature]								; set bed temp
G0 Z5												; add Z clearance
M109 T0 R[idle_temperature]							; wait for temp


G28 XY												; Home XY
G1 F[travel_speed]									; try picking tool(s) used in print
T0 S1 L0 D0
T1 S1 L0 D0
T2 S1 L0 D0
T3 S1 L0 D0
T4 S1 L0 D0

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

; set extruder temps but do not wait, this just speeds things up
M104 T0 S[t0_temperature]
M104 T1 S[t1_temperature]
M104 T2 S[t2_temperature]
M104 T3 S[t3_temperature]
M104 T4 S[t4_temperature]

; Purge T0
G1 F24000
P0 S1 L2 D0											; park the tool
M109 T0 R[t0_temperature]							; wait for temp
T0 S1 L0 D0											; pick the tool
G92 E0												; reset extruder position
G0 X30 Y-7 Z10 F24000								; move close to the sheet's edge
G0 E30 X40 Z0.2 F170								; purge while moving towards the sheet
G0 X70 E9 F800										; continue purging and wipe the nozzle
G0 X73 Z0.05 F8000									; wipe, move close to the bed
G0 X76 Z0.2 F8000									; wipe, move quickly away from the bed
G1 E-1.2 F2400										; retract
G92 E0												; reset extruder position
P0 S1 L2 D0											; park the tool

# Purge T1
G1 F24000
M109 T1 R[t1_temperature]							; wait for temp
T1 S1 L0 D0											; pick the tool
G92 E0												; reset extruder position
G0 X150 Y-7 Z10 F24000								; move close to the sheet's edge
G0 E30 X140 Z0.2 F170								; purge while moving towards the sheet
G0 X110 E9 F800										; continue purging and wipe the nozzle
G0 X107 Z0.05 F8000									; wipe, move close to the bed
G0 X104 Z0.2 F8000									; wipe, move quickly away from the bed
G1 E-1.2 F2400										; retract
G92 E0												; reset extruder position
P0 S1 L2 D0											; park the tool

# Purge T2
G1 F24000
M109 T2 R[t2_temperature]							; wait for temp
T2 S1 L0 D0											; pick the tool
G92 E0												; reset extruder position
G0 X210 Y-7 Z10 F24000								; move close to the sheet's edge
G0 E30 X220 Z0.2 F170								; purge while moving towards the sheet
G0 X250 E9 F800										; continue purging and wipe the nozzle
G0 X253 Z0.05 F8000									; wipe, move close to the bed
G0 X256 Z0.2 F8000									; wipe, move quickly away from the bed
G1 E-1.2 F2400										; retract
G92 E0												; reset extruder position
P0 S1 L2 D0											; park the tool

# Purge T3
G1 F24000
M109 T3 R[t3_temperature]							; wait for temp
T3 S1 L0 D0											; pick the tool
G92 E0												; reset extruder position
G0 X330 Y-7 Z10 F24000								; move close to the sheet's edge
G0 E30 X320 Z0.2 F170								; purge while moving towards the sheet
G0 X290 E9 F800										; continue purging and wipe the nozzle
G0 X287 Z0.05 F8000									; wipe, move close to the bed
G0 X284 Z0.2 F8000									; wipe, move quickly away from the bed
G1 E-1.2 F2400										; retract
G92 E0												; reset extruder position
P0 S1 L2 D0											; park the tool

# Purge T4
G1 F24000
M109 T4 R[t4_temperature]							; wait for temp
T4 S1 L0 D0											; pick the tool
G92 E0												; reset extruder position
G0 X330 Y-4.5 Z10 F24000							; move close to the sheet's edge
G0 E30 X320 Z0.2 F170								; purge while moving towards the sheet
G0 X290 E9 F800										; continue purging and wipe the nozzle
G0 X287 Z0.05 F8000									; wipe, move close to the bed
G0 X284 Z0.2 F8000									; wipe, move quickly away from the bed
G1 E-1.2 F2400										; retract
G92 E0												; reset extruder position
P0 S1 L2 D0											; park the tool


G21													; set units to millimeters
G90													; use absolute coordinates
M83													; use relative distances for extrusion
M900 K0												; Filament gcode
M142 S36											; set heatbreak target temp

M109 T0 R[extruder_temperature]						; wait for temp
T0 S1 L0 D0											; pick the first tool
