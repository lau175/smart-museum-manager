/*Author: Luca Tomaino (s263690)
Academic year: 2018/19*/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <string.h>
#include <ESP8266HTTPClient.h>

// Network parameters
const char* ssid = "iPhone di Luca Tomaino";
const char* password = "Cif313103";
const char* mqtt_server = "172.20.10.11";

bool START = false;
bool LIGHT = false;
bool HEAT = false;
bool a = true;

// Creation of an ESP8266WiFi object
WiFiClient espClient;
// Creation of a PubSubClient object
PubSubClient client(espClient);

// Function to connect to the WiFi network whose parameters are declared above
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int cnt = 0;

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    cnt++;
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

/* Function to implement a callback to subscribe the ESP to the initialization topic "system"
   and to the refreshment topic "ping" */
void callback(char* topic, byte* payload, unsigned int length) {
  /*Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  Serial.println(String(topic));*/
 
  if ((String(topic) == "system") || (String(topic) == "ping")) {
    START = true;
    //Serial.println(START);
    delay(500);
  } else if (String(topic) == "trigger/light") {
    LIGHT = true;
    //Serial.println(LIGHT);
    delay(500);
  } else if (String(topic) == "trigger/heat") {
    HEAT = true;
    //Serial.println(HEAT);
    delay(500);
  }

  // Subscription of the MQTT client to the topics mentioned before plus the two topics related
  // to the control of the lighting and heating systems
  client.subscribe("trigger/light");
  client.subscribe("trigger/heat");
  client.subscribe("system");
  client.subscribe("ping");
}

// Loop until the MQTT connection is established
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += "relay";
    
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      // Once connected, resubscribe to desired topics
      client.subscribe("trigger/light");
      client.subscribe("trigger/heat");
      client.subscribe("system");
      client.subscribe("ping");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000); // retry in 5 seconds
    }
  }
}

void httpConnect()
/* Function to establish an HTTP connection which is used to make a POST request to the room
   catalog, which is then able to include the current device connector to the device list */
{
  HTTPClient http; // declaration of HTTP object
  // opening the connection with the URL of the room catalog
  http.begin("http://172.20.10.11:9090/devices?id=2&sensors=RELAY1_RELAY2&board=arduino"); // opening the connection with the URL of the room catalog
  http.addHeader("Content-Type", "text/plain");
  // code response of the POST request
  int httpCode = http.POST("Message from Arduino board #2, containing two relays.");
  /*Serial.print("httpCode = ");
  Serial.println(httpCode);*/
  http.end(); // closing the HTTP connection
}

void setup() {
  Serial.begin(9600);
  setup_wifi();

  httpConnect();
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() { 
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  if (START) {
    if(a)
      Serial.write("X");
    
    a = false;

    if(Serial.available()){
      String code = "";
      code += Serial.read();
      int c = code.toInt();

      if(c == 210)
        client.publish("measure/light_stat","{\"msg\": 0}");
      else if(c == 211)
        client.publish("measure/light_stat","{\"msg\": 1}");
      else if(c == 200)
        client.publish("measure/heat_stat","{\"msg\": 0}");
      else if(c == 201)
        client.publish("measure/heat_stat","{\"msg\": 1}");
    }
        
    if(LIGHT) {
      Serial.write("L");
      LIGHT = false;
    }
    else if(HEAT) {
      Serial.write("H");
      HEAT = false;
    }
  }
}
