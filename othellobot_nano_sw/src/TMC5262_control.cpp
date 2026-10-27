#include "TMC5262_control.h"
#include <TMC5262.h>

const long CELL_SIZE_X = m_to_tmc_dist(0.0275);  
const long CELL_SIZE_Y = m_to_tmc_dist(0.0275);  
const long SLOT_0_X = 85500;     
const long SLOT_0_Y = 11500;    
const long SLOT_OFFSET = m_to_tmc_dist(0.0347);

int velocityToMicroseconds(int velocity) {
  velocity = constrain(velocity, -100, 100);
  return map(velocity, -100, 100, 1000, 2000);
}

uint32_t vrpm_to_vtmc(float rpm) {
  return (rpm / MIN_TO_SEC) * USC * FSC * (pow(2, 24) / FCLK);
}

unsigned long arpm_to_atmc(float arpm) {
  return (arpm / pow(MIN_TO_SEC, 2)) * USC * FSC * (pow(2, 41) / pow(FCLK, 2));
}

void tmc5262_config(int driver_CS) {
  tmc5262_writeRegister(driver_CS, TMC5262_PLL, 0x01E5);
  tmc5262_writeRegister(driver_CS, TMC5262_PLL, 0x11ED);

  while((tmc5262_readRegister(driver_CS, TMC5262_PLL) & 1) == 1) {}

  tmc5262_writeRegister(driver_CS, TMC5262_PLL, 0x71EC);
  tmc5262_writeRegister(driver_CS, TMC5262_GSTAT, 0b111111);

  tmc5262_writeRegister(driver_CS, TMC5262_DRV_CONF, bitmask(tmc5262_readRegister(driver_CS, TMC5262_DRV_CONF), 0b111111, 0b111101));
  tmc5262_writeRegister(driver_CS, TMC5262_IHOLD_IRUN, bitmask(tmc5262_readRegister(driver_CS, TMC5262_IHOLD_IRUN), 0xFFFF, 0xB123));
  tmc5262_writeRegister(driver_CS, TMC5262_COIL_INDUCT, 4400);
  tmc5262_writeRegister(driver_CS, TMC5262_GCONF, bitmask(tmc5262_readRegister(driver_CS, TMC5262_GCONF), 0b11111, 0b10110));
  tmc5262_fieldWrite(driver_CS, TMC5262_TCOOLTHRS_FIELD, 2000);
  tmc5262_writeRegister(driver_CS, TMC5262_CHOPCONF, bitmask(tmc5262_readRegister(driver_CS, TMC5262_CHOPCONF), 0b11, 0b11));
  tmc5262_writeRegister(driver_CS, TMC5262_SW_MODE, bitmask(tmc5262_readRegister(driver_CS, TMC5262_SW_MODE), 0b11111111111, 0b00010110011));
  tmc5262_writeRegister(driver_CS, TMC5262_TZEROWAIT, 3125);

  if (driver_CS == CS_Y) {
    tmc5262_writeRegister(driver_CS, TMC5262_SW_MODE, bitmask(tmc5262_readRegister(driver_CS, TMC5262_SW_MODE), 0b11111111111, 0b00000010001));
    tmc5262_writeRegister(driver_CS, TMC5262_GCONF, bitmask(tmc5262_readRegister(driver_CS, TMC5262_GCONF), 0b11111, 0b10100));
    tmc5262_fieldWrite(driver_CS, TMC5262_SGT_FIELD, (uint32_t)lref_sgt);
    tmc5262_fieldWrite(driver_CS, TMC5262_SHAFT_FIELD, 1);
    tmc5262_fieldWrite(CS_Y, TMC5262_SWAP_LR_FIELD, 0);
    tmc5262_fieldWrite(driver_CS, TMC5262_EN_SOFTSTOP_FIELD, 0);
  }
}

void velocity_control(int driver_CS, int driver_EN, int vrpm, int arpm, int dir) {
  tmc5262_writeRegister(driver_CS, TMC5262_RAMPMODE, dir);
  digitalWrite(driver_EN, LOW);
  tmc5262_writeRegister(driver_CS, TMC5262_AMAX, arpm_to_atmc(arpm));
  tmc5262_writeRegister(driver_CS, TMC5262_VMAX, vrpm_to_vtmc(vrpm));
}

