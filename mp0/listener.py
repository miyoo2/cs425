import socket               # Import socket module
from datetime import datetime

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)         # Create a socket object
host = socket.gethostname()  # Get local machine name
port = 12346                # Reserve a port for your service.
s.bind((host, port))        # Bind to the port
while True:
	message, addr = s.recvfrom(1024)
	print "receive %s from %s" %(message, addr)
	s.sendto("I have got your message at %s" %str(datetime.now()), addr)