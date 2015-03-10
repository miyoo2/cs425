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
		self.delay = 0	# invocation & operation delay

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
			self.receive()	# invode a thread for FIFO and delay


	# main thread read and write
	@thread(False)
	def read(self):
		while True:
			cmd = raw_input("Enter your command here : ")

			time.sleep(self.delay)	# delay the next operation
			self.delay = 0	# reset the delay time

			if cmd.lower().startswith('q'):
				return
			# show all keys in the local replica
			elif cmd.lower().startswith('show-all'):
				for key in self.replica:
					print key, self.replica[key]
			# set the next delay
			elif cmd.lower().startswith('delay'):
				cmd = cmd.split(' ')
				if len(cmd) < 2:
					self.delay = 0
				else:
					self.delay = int(cmd[1])

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
			
			elif cmd.lower().startswith('get') or cmd.lower().startswith('delete'):
				cmd = cmd.split(' ')
				if len(cmd) < 3:
					print 'Please provide key'	# missing key
					continue
				if cmd[-1] == '1':	# linearizability
					self.message.put(cmd[0]+' '+cmd[1])
					self.dest.put((self.config.host,self.config.central))	# send the message to central server
				elif cmd[-1] == '2':	# sequential consistent
					print "The value corresponding to %s is %s" %(cmd[1],self.replica[int(cmd[1])])
				
			elif cmd.lower().startswith('insert') or cmd.lower().startswith('update'):
				cmd = cmd.split(' ')
				if len(cmd) < 4:
					print 'Please provide key and value'
					continue
				if cmd[-1] == '1' or cmd[-1] == '2':	# linearizability and sequential consistent
					self.message.put(cmd[0]+' '+cmd[1]+' '+cmd[2])
					self.dest.put((self.config.host,self.config.central))


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
		try:
			message, addr = self.inbox.get()
		except:
			return
		time.sleep(self.config.get_time())	# simulate delay for message delivery

		message = message.split(' ')
		if addr[1] == 23333:
			addr = message.pop(-1)
		message = ' '.join(message)
		print "Receive %s from %s, max delay is %s, system time is %s" %(message, addr, self.config.MAX, str(datetime.now()))

		message = message.split(' ')
		if message[0] == 'get':
			print "The value corresponding to %s is %s" %(message[1],self.replica[int(message[1])])

		elif message[0] == 'delete':
			print "Delete %s from all replicas" %(message[1])
			del self.replica[int(message[1])]

		elif message[0] == 'insert':
			print "Insert %s : %s into replica" %(message[1],message[2])
			self.replica[int(message[1])] = int(message[2])

		elif message[0] == 'update':
			print "Update %s : %s " %(message[1],message[2])
			self.replica[int(message[1])] = int(message[2])

		else:
			return

		self.message.put('ack '+message[-1])
		self.dest.put((self.config.host,self.config.central))


if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.argv.append(raw_input("Enter node letter a~d: "))

	my_server = Server(sys.argv[1])
	t_listen = my_server.listen()
	t_send = my_server.send()
	t_read = my_server.read()
	t_read.join()	# wait for only this thread to end, others will be killed as soon as main thread ends
