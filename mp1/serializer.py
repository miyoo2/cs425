from threading import Thread
from functools import wraps

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

# serialize socket message
def serialize(ops,key,value,model,time_stamp,node):
	return ' '.join([ops,str(key),str(value),str(model),str(time_stamp),node])

def deserialize(message):
	message = message.split(' ')
	return message[0],message[1],message[2],message[3],message[4]+' '+message[5],message[6]