G4                              ; wait

G91                             ; relative positioning
G1 Z5 F6000                     ; Move head up

M104 S0							; turn off temperature
M140 S0							; turn off heatbed

G90							 	; absolute positioning
G1 X241 Y170 F3600 				; park

M221 S100                       ; reset flow percentage
M84                             ; disable motors
M77                             ; stop print timer

M572 S0							; reset PA
M593 X T2 F0					; disable IS
M593 Y T2 F0					; disable IS
M84 X Y E						; disable motors