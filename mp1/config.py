import random
import socket

class ServerConfig(object):
	"""docstring for ServerConfig"""
	def __init__(self):
		# 10s as max delay
		self.MAX = 10
		self.port = 12345
		self.host = socket.gethostname()

	def get_time(self):
		return random.randint(0,self.MAX)


if __name__ == '__main__':
	config = ServerConfig()
	print config.get_time()