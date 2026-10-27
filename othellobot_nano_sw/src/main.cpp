//this is the main file ran by the nano, managing the game and interfacing with all electronics/motors

#include <Arduino.h>
#include <SPI.h>
#include <math.h>
#include <FastLED.h>
#include "TMC5262_control.h"
#include "TMC5262.h"

uint32_t x_max = 0;
uint32_t y_max = 0;
int x_move = 0;
int y_move = 0;
String serialBuffer = "";
int8_t lref_sgt = -5;
int32_t end_pos = 0;
uint32_t TOKEN_DIA_TMC = 0.025;

ServoTimer2 myservo;
GameState currentState = STARTING_BOARD;
bool isPlayerTurn = true;
bool isLegalMove[NUM_LEDS] = {false};
CRGB led_matrix[NUM_LEDS];
unsigned long lastBlinkTime = 0;
bool blinkState = false;
const unsigned long blinkInterval = 500; 
int lastMovePlaced = -1;

uint32_t color_player = 0xFF00FF;    //magenta
uint32_t color_cpu = 0x00FF00;       //lime

int readings[5] = {1023, 1023, 1023, 1023, 1023}; 
int readIndex = 0;
long total = 5115; 
int average = 1023;

unsigned long lastCameraRequestTime = 0;

SPISettings mySetting(FCLK, MSBFIRST, SPI_MODE3);

void setup() 
{
  pinMode(DRV_EN_X, OUTPUT);
  pinMode(CS_X, OUTPUT);
  pinMode(DRV_EN_Y, OUTPUT);
  pinMode(CS_Y, OUTPUT);
  pinMode(SOL_PIN, OUTPUT);     
  pinMode(PUMP_PIN, OUTPUT);    
  myservo.attach(SERVO_PIN);    

  digitalWrite(DRV_EN_X, HIGH);
  digitalWrite(DRV_EN_Y, HIGH);
  digitalWrite(CS_X, HIGH);
  digitalWrite(CS_Y, HIGH);
  digitalWrite(SOL_PIN, HIGH);  

  FastLED.addLeds<WS2812B, NRZ_PIN, GRB>(led_matrix, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);

  SPI.begin();
  Wire.begin();
  
  Serial.begin(9600);
  Serial.setTimeout(100); 

  delay(1000);

  tmc5262_config(CS_X);
  tmc5262_config(CS_Y);

  x_max = homing_process(CS_X, DRV_EN_X);
  y_max = homing_process(CS_Y, DRV_EN_Y);

  while (Serial.available() > 0) {
    Serial.read(); 
  }
  
  Serial.println("ARDUINO_READY"); 
} 

void loop() 
{
  switch (currentState) 
  {
    case STARTING_BOARD:
      if (receiveFullBoardFromPython(color_player, color_cpu)) 
      {
        if (isPlayerTurn) 
          currentState = WAIT_FOR_MOVE; 
        else
          currentState = CPU_TURN;
      }
      break;

    case WAIT_FOR_MOVE:
      if (millis() - lastBlinkTime >= blinkInterval) 
      {
        lastBlinkTime = millis();
        blinkState = !blinkState; 
        for (int i = 0; i < NUM_LEDS; i++) 
        {
          if (isLegalMove[i]) 
          {
            led_matrix[i] = blinkState ? color_player : CRGB::Black; 
          }
        }
        FastLED.show(); 
      }

      if (millis() - lastCameraRequestTime >= 1500) {
        lastCameraRequestTime = millis();
        Serial.println("REQUEST_MOVE"); 
      }

      if (Serial.available() > 0) {
        String response = Serial.readStringUntil('\n');
        response.trim();
        
        while (Serial.available() > 0) Serial.read(); 
        
        if (response != "-1" && response != "NONE" && response != "") {
          lastMovePlaced = response.toInt();
          
          if (lastMovePlaced >= 0 && lastMovePlaced <= 63) {
            
            while (Serial.available() > 0) Serial.read(); 
            
            unsigned long waitTime = millis();
            while (Serial.available() < 64 && (millis() - waitTime < 500)) {
              delay(1);
            }
            
            if (receiveFullBoardFromPython(color_player, color_cpu)) {
              for (int i = 0; i < NUM_LEDS; i++) {
                if (isLegalMove[i]) led_matrix[i] = CRGB::Black; 
              }
              
              FastLED.show();
              delay(2000); 
            }
            
            isPlayerTurn = false;
            currentState = CPU_TURN; 
          }
        }
      }
      break;

    case CPU_TURN:
      if (Serial.available() > 0) {
        if (Serial.peek() == 'R') {
          String robotCmd = Serial.readStringUntil('\n');
          robotCmd.trim();
          
          if (robotCmd.startsWith("ROBOT")) {
            
            int firstComma = robotCmd.indexOf(',');
            int secondComma = robotCmd.indexOf(',', firstComma + 1);
            int thirdComma = robotCmd.indexOf(',', secondComma + 1);
            
            int slotIndex = robotCmd.substring(firstComma + 1, secondComma).toInt();
            int boardRow = robotCmd.substring(secondComma + 1, thirdComma).toInt();
            int boardCol = robotCmd.substring(thirdComma + 1).toInt();
            
            moveToSlot(slotIndex);         
            goDownAndGrab();               
            moveToCell(boardRow, boardCol); 
            goDownAndPlace();              
            returnToHome();                
            
            while (Serial.available() > 0) {
              Serial.read();
            }
            Serial.println("ROBOT_DONE");
          }
        } 
        else {
          if (receiveFullBoardFromPython(color_player, color_cpu)) {
            
            for (int i = 0; i < NUM_LEDS; i++) {
              if (isLegalMove[i]) {
                led_matrix[i] = CRGB::Black;
              }
            }
            FastLED.show(); 
            
            delay(2000); 
            
            lastCameraRequestTime = millis(); 
            lastBlinkTime = millis(); 
            
            isPlayerTurn = true;
            currentState = WAIT_FOR_MOVE; 
          }
        }
      }
      break;
  }
}

void tmc5262_readWriteSPI(uint16_t icID, uint8_t *data, uint16_t dataLength)
{
  SPI.beginTransaction(mySetting);
  digitalWrite(icID, LOW);

  for (uint16_t i = 0; i < dataLength; i++)
  {
    *(data + i) = SPI.transfer(*(data + i));
  }

  digitalWrite(icID, HIGH);
  SPI.endTransaction();
}