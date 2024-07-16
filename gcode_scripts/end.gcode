; Set to relative positioning
G91
; Move up 5mm
G1 Z5 F600

; Move to the front of the bed
G1 X5 Y5

; Set to absolute positioning
G90

; Turn off the hotend and bed
M140 S0 ; turn off heatbed
M104 S0 ; turn off temperature

; Turn off the fans and motors
M107 ; turn off fan
M84 X Y E ; disable motors