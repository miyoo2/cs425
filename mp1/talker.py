import socket               # Import socket module

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)         # Create a socket object
host = socket.gethostname()  # Get local machine name
port = 12346                # Reserve a port for your service.
addr = (host, port)
while True:
	message = raw_input("What are you going to say: ") # Don't run in sublime it does not support input
	s.sendto(message, addr)
	message = s.recvfrom(1024)[0]
	print "reply: %s" %message