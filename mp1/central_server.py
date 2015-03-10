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
	def __init__(self):
		super(Central, self).__init__()
		data = open('config.json')
		data = json.load(data)
		#self.model = int(model)
		self.port = int(data['central']['port'])	# get self port
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)	# form a socket
		self.s.bind((socket.gethostname(),self.port))
		self.nodes = dict()

		for key in data:
			if key != "central":
				self.nodes[data[key]['port']] = (socket.gethostname(),int(data[key]['port']))	# only work for locals

		self.sequence = Queue.Queue()	# thread safe queue to sequence messages

	"""run the central server"""
	@thread(True)
	def run(self):
		while True:
			message, addr = self.s.recvfrom(1024)
			if not message:
				continue
			self.sequence.put((message, addr))	# put the message into the sequencer


	@thread(True)
	def deliver(self):
		while True:
			try:
				message, addr = self.sequence.get()	# fetch the message from the sequencer
			except:
				continue
			if message:
				for port in self.nodes:
					self.s.sendto(message+' '+str(addr[1]), self.nodes[port])

	@thread(False)
	def quit(self):
		while True:
			if raw_input() is 'q':
				return

if __name__ == '__main__':
	central_server = Central()

	t_run = central_server.run()
	t_deliver = central_server.deliver()
	t_quit = central_server.quit()
	t_quit.join()