# Smart Museum Manager

## Hardware
#### ESP8266 Pinout
```
____________
|   1   2   |   1 - RX  5 - GPIO2
|   3   4   |   2 - VCC  6 - CH_EN
|   5   6   |   3 - GPIO0  7 - GND
|   7   8   |   4 - RST  8 - TX
____________     
```

#### ESP8266 - Arduino connection
```
ESP8266 - Arduino
 2    -    3.3V
 1    -     RX
 3    -     ***
 4    -     GND
 5    -      -
 6    -    3.3V
 7    -     GND
 8    -     TX
```
*** To flash the ESP link the GPI0 to GND, RST to GND. Unlink RST from GND. Wait the uploading time. Link the GPIO0 to 3.3V and Reset.
To make the ESP print on serial monitor, reset twice quickly.

#### Adafruit DHT - Raspberry pinout
```
DHT11 - Rpi
VCC   - 1
OUT   - 11
GND   - 6
```
## Room Catalog HTTP requests
Three http requests are used: GET to read the room catalg, POST to update the thresholds and to register new devices, DELETE to remove a registered device. The GET requests return jsons.</br>
Replace ```xxx.xxx.xxx.xxx``` with the rpi IP address.</br>
#### GET
```http://xxx.xxx.xxx.xxx:9090/broker``` to read the broker IP and port</br>
```http://xxx.xxx.xxx.xxx:9090/interacquisition``` to read the minutes between one acquisition and the next one</br>
```http://xxx.xxx.xxx.xxx:9090/timetable``` to read museum timetable</br>
```http://xxx.xxx.xxx.xxx:9090/th``` to read the thresholds</br>
#### POST
```http://xxx.xxx.xxx.xxx:9090/th?type=FIELD&val=VALUE``` to update the thresholds</br>  
FIELD is the threshold type (humidity, people, etc.)</br>
VALUE is the new threshold value</br>
```http://xxx.xxx.xxx.xxx:9090/devices?id=ID&sensors=SENSOR1_SENSOR2&board=BOARD``` to register a new device</br>
ID is the identification number of the device</br>
SENSORx is the type of acquisition (temperature, humidity, etc.)</br>
BOARD can be arduino or rpi</br></br>
#### DELETE
```http://xxx.xxx.xxx.xxx:9090/devices?id=ID&board=BOARD``` to remove a registered device</br>
ID is the identification number of the device</br>
BOARD can be arduino or rpi</br>

## ESP8266 "protocol" for topics and messages
```
Topic                         Message                                                   CODE/msg_CODE       
alert/temperature             {"msg":critical_value}                                    1/*value*
alert/humidity                {"msg":critical_value}                                    2/*value*
alert/people                  {"msg":critical_value}                                    3/*value*
alert/light_down              {"msg":"void"}                                            4/999
alert/closing                 {"msg":"void"}                                            5/999

measure/light_stat            {"msg":1} if lights on                                    6/*msg*
                              {"msg":0} if lights down 
measure/heat_stat             {"msg":1} if heating on                                   7/*msg*
                              {"msg":0} if heating down
measure/temperature           {"msg":measured_value}                                    8/*value*
measure/humidity              {"msg":measured_value}                                    9/*value*       
measure/people                {"msg":measured_value}                                    10/*value*
measure/people/detection      {"msg": "in"}  if a person enters                         12/1
                              {"msg": "out"} if a person exits                          12/0
                              
trigger/th                    {"msg":"void"}                                            17/999
trigger/light                 {"msg":"void"}                                            18/999  
trigger/heat                  {"msg":"void"}                                            19/999

system                        {"msg":"void"}                                            20/999

ping                          {"msg":"void"}                                            21/999
```
             
## Install mosquitto with websockets
Mosquitto with websockets allow to use the mqtt protocol from internet browser. Firefox is recommended. The websockets port is 9001.

#### Install the dependecies
```
$ sudo apt-get update
$ sudo apt-get install build-essential python quilt python-setuptools python3
$ sudo apt-get install libssl-dev
$ sudo apt-get install cmake
$ sudo apt-get install libc-ares-dev
$ sudo apt-get install uuid-dev
$ sudo apt-get install daemon
$ sudo apt-get install libwebsockets-dev
```

#### Download mosquitto
```
$ cd Downloads/
$ wget http://mosquitto.org/files/source/mosquitto-1.4.10.tar.gz
$ tar zxvf mosquitto-1.4.10.tar.gz
$ cd mosquitto-1.4.10/
$ sudo nano config.mk
```

#### Edit config.mk 
```
WITH_WEBSOCKETS:=yes
```

#### Build mosquitto
```
$ make
$ sudo make install
$ sudo cp mosquitto.conf /etc/mosquitto
```

#### Configure ports for mosquitto
Add the following lines to /etc/mosquitto/mosquitto.conf in the "Default Listener" section: 

```
port 1883
listener 9001
protocol websockets
```

#### Add user for mosquitto 

```
$ sudo adduser mosquitto
```

#### Reeboot computer

```
$ reboot
```

#### Run mosquitto

```
$ mosquitto -c /etc/mosquitto/mosquitto.conf
```

## Install the zbar shared library
```
$ apt-get install libzbar0
pip install zbar
```

## Install the Adafruit_DHT library
Python 2:
```
$ apt-get update
$ apt-get install python-pip
$ python -m pip install --upgrade pip setuptools wheel
$ pip install Adafruit_DHT
$ cd Adafruit_Python_DHT
$ python setup.py install
```

## Install the requirements
```
$ pip install -r requirements.txt
```

## Usage
* ___Mosquitto Broker___
Run ```$ mosquitto -c /etc/modquitto/mosquitto.conf -v```

* ___Room Catalog___
Run ```$ python roomCatalog.py``` to exploit the room catalog file stored in the ```jsons/``` folder. See the Room Catalog documentation for the http requests related to it.

* ___Raspberry Pi Connector___
Manages the DHT sensor's data acquisition and the ThingSpeak requests to update the channels.
Run ```$ python rpiConnector.py```

* ___Control System___
Controls if the measured parameters exceed a threshold and periodically sends to the Raspberry Pi connector the average number of people inside the room. This value is determined by receiving a trigger from the Arduino board when a person enters or exits the room.
Run ```$ python controlSystem.py```

* ___Freeboard___
Freeboard configuration to display the room parameters stored in an online dabase provided by ThingSpeak. The configuration is stored in the `lib/freeboard/` folder. To access the Freeboard web page run ```$ python freeboard.py```, which implement the freeboard web service.
Open `http://192.168.1.80:8080` in your favorite browser.

* ___Room manager Telegram bot___
Run ```$ python botMuseum.py``` to turn the bot on. It is reachable by searching `@smart_museum_bot` on Telegram

* ___QR Artworks Bot___
Run ```$ python botArtworks.py``` to turn the bot on. It is reachable by searching `@qr_temp_bot` on Telegram. The artworks qr codes are stored in the `qr_codes/` folder. The artworks database is stored in the `art_db/` folder

* __Starter__
Run ```$ ./starter.sh``` to start synchronously the data acquisition.
