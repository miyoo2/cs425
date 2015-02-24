from config import ServerConfig
from threading import Thread
from functools import wraps
import socket
import time
import sys
import Queue

# function wrapper 
def thread(daemon):
	def decorator(f):
		@wraps(f)
		def wrapper(*args, **kwargs):
			worker = Thread(target=f,args=args,kwargs=kwargs)
			worker.daemon = daemon
			worker.start()
			return worker
		return wrapper
	return decorator

# major server class
class Server(object):
	"""docstring for Server"""
	def __init__(self):
		super(Server, self).__init__()
		self.config = ServerConfig()
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.bind((self.config.host,self.config.port))
		self.message = Queue.Queue()	# A thread safe queue to implement FIFO ordering
		self.dest = Queue.Queue()

	# thread for listening
	@thread(True)
	def listen(self):
		while True:
			message, addr = self.s.recvfrom(1024)
			print "Receive %s from %s, max delay is %s, system time is %s" %(message, addr, self.config.MAX, str(time.time()))
			print "Enter your command here : "


	# main thread read and write
	@thread(False)
	def read(self):
		while True:
			cmd = raw_input("Enter your command here : ")

			if cmd.startswith('q'):
				return

			elif cmd.startswith('Send'):
				cmd = cmd.split(' ')
				self.message.put(cmd[1])
				""" if host is not provided, assume it's local server """
				try:
					self.dest.put(cmd[2])
				except:
					self.dest.put(self.config.host)
					cmd.append(self.config.host)

				print "Send %s to %s, system time is %s" %(str(cmd[1]),str(cmd[2]),str(time.time()))

	# thread for sending messages
	@thread(True)
	def send(self):
		while True:
			message = self.message.get()	# get the message and host atomically
			dest = self.dest.get()
			addr = (dest,self.config.port)
			time.sleep(self.config.get_time())	# simulate delay for message delivery
			self.s.sendto(message, addr)


if __name__ == '__main__':
	my_server = Server()
	t_listen = my_server.listen()
	t_send = my_server.send()
	t_read = my_server.read()
	t_read.join()	# wait for only this thread to end, others will be killed as soon as main thread ends
