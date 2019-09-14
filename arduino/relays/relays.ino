/*Author: Luca Tomaino (s263690)
Academic year: 2018/19*/

#include <SoftwareSerial.h>

int LIGHT = 4; // pin of the relay module which controls the lighting system
int HEAT = 5; // pin of the relay module which controls the heating system

// assignment of software serial's pins
int espReceiver = 2; //ESP's TX connected here
int espTransmitter = 3; //ESP's RX connected here

// initialization of software serial port to let the Arduino board and the ESP8266 module communicate
SoftwareSerial ESPserial(espReceiver,espTransmitter);

void setup() {
  // initialization of the relay modules' pins, set to LOW at the beginning (systems off)
  pinMode(LIGHT, OUTPUT);
  digitalWrite(LIGHT, LOW);
  pinMode(HEAT, OUTPUT);
  digitalWrite(HEAT, LOW);
  
  Serial.begin(9600);                 // initialize serial
  ESPserial.begin(9600);              // initialize software serial

  Serial.println("Ready.");
}

void loop() {
  // the device works if there is software serial connection between Arduino and ESP module
  while (ESPserial.available()) {

    char cmd = ESPserial.read(); // char sent by ESP module to control the relay modules
    // Serial.println(cmd);

    if (cmd == 'X') {
      Serial.println("Received message on topic ''system'' (CODE: 20) or on topic ''ping'' (CODE: 21).");
    }

    /* the Arduino writes on the software serial port some codes corresponding
     *  to what has happened and depending on which relay has been activated */
    if (cmd == 'L') {
      if (digitalRead (LIGHT) == HIGH) {
        digitalWrite (LIGHT, LOW);
        ESPserial.write(210);
        Serial.println("Received message on topic ''trigger/light'' (CODE: 18). Lights status: OFF.");
        Serial.println("Publishing message ''0'' on topic ''measure/light_stat''.");
      }
      else {
        digitalWrite (LIGHT, HIGH);
        ESPserial.write(211);
        Serial.println("Received message on topic ''trigger/light'' (CODE: 18). Lights status: ON.");
        Serial.println("Publishing message ''1'' on topic ''measure/light_stat''.");
      }
    } else if(cmd == 'H') {
      if (digitalRead(HEAT) == HIGH) {
        digitalWrite(HEAT, LOW);
        ESPserial.write(200);
        Serial.println("Received message on topic ''trigger/heat'' (CODE: 19). Heat status: OFF.");
        Serial.println("Publishing message ''0'' on topic ''measure/heat_stat''.");
      }
      else {
        digitalWrite(HEAT, HIGH);
        ESPserial.write(201);
        Serial.println("Received message on topic ''trigger/heat'' (CODE: 19). Heat status: ON.");
        Serial.println("Publishing message ''1'' on topic ''measure/heat_stat''.");
      }
    }
  }
}
