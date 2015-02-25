from config import ServerConfig
from threading import Thread
from functools import wraps
from server import thread
import json
import socket
import time
import sys
import Queue

class Central(object):
	"""docstring for Central"""
	def __init__(self,model):
		super(Central, self).__init__()
		data = open('config.json')
		data = json.load(data)
		self.model = int(model)
		self.port = int(data['central']['port'])
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.bind((socket.gethostname(),self.port))
		self.sequence = Queue.Queue()	# thread safe queue to sequence messages

	"""run the central server"""
	@thread(True)
	def run(self):
		while True:
			pass

	@thread(True)
	def deliver(self):
		while True:
			pass

	@thread(False)
	def quit(self):
		while True:
			if raw_input() is 'q':
				return

if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.argv.append(raw_input('Enter consistency model 1. Linearizability 2. Sequential consistency 3. Eventual consistency, W = 1, R = 1 4. Eventual consistency, W = 2, R = 2 '))
	central_server = Central(sys.argv[1])

	t_run = central_server.run()
	t_deliver = central_server.deliver()
	t_quit = central_server.quit()
	t_quit.join()