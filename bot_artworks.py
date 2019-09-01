from lib.mqttcli import Client
from lib.artworks import ArtBot
from lib.museum import MuseumBot
import time

mqtt = Client("artbot", 'art')
art_bot = ArtBot(mqtt)
art_bot.start()

while 1:
	time.sleep(1)
