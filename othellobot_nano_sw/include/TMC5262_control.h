#pragma once
#include <Arduino.h>
#include <ServoTimer2.h>
#include <FastLED.h>
#include <Wire.h>

// ARDUINO NANO PINS
const int DRV_EN_X = 5;
const int CS_X = 6;
const int DRV_EN_Y = 7;
const int CS_Y = 9;

const int SOL_PIN = A2;
const int PUMP_PIN = A3;
const int PRESSURE_SENSOR_PIN = A6;
const int SERVO_PIN = A0;
extern ServoTimer2 myservo;

extern uint32_t x_max;
extern uint32_t y_max;

const uint32_t FCLK = 16000000;
const uint32_t USC = 256;
const uint32_t FSC = 200;
const float MIN_TO_SEC = 60.0;
const byte AS5600_ADDRESS = 0x36;

// Ramp profile parameters
const int VSTART = 0;
const int VSTOP = 200;
const int V1 = 150;
const int V2 = 200;
const int VMAX = 250;
const uint16_t Ac1 = 40000;
const int Ac2 = 20000;
const int AMAX = 10000;
const int DMAX = 10000;
const int D2 = 20000;
const uint16_t D1 = 40000;

// --- CALIBRATION COORDINATES ---
const long BOARD_0_0_X = 9000; 
const long BOARD_0_0_Y = 70500; 

// Mechanical parameters
const float PULLEY_DIA = 0.01273239545; 
const float TOKEN_DIA_M = 0.023; 
extern uint32_t TOKEN_DIA_TMC;
extern int32_t end_pos;

extern int readings[5];
extern int readIndex;
extern long total;
extern int average;

// Stalling param
extern int8_t lref_sgt;

// LED parameters
const int NUM_LEDS = 64;
const int NRZ_PIN = A1;
const int BRIGHTNESS = 150;

// Game parameters
enum GameState 
{
  STARTING_BOARD,
  WAIT_FOR_MOVE,
  CPU_TURN
};

extern CRGB led_matrix[NUM_LEDS];
extern bool isLegalMove[NUM_LEDS];

// Function declarations
uint32_t vrpm_to_vtmc(float rpm);
unsigned long arpm_to_atmc(float arpm);
void tmc5262_config(int driver_CS);
void velocity_control(int driver_CS, int driver_EN, int vrpm, int arpm, int duration);
float homing_process(int driver_CS, int driver_EN);
uint32_t bitmask(uint32_t register_read, uint32_t mask, uint32_t new_bits);
void set_ramp_param(int driver_CS);
int32_t twos_complement(int32_t bits);
float vactual_to_vrpm(int32_t vactual);
float xlatch_to_dist(int32_t xlatch);
int32_t m_to_tmc_dist(float dist_m);
void move_to_target(int move[2], int CS_X, int CS_Y, uint32_t x_max, uint32_t y_max);
bool receiveFullBoardFromPython(uint32_t col_player, uint32_t col_cpu);
int readPhysicalSensors();
bool isMoveLegal(int index);
void flashErrorLED(int index);
void moveToCell(int row, int col);
void moveToSlot(int slotIndex);
void goDownAndGrab();
void goDownAndPlace();
void returnToHome();