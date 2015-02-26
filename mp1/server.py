from config import ServerConfig
from threading import Thread
from functools import wraps
from datetime import datetime
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
	def __init__(self,node):
		super(Server, self).__init__()
		self.config = ServerConfig(node)
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.bind((self.config.host,self.config.port))
		self.message = Queue.Queue()	# A thread safe queue to implement FIFO ordering
		self.dest = Queue.Queue()
		self.inbox = Queue.Queue()
		self.replica = dict()	# key-value store

	# thread for listening
	@thread(True)
	def listen(self):
		while True:
			message, addr = self.s.recvfrom(1024)	# 1024 the size
			if not message:
				continue
			self.inbox.put((message, addr))
			#print "Receive %s from %s, max delay is %s, system time is %s" %(message, addr, self.config.MAX, str(time.time()))
			#print "Enter your command here : "


	# main thread read and write
	@thread(False)
	def read(self):
		while True:
			cmd = raw_input("Enter your command here : ")

			if cmd.lower().startswith('q'):
				return

			elif cmd.lower().startswith('send'):
				cmd = cmd.split(' ')
				if len(cmd) < 3:
					print 'At least provide port'
					continue
				self.message.put(cmd[1])
				""" if host is not provided, assume it's local server """
				try:
					self.dest.put((cmd[2],int(cmd[3])))	# enter [host] [port]
				except:
					self.dest.put((self.config.host,int(cmd[2])))
					cmd.append((self.config.host,self.config.port))

				print "Send %s to %s, system time is %s" %(str(cmd[1]),str(cmd[2]),str(datetime.now()))

			elif cmd.lower().startswith('delete'):
				pass

			elif cmd.lower().startswith('get'):
				pass

			elif cmd.lower().startswith('insert'):
				pass

			elif cmd.lower().startswith('update'):
				pass

	# thread for sending messages
	@thread(True)
	def send(self):
		while True:
			try:
				message = self.message.get()	# get the message and host atomically
				addr = self.dest.get()
			except:
				continue
			if not message:
				continue
			#time.sleep(self.config.get_time())	# simulate delay for message delivery
			self.s.sendto(message, addr)

	# thread for simulation delay by printing message after sleep
	@thread(True)
	def receive(self):
		while True:
			try:
				message, addr = self.inbox.get()
			except:
				continue
			time.sleep(self.config.get_time())	# simulate delay for message delivery
			print "Receive %s from %s, max delay is %s, system time is %s" %(message, addr, self.config.MAX, str(datetime.now()))
			print "Enter your command here : "



if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.argv.append(raw_input("Enter node letter a~d: "))

	my_server = Server(sys.argv[1])
	t_listen = my_server.listen()
	t_send = my_server.send()
	t_receive = my_server.receive()
	t_read = my_server.read()
	t_read.join()	# wait for only this thread to end, others will be killed as soon as main thread ends