float homing_process(int driver_CS, int driver_EN) {
  while((tmc5262_readRegister(driver_CS, TMC5262_RAMP_STAT) & 0b1) == 0b1) {
    velocity_control(driver_CS, driver_EN, 150, 20000, 0b1);
    delay(1000);
  }
  
  velocity_control(driver_CS, driver_EN, 150, 20000, 0b10);

  while(!((tmc5262_readRegister(driver_CS, TMC5262_RAMP_STAT) & 0b1) == 0b1)) {}

  tmc5262_writeRegister(driver_CS, TMC5262_XACTUAL, 0);
  velocity_control(driver_CS, driver_EN, 150, 20000, 0b1);

  if (driver_CS == CS_X) {
    while(!((tmc5262_readRegister(driver_CS, TMC5262_RAMP_STAT) & 0b10) == 0b10)) {}
    tmc5262_writeRegister(driver_CS, TMC5262_RAMPMODE, 0x3);
    end_pos = tmc5262_readRegister(driver_CS, TMC5262_XLATCH);
  } 
  else if (driver_CS == CS_Y) {
    while (!(tmc5262_fieldRead(CS_Y, TMC5262_VELOCITY_REACHED_FIELD))) {}
    tmc5262_fieldWrite(CS_Y, TMC5262_SG_STOP_FIELD, 1);
    while(!(tmc5262_fieldRead(CS_Y, TMC5262_EVENT_STOP_SG_FIELD))) {}
    tmc5262_fieldWrite(CS_Y, TMC5262_SG_STOP_FIELD, 0);
    end_pos = tmc5262_readRegister(driver_CS, TMC5262_XACTUAL);
    tmc5262_fieldWrite(CS_Y, TMC5262_EN_STEALTHCHOP_FIELD, 1);
  }

  tmc5262_writeRegister(driver_CS, TMC5262_XACTUAL, end_pos);
  tmc5262_writeRegister(driver_CS, TMC5262_XTARGET, end_pos);
  tmc5262_writeRegister(driver_CS, TMC5262_RAMPMODE, 0x0);

  set_ramp_param(driver_CS);

  return end_pos;
}

uint32_t bitmask(uint32_t register_read, uint32_t mask, uint32_t new_bits) {
  return (register_read & ~mask) | new_bits;
}

void set_ramp_param(int driver_CS) {
  tmc5262_writeRegister(driver_CS, TMC5262_VSTART, vrpm_to_vtmc(VSTART));
  tmc5262_writeRegister(driver_CS, TMC5262_VSTOP, VSTOP);
  tmc5262_writeRegister(driver_CS, TMC5262_V1, vrpm_to_vtmc(V1));
  tmc5262_writeRegister(driver_CS, TMC5262_V2, vrpm_to_vtmc(V2));
  tmc5262_writeRegister(driver_CS, TMC5262_VMAX, vrpm_to_vtmc(VMAX));
    
  tmc5262_writeRegister(driver_CS, TMC5262_A1, arpm_to_atmc(Ac1));
  tmc5262_writeRegister(driver_CS, TMC5262_A2, arpm_to_atmc(Ac2));
  tmc5262_writeRegister(driver_CS, TMC5262_AMAX, arpm_to_atmc(AMAX));
    
  tmc5262_writeRegister(driver_CS, TMC5262_DMAX, arpm_to_atmc(DMAX));
  tmc5262_writeRegister(driver_CS, TMC5262_D2, arpm_to_atmc(D2));
  tmc5262_writeRegister(driver_CS, TMC5262_D1, arpm_to_atmc(D1));
}

int32_t twos_complement(int32_t bits) {
  bits &= 0x00FFFFFF; 
  if (bits & 0x00800000) {
      bits = bits | 0xFF000000;
  }
  return bits;
}

float vactual_to_vrpm(int32_t vactual) {
  return twos_complement(vactual) * MIN_TO_SEC * (FCLK / pow(2, 24)) / (USC * FSC);
}

float xlatch_to_dist(int32_t xlatch) {
  return xlatch * PULLEY_DIA * PI * 100 / (USC * FSC);
}

int32_t m_to_tmc_dist(float dist_m) {
  return dist_m * (USC * FSC) / (PULLEY_DIA * PI);
}

void move_to_target(int move[2], int CS_X, int CS_Y, uint32_t x_max, uint32_t y_max) {
  uint32_t x_target = x_max * 0.95 - TOKEN_DIA_TMC * (8 - move[0]);
  uint32_t y_target = y_max * 0.95 - TOKEN_DIA_TMC * (8 - move[1]);

  tmc5262_writeRegister(CS_X, TMC5262_XTARGET, x_target);
  tmc5262_writeRegister(CS_Y, TMC5262_XTARGET, y_target);

  while(!(((tmc5262_readRegister(CS_X, TMC5262_RAMP_STAT) >> 9 & 1) == 1) && ((tmc5262_readRegister(CS_Y, TMC5262_RAMP_STAT) >> 9 & 1) == 1))) {}
}

bool receiveFullBoardFromPython(uint32_t col_player, uint32_t col_cpu) {
  static int led_index = 0;

  while (Serial.available() > 0) {
    byte colorCode = Serial.read();
    isLegalMove[led_index] = false; 

    if (colorCode == 0) led_matrix[led_index] = CRGB::Black;
    else if (colorCode == 1) led_matrix[led_index] = col_player;
    else if (colorCode == 2) led_matrix[led_index] = col_cpu;
    else if (colorCode == 3) {
      led_matrix[led_index] = CRGB::Black;
      isLegalMove[led_index] = true;       
    }

    led_index++; 

    if (led_index >= 64) {
      FastLED.show();
      led_index = 0;
      return true;
    }
  }
  return false; 
}

