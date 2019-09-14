/*Author: Luca Tomaino (s263690)
Academic year: 2018/19*/

#include <SoftwareSerial.h>

int sensor_1 = 8;                     // pin to which motion sensor 1 is attached
int sensor_2 = 9;                     // pin to which motion sensor 1 is attached

// by default, no motion detected by the two sensors
int state_1 = LOW; 
int state_2 = LOW;

// variables to store the sensor status (value)
int val_1 = 0;
int val_2 = 0;

// assignment of software serial's pins
int espReceiver = 4; // ESP's TX connected here
int espTransmitter = 5; // ESP's RX connected here

// initialization of software serial port to let the Arduino board and the ESP8266 module communicate
SoftwareSerial ESPserial(espReceiver,espTransmitter);

// counters and flags to avoid too many alerts of motion sensors for one detection only
int cnt_in = 0;
bool flag_in = false;
int cnt_out = 0;
bool flag_out = false;

void setup()
{
  // initialize sensor as an input
  pinMode(sensor_1, INPUT);
  pinMode(sensor_2, INPUT);

  // initialization of software serial's pins
  pinMode(espReceiver, INPUT);
  pinMode(espTransmitter, OUTPUT);
  
  Serial.begin(9600);                 // initialize serial
  ESPserial.begin(9600);              // initialize software serial

  Serial.println("Ready.");
}

void loop()
{
  // initialization of topic and message to be sent to the ESP module
  int topic = 0;
  int msg = 0;

  char cmd = ESPserial.read();
  // Serial.println(cmd);

  /*if (cmd == 'X') {
    Serial.println("Received message on topic ''system'' (CODE: 20) or on topic ''ping'' (CODE:21).");
    }*/

  // read sensors' values
  val_1 = digitalRead(sensor_1);
  val_2 = digitalRead(sensor_2);

  if(motionDetect(val_1, state_1, 1) == 1)// motion sensor for people entering the room 
  {
    cnt_in ++;
    Serial.print("cnt_in = ");
    Serial.println(cnt_in);
    if (cnt_in == 200) {
      flag_in = true;
      cnt_in = 0;
      topic = 12;
      msg = 1;
      Serial.println("A person entered the room.");
      serialWriting(topic, msg);
      Serial.println("Publishing message ''in'' on topic ''measure/people/detection'' (CODE: 12/1).");
      delay(200);
    }
  }
 
  if(motionDetect(val_2, state_2, 2) == 1)// motion sensor for people exiting the room
  {
    cnt_out ++;
    Serial.print("cnt_out = ");
    Serial.println(cnt_out);
    if (cnt_out == 200) {
      flag_out = true;
      cnt_out = 0;
      topic = 12;
      msg = 0;
      Serial.println("A person went out from the room.");
      serialWriting(topic, msg);
      Serial.println("Publishing message ''out'' on topic ''measure/people/detection'' (CODE: 12/0).");
      delay(200);
    }
  }

  if (flag_in) {
    cnt_in = 0;
    flag_in = false;
  }

  if (flag_out) {
    cnt_out = 0;
    flag_out = false;
  }
}

int motionDetect(int val, int state, int ID)
/* function to detect the presence of a person (entering or exiting the controlled room)
 *  through the usage of the motion sensors attached to the board 
 *  PARAMETERS:
 *    - val: value related to the status of the motion sensor (HIGH if a person is detected)
 *    - state: the actual status of the motion sensor
 *    - ID: used to identify the sensor */
{
  if (val== HIGH)                     // check if the sensor is HIGH 
  {                 
    if (state == LOW) 
      state = HIGH;                   // update variable state to HIGH

    return 1;
  } 
  else 
  {
    if (state == HIGH)
        state = LOW;                  // update variable state to LOW
    
    return 0;
  }
}

void serialWriting(int top, int ms) 
/* function to write on the software serial channel between Arduino and the ESP module
 *  the topic and the message related to what has happened, following a proper protocol
 *  which assigns to each topic and message a numeric code 
 *  PARAMETERS:
 *  - top: topic to which the message will be published by the ESP module
 *  - msg: actual message to be published by the ESP module */
{
  if(ESPserial.available()) {
      ESPserial.write(top);
      ESPserial.write("/");
      ESPserial.write(ms);
      ESPserial.flush();
  }
}
