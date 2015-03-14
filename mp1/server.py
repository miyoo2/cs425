from serializer import thread, serialize, deserialize
from datetime import datetime
from threading import Lock
import socket
import time
import sys
import Queue
import json
import random

# major server class
class Server(object):
	"""docstring for Server"""
	def __init__(self,node):
		super(Server, self).__init__()
		self.config(node)	# read config from json
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.bind((self.host,self.port))
		self.inbox = Queue.Queue()	# thread safe queue to implement FIFO ordering
		self.replica = dict()	# key-value store
		self.delay = 0	# operation delays
		self.node = node
		self.stamps = dict()	# insertion time stamps
		self.lock = Lock()	# a threading lock

	"""json loader"""
	def config(self,node):
		data = open('config.json')
		data = json.load(data)
		self.MAX = int(data[str(node)]['MAX'])	# max delay
		self.port = int(data[str(node)]['port'])	# server's port
		self.host = socket.gethostname()	# server's ip address
		self.central = (socket.gethostname(),int(data['central']['port']))	# central server's port
		self.nodes = dict()	# other nodes ports

		for key in data:
			if key != "central":
				self.nodes[key] = (socket.gethostname(),int(data[key]['port']))	# only work for locals

	"""random time generator"""
	def get_time(self):
		return random.randint(0,self.MAX)

	# thread for listening
	@thread(True)
	def listen(self):
		while True:
			message, addr = self.s.recvfrom(1024)	# listen from the socket

			self.inbox.put((message, addr))	# put message into the queue
			self.receive()	# invoke a thread to deliver the message

	# main thread read and write
	@thread(False)
	def read(self):
		while True:
			cmd = raw_input()

			time.sleep(self.delay)	# delay the next operation
			self.delay = 0	# reset delay time

			if cmd.lower().startswith('q'):
				return

			# send arbitrary message	usage send [message] [dest]
			elif cmd.lower().startswith('send'):
				cmd = cmd.split(' ')
				# sanity
				if len(cmd) < 3:
					print 'Usage send [message] [dest]'
					continue
				#	use value field as message
				self.s.sendto((serialize('send',0,cmd[1],0,datetime.now(),self.node)),self.nodes[cmd[2]])

			# write operations
			elif cmd.lower().startswith('insert') or cmd.lower().startswith('update'):
				cmd = cmd.split(' ')
				if len(cmd) < 4:
					print 'Usage insert [key] [value] [Model]'
					continue
				# linearizibility & sequential consistency
				if int(cmd[-1]) == 1 or int(cmd[-1]) == 2:
					self.s.sendto(serialize(cmd[0],cmd[1],cmd[2],cmd[3],datetime.now(),self.node),self.central)

			# read
			elif cmd.lower().startswith('get'):
				cmd = cmd.split(' ')
				if len(cmd) < 3:
					print 'Usage get [key] [model]'
					continue
				# linearizability
				if int(cmd[-1]) == 1:
					self.s.sendto(serialize(cmd[0],cmd[1],0,cmd[2],datetime.now(),self.node),self.central)
				# sequential consistency
				elif int(cmd[-1]) == 2:
					try:
						print "Key %s with value %s" %(cmd[1],self.replica[cmd[1]])
					except KeyError:
						pass

			# show-all
			elif cmd.lower().startswith('show-all'):
				for key in self.replica:
					print key,self.replica[key]

			# delay
			elif cmd.lower().startswith('delay'):
				cmd = cmd.split(' ')
				if len(cmd) < 2:
					print "Usage delay [T]"
					continue
				self.delay = int(cmd[1])

			# search key
			elif cmd.lower().startswith('search'):
				cmd = cmd.split(' ')
				if len(cmd) < 2:
					print "Usage search [key]"
					continue

				for key in self.nodes:
					if key != self.node:
						self.s.sendto(serialize(cmd[0],cmd[1],0,1,datetime.now(),self.node),self.nodes[key])
				try:
					print "Key %s with value %s found at %s" %(cmd[1],self.replica[cmd[1]],self.node)
				except KeyError:
					pass

	# thread for simulation delay by printing message after sleep
	@thread(True)
	def receive(self):
		time.sleep(self.get_time())	# simulation delay
		message, addr = self.inbox.get()	# FIFO ordering by queue

		# deserialize the message into components
		ops,key,value,model,time_stamp,node = deserialize(message)

		if ops == 'send':
			print "Receive %s from %s, max delay is %s, system time is %s" %(value,node,self.MAX,str(datetime.now()))

		elif ops == 'insert' or ops == 'update':
			self.lock.acquire(True)		# lock when enter cs
			if key not in self.stamps or datetime.strptime(self.stamps[key]) < datetime.strptime(time_stamp):
				self.replica[key] = value
				self.stamps[key] = time_stamp
			self.lock.release()		# leave the cs
			self.s.sendto(serialize('ack',key,value,model,time_stamp,node),self.central)	# send ack to central server

		elif ops == 'get':
			if node == self.node:
				try:
					print "Key %s with value %s" %(cmd[1],self.replica[cmd[1]])
				except KeyError:
					pass

		elif ops == 'ack':
			print "Ack %s : %s" %(key, value)


if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.argv.append(raw_input("Enter node letter a~d: "))

	my_server = Server(sys.argv[1])
	t_listen = my_server.listen()
	t_read = my_server.read()
	t_read.join()	# wait for only this thread to end, others will be killed as soon as main thread ends
