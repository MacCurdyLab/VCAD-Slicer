G4                              ; wait

G91                             ; relative positioning
G1 Z5 F6000                     ; Move bed down

P0 S1                           ; park tool

M104 T0 S0                      ; turn off extruder heaters

M140 S0                         ; turn off heatbed
M107                            ; turn off fan
M221 S100                       ; reset flow percentage
M84                             ; disable motors
M77                             ; stop print timer