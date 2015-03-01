import random
import socket
import json

class ServerConfig(object):
	"""docstring for ServerConfig"""
	def __init__(self,node):
		# load configuration from json file
		data = open('config.json')
		data = json.load(data)
		self.MAX = int(data[str(node)]['MAX'])
		self.port = int(data[str(node)]['port'])
		self.host = socket.gethostname()
		self.central = int(data['central']['port'])

	def get_time(self):
		return random.randint(0,self.MAX)


if __name__ == '__main__':
	config = ServerConfig()
	print config.get_time()