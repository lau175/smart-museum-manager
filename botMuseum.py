from lib.mqttcli import Client
from lib.artworks import ArtBot
from lib.museum import MuseumBot
import time

mqtt = Client("museumbot", 'museum')
museum_bot = MuseumBot(mqtt)
museum_bot.start()

while 1:
	time.sleep(1)
