from serializer import thread,serialize,deserialize
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
		self.counter = 0	# count the acks

		for key in data:
			if key != "central":
				self.nodes[key] = (socket.gethostname(),int(data[key]['port']))	# only work for locals

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
			ops,key,value,model,time_stamp,node = deserialize(message)
			if ops != 'ack':
				for port in self.nodes:
					self.s.sendto(message, self.nodes[port])
			else:
				self.counter += 1
				if self.counter == 4:
					self.counter = 0
					self.s.sendto(message,self.nodes[node])

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