import socket               # Import socket module
import sys

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 12345                # Reserve a port for your service.
s.bind((host, port))        # Bind to the port

argv = sys.argv
if len(argv) == 2:
	filename = argv[1]

s.listen(5)                 # Now wait for client connection.
while True:
   c, addr = s.accept()     # Establish connection with client.
   print 'Got connection from', addr
   c.sendall(filename)
   f = open(filename)
   c.sendall(f.read())
   print 'file sent to all clients\n'
   f.close()
   c.close()                # Close the connection