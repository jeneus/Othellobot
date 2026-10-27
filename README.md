# Othellobot
Othellobot is a 3-axis pick-and-place robotic platform that plays Othello, a two player board game played on an 8 by 8 grid. 
<img width="490" height="872" alt="image" src="https://github.com/user-attachments/assets/07cb2f1a-e525-405f-812c-b34067a0bc01" />

# Mechanical/Electromechanical Design
The frame is assembled using 2020 extruded aluminum and 1/8" cast acrylic sheets. 
Belt pulley systems coupled with microstepping-enabled stepper motors achieve precise x and y-axis motion without sensor feedback. 
The custom z-axis actuator uses a high-torque 360 degrees servo motor and a rack-and-pinion mechanism equipped with a magnetic encoder to produce accurate vertical motion. 
The TPU-based suction cup is connected to a solonoid valve and diaphragm vacuum pump to pick up acrylic tokens. 
Custom drag chains hang off the linear rails to prevent wire tangling. 
# PCB/Electronics Design
The playing board is equipped with 64 individually addressable LEDs underneath a thin player of PLA. A pressure sensor is integrated to the pneumatic system to sense successful token grasping. The main PCB enables interfacing between the Arduino Nano, Raspberry Pi, and the rest of the electronics. It includes:
- TMC5262 Smart Motion Controller and Stepper Motor
- Voltage Regulators (one for providing power to LEDs/Servo, one for defining TMC5262 digital logic level)
- Pressure sensor circuitry
- Interfaces for motors, limit switches, LED matrix PCBs, encoder, vacuum pump, solenoid, and power terminal
#Communications/Embedded Software
- OV2643 Camera module detects user moves through OpenCV and image processing (edge detection, centroid placement, image distortion, interpolation)
- Nano communicates with TMC5262s through SPI; software handling TMC5262 was completely hand-written
- Nano uses a state machine structure to operate between game states
