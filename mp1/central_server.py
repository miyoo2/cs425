from config import ServerConfig
from threading import Thread
from functools import wraps
import json
import socket
import time
import sys
import Queue

class Central(object):
	"""docstring for Central"""
	def __init__(self,model):
		super(Central, self).__init__()


if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.argv.append(raw_input('Enter consistency model 1. Linearizability 2. Sequential consistency 3. Eventual consistency, W = 1, R = 1 4. Eventual consistency, W = 2, R = 2 '))