int readPhysicalSensors() {
  while (Serial.available() > 0) {
    Serial.read();
  }

  Serial.println("REQUEST_MOVE");
  unsigned long startTime = millis();
  while (!Serial.available()) {
    if (millis() - startTime > 3000) { 
      return -1; 
    }
  }

  String response = Serial.readStringUntil('\n');
  response.trim(); 

  if (response == "-1" || response == "NONE" || response == "") {
    return -1; 
  }

  int moveIndex = response.toInt();
  
  if (moveIndex == 0 && response != "0") {
    return -1; 
  }

  if (moveIndex >= 0 && moveIndex <= 63) {
    return moveIndex;
  }

  return -1; 
}

void flashErrorLED(int index) {
  led_matrix[index] = CRGB::Red;
  FastLED.show();
}

void moveToCell(int row, int col) {
  long targetX = BOARD_0_0_X + (col * CELL_SIZE_X); 
  long targetY = BOARD_0_0_Y + (row * CELL_SIZE_Y); 
  
  tmc5262_writeRegister(CS_X, TMC5262_XTARGET, targetX);
  tmc5262_writeRegister(CS_Y, TMC5262_XTARGET, targetY);
  
  while(!(((tmc5262_readRegister(CS_X, TMC5262_RAMP_STAT) >> 9 & 1) == 1) && 
          ((tmc5262_readRegister(CS_Y, TMC5262_RAMP_STAT) >> 9 & 1) == 1))) {
    delay(10);
  }
}

void moveToSlot(int slotIndex) {
  long targetX = SLOT_0_X;
  long targetY = SLOT_0_Y + (slotIndex * SLOT_OFFSET);
  
  tmc5262_writeRegister(CS_X, TMC5262_XTARGET, targetX);
  tmc5262_writeRegister(CS_Y, TMC5262_XTARGET, targetY);
  
  while(!(((tmc5262_readRegister(CS_X, TMC5262_RAMP_STAT) >> 9 & 1) == 1) && 
          ((tmc5262_readRegister(CS_Y, TMC5262_RAMP_STAT) >> 9 & 1) == 1))) {
    delay(10);
  }
}

void goDownAndGrab() {
  digitalWrite(PUMP_PIN, HIGH);
  digitalWrite(SOL_PIN, LOW);
  delay(200);

  average = 1023; 
  total = 5115;
  for(int i = 0; i < 5; i++) readings[i] = 1023;
  readIndex = 0;

  while(average >= 464) {
    myservo.write(velocityToMicroseconds(9)); 
    
    total = total - readings[readIndex];
    readings[readIndex] = analogRead(PRESSURE_SENSOR_PIN);
    total = total + readings[readIndex];
    
    readIndex = readIndex + 1;
    if (readIndex >= 5) readIndex = 0;
    average = total / 5;
    delay(5);
  }
  
  myservo.write(velocityToMicroseconds(0));
  delay(200);

  myservo.write(velocityToMicroseconds(-20));
  int zAngle = 4096;
  
  while (zAngle >= 100) {
    Wire.beginTransmission(AS5600_ADDRESS);
    Wire.write(0x0E); 
    Wire.endTransmission();

    Wire.requestFrom(AS5600_ADDRESS, (byte)2);

    if (Wire.available() >= 2) {
      zAngle = Wire.read();
      zAngle = (zAngle << 8) | Wire.read();
    }
    
    delay(5); 
  }
  
  myservo.write(velocityToMicroseconds(0));
}

void goDownAndPlace() {
  int zAngle;
  
  myservo.write(velocityToMicroseconds(17)); 
  zAngle = 0; 
  
  while (zAngle <= 600) {
    Wire.beginTransmission(AS5600_ADDRESS);
    Wire.write(0x0E);
    Wire.endTransmission();

    Wire.requestFrom(AS5600_ADDRESS, (byte)2);

    if (Wire.available() >= 2) {
      zAngle = Wire.read();
      zAngle = (zAngle << 8) | Wire.read();
    }
    delay(5);
  }
  
  myservo.write(velocityToMicroseconds(0));
  delay(100); 

  digitalWrite(SOL_PIN, HIGH); 
  digitalWrite(PUMP_PIN, LOW); 
  delay(300);

  myservo.write(velocityToMicroseconds(-20)); 
  zAngle = 4096; 
  
  while (zAngle >= 100) {
    Wire.beginTransmission(AS5600_ADDRESS);
    Wire.write(0x0E);
    Wire.endTransmission();

    Wire.requestFrom(AS5600_ADDRESS, (byte)2);

    if (Wire.available() >= 2) {
      zAngle = Wire.read();
      zAngle = (zAngle << 8) | Wire.read();
    }
    delay(5);
  }
  
  myservo.write(velocityToMicroseconds(0));
}

void returnToHome() {
  tmc5262_writeRegister(CS_X, TMC5262_XTARGET, x_max * 0.95);
  tmc5262_writeRegister(CS_Y, TMC5262_XTARGET, y_max * 0.95);
  
  while(!(((tmc5262_readRegister(CS_X, TMC5262_RAMP_STAT) >> 9 & 1) == 1) && 
          ((tmc5262_readRegister(CS_Y, TMC5262_RAMP_STAT) >> 9 & 1) == 1))) {
    delay(10);
  }
}