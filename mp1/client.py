import socket               # Import socket module

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 12345                # Reserve a port for your service.

s.connect((host, port))
print "Successfully connected to ", (host, port)
filename = 'client_' + s.recv(1024)
with open(filename,'w') as f:
	line = s.recv(1024)
	while line:
		f.write(line)
		line = s.recv(1024)
f.close()
print "File written to current dir\n"
s.close                     # Close the socket when done