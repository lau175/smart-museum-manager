# Author: Giuseppe Di Giacomo s263765
# Academic year: 2018/19

import paho.mqtt.client as PahoMQTT

class MyMQTT:


    def __init__(self, clientID, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self.clientID = clientID
        self._topic = []
        self._isSubscriber = False

        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(clientID, False)

        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        # todo devo scrivere "with result"?
        print("MQTT: '%s' connected to %s with result code: %d" % (clientID, self.broker, rc))

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        print ("MQTT: message received by " + clientID)
        print (msg.topic)
        print (msg.payload)
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, topic, msg):
        
        print("MQTT: '%s' published message '%s' with topic '%s'" % (clientID, msg, topic))
        # publish a message with a certain topic
        self._paho_mqtt.publish(topic, msg, 2)

    def mySubscribe(self, topic):
                
        print("MQTT: '%s' subscribed to  %s" % (clientID, topic))
        # subscribe for a topic
        self._paho_mqtt.subscribe(topic, 2)

        # just to remember that it works also as a subscriber
        self._isSubscriber = True
        # topic added to the list of topics to which the MQTT client subscribed
        self._topic.append(topic)

    def start(self):
        # manage connection to broker
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def stop(self):
        if self._isSubscriber:
            # remember to unsubscribe if it is working also as subscriber
            for t in self._topic:
                self._paho_mqtt.unsubscribe(t)

        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
