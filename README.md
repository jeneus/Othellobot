# Othellobot
Othellobot is an automated, 3-axis pick-and-place robotic platform that plays Othello against a human opponent on a physical 8x8 grid. Instead of flipping tokens on the board at the end of every turn, the colors of the cells change with respect to the state of the game. 

<img width="512" height="910" alt="unnamed" src="https://github.com/user-attachments/assets/19b32877-47c6-42c2-8de5-e4dd35383fba" />
<img width="512" height="288" alt="unnamed" src="https://github.com/user-attachments/assets/8f971992-41a4-441e-a794-52232dbe4bce" />

# Technical Specifications

| Specification Category | Axis / Parameter | Measured Metric |
| :--- | :--- | :--- |
| **Workspace / Travel Distance** | X-Axis Travel | 231.2 mm |
| | Y-Axis Travel | 264.8 mm |
| **Precision** | X-Axis Precision | 0.04 mm |
| | Y-Axis Precision | 0.015 mm |
| **Resolution** | X-Axis Resolution | < 0.01 mm |
| | Y-Axis Resolution | < 0.01 mm |
| **Max Velocity** | X-Axis Velocity | 0.33 m/s |
| | Y-Axis Velocity | 0.33 m/s |

# Mechanical & Electromechanical Design
The frame is constructed from 2020 extruded aluminum and 1/8" laser-cut cast acrylic sheets. Belt pulley systems coupled with microstepping-enabled stepper motors achieve precise X and Y-axis motion without sensor feedback. The custom Z-axis actuator uses a high-torque 360-degree servo motor and a rack-and-pinion mechanism equipped with a magnetic encoder for accurate vertical positioning. The end-effector uses a TPU-based suction cup connected to a 4.5V DC diaphragm vacuum pump (ZR370-02PM), a solenoid valve and a pressure sensor to reliably manipulate tokens on and across the board. Custom drag chains route along the linear rails to manage wiring. Various 3d-printed mounts for the belt drives, limit switches, motors, linear rails, and camera were designed in SolidWorks.

<img width="512" height="909" alt="unnamed" src="https://github.com/user-attachments/assets/4e706cb5-397e-4e64-86d7-8a1fd4dd580f" />

<table>
  <tr>
    <td align="center">
      <img src="images/exploded_end_effector_assembly.JPG" width="100%" alt="Exploded End Effector Assembly"><br/>
      <b>Exploded View of End Effector Assembly</b>
    </td>
    <td align="center">
      <img src="images/exploded_x_axis_assembly.JPG" width="100%" alt="Exploded X-Axis Drive Subassembly"><br/>
      <b>Exploded View of X-Axis Drive Subassembly</b>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="images/exploded_board_assembly.JPG" width="100%" alt="Exploded Board Assembly"><br/>
      <b>Exploded View of Board Assembly</b>
    </td>
    <td align="center">
      <img src="images/bot_layer_assembled.JPG" width="100%" alt="Bot Layer and Electronics Orthogonal View"><br/>
      <b>Bottom Layer of Robot Frame</b>
    </td>
  </tr>
</table>

# PCB & Electronics Design
The playing board integrates 64 individually addressable LEDs beneath a thin layer of PLA. A custom 4-layer PCB facilitates interfacing between the Arduino Nano, Raspberry Pi 4, and the peripheral electronics. The board features:
- TMC5262 Smart Motion Controllers and Stepper Motor drivers
- Dual voltage regulators (dedicated power for the LEDs/servo, and logic-level definition for the TMC5262s)
- Pressure sensor conditioning circuitry
- Centralized interfaces for motors, limit switches, the LED matrix, encoders, the vacuum pump, and the solenoid
- PCBs were soldered and tested by hand (soldering iron, heat gun, multimeter)
- All wires were crimped and managed by hand (JST-PH connectors, Dupont connectors, quick disconnected, ring terminals, zip ties, heat shrinks)
- Power supply is selected to handle worst-case maximum loading

<img src="images/pcb_schematic" width="100%" alt="Schematic of Main Othellobot PCB"><br/>
<img width="1254" height="816" alt="image" src="https://github.com/user-attachments/assets/c68a7c98-06e4-410a-a007-532e67bd2333" />
<img width="512" height="288" alt="unnamed" src="https://github.com/user-attachments/assets/3078c0f6-4eb6-4382-8de8-4a1b6b782d73" />

# Communications, AI & Embedded Software

Vision & AI: An OV2643 camera module tracks user moves using OpenCV for image processing (edge detection, centroid placement, image distortion correction, and interpolation). The game logic and opponent decision-making are driven by an AlphaZero reinforcement learning model built in PyTorch running on the Raspberry Pi 4 (or laptop).

<img width="640" height="480" alt="board_state_overlay" src="https://github.com/user-attachments/assets/76702032-2a80-4a2f-b1b5-336301e9441a" />

Firmware: The Arduino Nano operates on a custom state-machine architecture to transition smoothly between game states.

Driver Integration: The Nano communicates with the TMC5262 drivers via SPI using a completely hand-written software implementation for low-level motor control.

