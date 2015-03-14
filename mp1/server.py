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
		self.counter = dict() 	# count
		self.invoke = False		# whether inside an operation
		self.last = time.time()		# last invocation

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
			self.receive()	# self.invoke a thread to deliver the message

	# main thread read and write
	@thread(False)
	def read(self):
		while True:
			cmd = raw_input()
			if self.invoke == True:
				print "The last operation is still running"
				continue

			self.invoke = True

			time.sleep(max(self.delay-time.time()+self.last,0))	# delay the next operation
			self.delay = 0	# reset delay time

			if cmd.lower().startswith('q'):
				return

			# send arbitrary message	usage send [message] [dest]
			elif cmd.lower().startswith('send'):
				cmd = cmd.split(' ')
				# sanity
				if len(cmd) < 3:
					print 'Usage send [message] [dest]'
					self.invoke = False
					continue
				#	use value field as message
				self.s.sendto((serialize('send',0,cmd[1],0,time.time(),self.node)),self.nodes[cmd[2]])
				self.invoke = False
				self.last = time.time()

			# delete a key through all replicas
			elif cmd.lower().startswith('delete'):
				cmd = cmd.split(' ')
				if len(cmd) < 2:
					print 'Usage delete [key]'
					self.invoke = False
					continue
				for key in self.nodes:
					if key != self.node:
						self.s.sendto(serialize(cmd[0],cmd[1],0,1,time.time(),self.node),self.nodes[key])
				try:
					del self.replica[cmd[1]]
					print 'Key %s deleted' %(cmd[1])
				except KeyError:
					pass
				self.invoke = False
				self.last = time.time()
			# write operations
			elif cmd.lower().startswith('insert') or cmd.lower().startswith('update'):
				cmd = cmd.split(' ')
				if len(cmd) < 4:
					print 'Usage insert [key] [value] [Model]'
					self.invoke = False
					continue
				# linearizibility & sequential consistency
				if int(cmd[-1]) == 1 or int(cmd[-1]) == 2:
					self.s.sendto(serialize(cmd[0],cmd[1],cmd[2],cmd[3],time.time(),self.node),self.central)
				# eventual consistency
				elif int(cmd[-1]) > 2:
					time_stamp = time.time()
					self.counter[str(time_stamp)] = 0
					for key in self.nodes:
						self.s.sendto(serialize(cmd[0],cmd[1],cmd[2],cmd[3],time_stamp,self.node),self.nodes[key])

			# read
			elif cmd.lower().startswith('get'):
				cmd = cmd.split(' ')
				if len(cmd) < 3:
					print 'Usage get [key] [model]'
					self.invoke = False
					continue
				# linearizability
				if int(cmd[-1]) == 1:
					self.s.sendto(serialize(cmd[0],cmd[1],0,cmd[2],time.time(),self.node),self.central)
				# sequential consistency
				elif int(cmd[-1]) == 2:
					try:
						print "Key %s with value %s" %(cmd[1],self.replica[cmd[1]])
					except KeyError:
						print "Key DNE at local replica"
					self.invoke = False
					self.last = time.time()
				# eventual
				elif int(cmd[-1]) > 2:
					time_stamp = time.time()
					self.counter[str(time_stamp)] = 0
					for key in self.nodes:
						self.s.sendto(serialize(cmd[0],cmd[1],0,cmd[2],time_stamp,self.node),self.nodes[key])

			# show-all
			elif cmd.lower().startswith('show-all'):
				for key in self.replica:
					print key,self.replica[key]
				self.invoke = False
				self.last = time.time()

			# delay
			elif cmd.lower().startswith('delay'):
				cmd = cmd.split(' ')
				if len(cmd) < 2:
					print "Usage delay [T]"
					self.invoke = False
					continue
				self.delay = int(cmd[1])
				self.invoke = False
				self.last = time.time()

			# search key
			elif cmd.lower().startswith('search'):
				cmd = cmd.split(' ')
				if len(cmd) < 2:
					print "Usage search [key]"
					self.invoke = False
					continue

				for key in self.nodes:
					if key != self.node:
						self.s.sendto(serialize(cmd[0],cmd[1],0,1,time.time(),self.node),self.nodes[key])
				try:
					print "Key %s with value %s found at %s" %(cmd[1],self.replica[cmd[1]],self.node)
				except KeyError:
					print "Key %s DNE at node %s" %(cmd[1],self.node)

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
			if key not in self.stamps or float(self.stamps[key]) < float(time_stamp):
				self.replica[key] = value
				self.stamps[key] = time_stamp
			self.lock.release()		# leave the cs

			if int(model) > 2:
				self.s.sendto(serialize('Ack',key,value,model,time_stamp,node),self.nodes[node])
			else:
				self.s.sendto(serialize('Write_ack',key,value,model,time_stamp,node),self.central)	# send ack to central server

		elif ops == 'get':
			if int(model) > 2:
				try:
					self.s.sendto(serialize('Even_'+time_stamp,key,self.replica[key],model,self.stamps[key],node),self.nodes[node])		# the ops field is concatenated with time_stamp of inovation
				except KeyError:
					pass
			else:
				self.s.sendto(serialize('Read_ack',key,value,model,time_stamp,node),self.central)	# send ack to central server
		# eventual consistency read and incosistency repair
		elif ops.split('_')[0] == 'Even':
			self.lock.acquire(True)
			if key not in self.stamps or float(self.stamps[key]) < float(time_stamp):
				self.replica[key] = value
				self.stamps[key] = time_stamp
			self.lock.release()
			self.counter[ops.split('_')[1]] += 1
			if self.counter[ops.split('_')[1]] + 2 == int(model):
				print "Key %s with value %s" %(key,self.replica[key])
				self.invoke = False
				self.last = time.time()

		elif ops == 'Write_ack':
			print "Ack %s : %s" %(key, value)
			self.invoke = False
			self.last = time.time()

		elif ops == 'Read_ack':
			try:
				print "Key %s with value %s" %(key,self.replica[key])
			except KeyError:
				print "Key DNE at local replicaf"
			self.invoke = False
			self.last = time.time()

		elif ops == 'Ack':
			self.counter[time_stamp] += 1
			if self.counter[time_stamp] + 2 == int(model):
				print "Ack %s : %s" %(key, value)
				self.invoke = False
				self.last = time.time()

		elif ops == 'search':
			try:
				self.s.sendto(serialize('Found',key,self.replica[key],model,self.stamps[key],self.node),self.nodes[node])
			except:
				self.s.sendto(serialize('NotFound',key,0,model,0,self.node),self.nodes[node])

		elif ops == 'Found':
			print "Key %s with value %s found at %s" %(key,value,node)
			self.invoke = False
			self.last = time.time()

		elif ops == 'NotFound':
			print "Key %s DNE at node %s" %(key,node)
			self.invoke = False
			self.last = time.time()

		elif ops == 'delete':
			try:
				del self.replica[key]
			except KeyError:
				pass

if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.argv.append(raw_input("Enter node letter a~d: "))

	my_server = Server(sys.argv[1])
	t_listen = my_server.listen()
	t_read = my_server.read()
	t_read.join()	# wait for only this thread to end, others will be killed as soon as main thread ends
