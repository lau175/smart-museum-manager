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
VCC   - 3.3V
OUT   - 17
GND   - GND
```
## Room Catalog HTTP requests
Two http requests are used: GET to read the room catalg, POST to update it. The requests return jsons.
#### GET
```192.168.1.164:9090/broker``` to read the broker IP and port</br>
```192.168.1.164:9090/interacquisition``` to read the minutes between one acquisition and the next one</br>
```192.168.1.164:9090/timetable``` to read museum timetable</br>
```192.168.1.164:9090/th``` to read the thresholds</br>

#### POST
```192.168.1.164:9090/th``` to update the room catalog  

## ESP8266 "protocol" for topics and messages
```
Topic                         Message                                                   CODE/msg_CODE       
alert/temperature             {"msg":critical_value}                                    1/*value*
alert/humidity                {"msg":critical_value}                                    2/*value*
alert/people                  {"msg":critical_value}                                    3/*value*
alert/light_down              {"msg":"void"}                                            4/999
alert/closing                 {"msg":"void"}                                            5/999

measure/light_stat            {"msg":1 if lights on, 0 if lights down}                  6/*msg*
measure/heat_stat             {"msg":1 if heating on, 0 if heating down}                7/*msg*
measure/temperature           {"msg":measured_value}                                    8/*value*
measure/humidity              {"msg":measured_value}                                    9/*value*       
measure/people                {"msg":measured_value}                                    10/*value*
measure/light                 {"msg":measured_value}                                    11/*value*
measure/people/detection      {"msg": "in" if a person enters, "out" if a person exits} 12/1 for "in", 12/0 for "out"

update                        {"msg" : "people"}                                        13/1
update                        {"msg" : "timeout", for the timeout of lights}            14/1
update                        {"msg" : "max_temp"}                                      15/1
update                        {"msg" : "min_temp"}                                      16/1

trigger/th                    {"msg":"void"}                                            17/999
trigger/light                 {"msg":"void"}                                            18/999  
trigger/heat                  {"msg":"void"}                                            19/999

system                        {"msg":"void"}                                            20/999

ping						  {"msg":"void"}
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

* ___Raspberry Pi software___
Manages the DHT sensor's data acquisition and the ThingSpeak requests to update the channels.
Run ```$ python rpi.py```

* ___Freeboard___
Freeboard configuration to display the room parameters stored in an online dabase provided by ThingSpeak. The configuration is stored in the `freeboard/` folder. To access the Freeboard web page run ```$ python freeboard.py```, which implement the freeboard web service.
Open `http://192.168.1.80:8080` in your favorite browser.

* ___Room manager Telegram bot___
Run ```$ python bot\_museum.py``` to turn the bot on. It is reachable by searching `@smart_museum_bot` on Telegram

* ___QR Artworks Bot___
Run ```$ python bot\_artworks.py``` to turn the bot on. It is reachable by searching `@qr_temp_bot` on Telegram. The artworks qr codes are stored in the `qr_codes/` folder. The artworks database is stored in the `art_db/` folder

* __Starter__
Run ```$ ./starter.sh``` to start synchronously the data acquisition.
