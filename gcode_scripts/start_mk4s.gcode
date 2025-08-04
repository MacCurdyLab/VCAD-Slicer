; Sliced with MACLab Gradient Slicer version 1.0.0 from an OpenVCAD model

; Print progress reset
M73 P0 R15
M73 Q0 S16

; Speeds and accelerations
M201 X4000 Y4000 Z200 E2500 						; sets maximum accelerations, mm/sec^2
M203 X300 Y300 Z40 E100 							; sets maximum feedrates, mm / sec
M204 P4000 R1200 T4000								; sets acceleration (P, T) and retract acceleration (R), mm/sec^2
M205 X8.00 Y8.00 Z2.00 E10.00 						; sets the jerk limits, mm/sec
M205 S0 T0 											; sets the minimum extruding and travel feed rate, mm/sec

M17													; enable steppers
M862.1 P0.4 A0 F0 									; nozzle check
M862.3 P "MK4S" 									; printer model check
M862.5 P2 											; g-code level check
M862.6 P"Input shaper" 								; FW feature check
M115 U6.1.3+7898									; FW version check
G90                                         		; use absolute coordinates
M83													; extruder relative mode
M555 X[min_x] Y[min_y] W[max_x] H[max_y]			; set print area

; set bed and extruder temp for MBL
M140 S[bed_temperature]								; set bed temp
G0 Z5												; add Z clearance
M104 T0 S170										; set level temp
M109 T0 R170 										; wait for temp

M84 E 												; turn off E motor

G28 												; home all without mesh bed level
G1 X42 Y-4 Z5 F4800
M302 S160 											; lower cold extrusion limit to 160C
G1 E-2 F2400 										; retraction
M84 E 												; turn off E motor
G29 P9 X10 Y-4 W32 H4
M106 S100											; turn on fan
G0 Z40 F10000
M190 S[bed_temperature] 							; wait for bed temp
M107												; turn off fan

; MBL
M84 E 												; turn off E motor
G29 P1 												; invalidate mbl & probe print area
G29 P1 X0 Y0 W50 H20 C 								; probe near purge place
G29 P3.2 											; interpolate mbl probes
G29 P3.13 											; extrapolate mbl outside probe area
G29 A 												; activate mbl

; prepare for purge
M104 S[extruder_temperature]						; set extruder temp
G0 X0 Y-4 Z15 F4800 								; move away and ready for the purge
M109 S[extruder_temperature]						; wait for temp

; Extrude purge line
G92 E0 												; reset extruder position
G1 E2 F2400 										; deretraction after the initial one before nozzle cleaning
G0 E7 X15 Z0.2 F500 								; purge
G0 X25 E4 F500 										; purge
G0 X35 E4 F650 										; purge
G0 X45 E4 F800 										; purge
G0 X48 Z0.05 F8000 									; wipe, move close to the bed
G0 X51 Z0.2 F8000 									; wipe, move quickly away from the bed

G92 E0
M221 S100 											; set flow to 100%
G21 												; set units to millimeters
G90 												; use absolute coordinates
M83 												; use relative distances for extrusion
M900 K0.05											; Filament gcode (linear advance)
M572 S0.036 										; Filament gcode (pressure advance)

M142 S36 											; set heatbreak target temp
M107												; turn off fan
