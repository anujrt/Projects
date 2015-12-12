#!/usr/bin/python
import sys;
import socket;
import random;
from struct import *;
from urlparse import urlparse;
from rawIp import make_ip_header;
from util import checksum;
from rawTcp import make_tcp_packet;
from util import verifyChecksum,getDataFromFirstResponse;
import time;

#This is the code to create the Transport and Network Layer Stack
# @author Nikhil Singh, Anuj Thakur

#Global variables used during the lifecycle of the program
tcpHandshakeAckNum = 0
#this is the random source port number which can range between 100 and 2000
tcp_source_global = random.randint(100,2000);	
#this is the destination default HTTP port number port number
tcp_destination_global = 80
#this is the random client sequence number which can range between 100 and 99999
tcp_seq_global = random.randint(100,99999);	
##################################################################
# this is the parse the command line argument which contains the 
# path of the file that needs to be downloaded
if ( len(sys.argv) == 2 ): 
	urlPath = sys.argv[1];
	parsed = urlparse(urlPath)
	address = parsed.netloc
	#incase the length of the address is Zero it means that 
	#address is missing in the argument
	if len(address) == 0:
		print "Invalid address";
		sys.exit();
	#logic to parse the file path and file name
	filePath =  parsed.path
	fileName = filePath[::-1]
	fileNameIndex = fileName.find('/')
	fileName = filePath[len(filePath) - fileNameIndex:]

	if '.' not in filePath:
		if filePath.endswith('/'):		
			fileName = "index.html"
		else: 
			print "Invalid address";
			sys.exit();
		
	#create a normal socket to fetch the destination IP
	# and the source IP
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
	s.connect((address,tcp_destination_global));
	sourceIp = s.getsockname()[0];
	destinationIp = s.getpeername()[0];
	s.close();
else:
	print "Incorrect number of argument passed";
	sys.exit();
##################################################################
#creating the RAW sockets for sending as well as receiving packets
try:
	sendSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
	#setting the time out for the sockets to 3 mins
	sendSocket.settimeout(180);
	receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW , socket.IPPROTO_TCP)
	#setting the time out for the sockets to 3 mins	
	receiveSocket.settimeout(180);	
except socket.error , msg:
	#Socket error occured
	print ('Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]);
	sys.exit();

##################################################################
'''
The Main function of the tcp_handshake_syn() function is to send the SYN packet to the destination address to initiate 
three way handshake, once server sends the SYN ACK packet for the three way handshake, another function is invoked to 
send the ack for the received packet
'''
def tcp_handshake_syn():
	# Call the function in rawIp.py to get the IP header based on the arguments of this function	
	ip_header = make_ip_header(sourceIp=sourceIp,destinationIp = destinationIp)
	#there is no user data in the first SYN packet since the client is initiating the three way handshake
	user_data = ''
	# Call the function in rawTcp.py to get the TCP header based on the arguments of this function
	tcp_header = make_tcp_packet(sourceIp,destinationIp,tcp_source_global,
			tcp_destination_global,tcp_seq_global,0,0,1,0,0,user_data)

	#creating the final packet
	packet = ip_header + tcp_header + user_data
	 
	#Send the packet finally - the port specified has no effect
	sendSocket.sendto(packet, (destinationIp , 0 ))

	# receive a packet
	packetReceived = True;
	while packetReceived:
	    packet = receiveSocket.recvfrom(tcp_source_global)
	    packet = packet[0]
	    ip_header = packet[0:20]
	    ipHeader = unpack('!BBHHHBBH4s4s' , ip_header)
	    version_ihl = ipHeader[0]
            version = version_ihl >> 4
	    ihl = version_ihl & 0xF
	    iph_length = ihl * 4

     	    tcp_header = packet[iph_length:iph_length+20]
 	    tcpHeader = unpack('!HHLLBBHHH' , tcp_header)
		
            source_port = tcpHeader[0]
	    dest_port = tcpHeader[1]
	    sequence = tcpHeader[2]
	    acknowledgement = tcpHeader[3]
	    dataOffset_reserved = tcpHeader[4]
	    tcpHeader_length = dataOffset_reserved >> 4

	    if  (acknowledgement == tcp_seq_global + 1) and (dest_port == tcp_source_global) :
		headerSize = iph_length + tcpHeader_length * 4
		data_size = len(packet) - headerSize
		#get data from the packet
		data = packet[headerSize:]
		packetReceived = False;
		#calling the function to perform handshakee by sending ACK for the SYN ACK packet received
		#the sequence will be increased by 1 and the ackNumber will be same as the seq number of the
		#received packet
		send_req(ackNum = sequence + 1,seqNum = acknowledgement)
################################################################## 
'''
The Main function of the send_req() function is to send the SYN packet to the destination address to complete 
three way handshake and to send the get request in the same packet once server sends the SYN ACK packet for the 
three way handshake.
Another important feature of this packet is to set the PSH flag to one to send the data to the application layer
'''
def send_req(ackNum,seqNum):
	# Call the function in rawIp.py to get the IP header based on the arguments of this function	
	ip_header = make_ip_header(sourceIp=sourceIp,destinationIp = destinationIp)


	# tcp data field
	user_data ='GET '+ filePath +' HTTP/1.0\r\nHost: '+ address +'\r\nUser-Agent: HTTPTool/1.1\r\nAccept-Language: en-US,en;q=0.5\r\nConnection: keep-alive\r\n\r\n';
	# Call the function in rawTcp.py to get the TCP header based on the arguments of this function	
	tcp_header = make_tcp_packet(sourceIp ,destinationIp,tcp_source_global,tcp_destination_global,
					seqNum ,ackNum,0,0,1,1,user_data)

	# this is the final packet that needs to be sent to the destination
	packet = ip_header + tcp_header + user_data

	sendSocket.sendto(packet, (destinationIp , 0 )) 
	# receive the ACK packet from the server .. this packet contains the sequence number for the receiver used for
	# the rest of the communication
	#sending the seq number of the last acked packet
	get_file(nextSeq = ackNum,clientSeqNum = seqNum + len(user_data))
			
##################################################################
'''
The Main function of the get_file() function is to read the packets received from the destination address i.e.
the server once the request has been sent to the server, this function is also responsible for performing the 
checksum verification for both IP and TCP headers by calling the function in the util.py file. The function
calls another function to send the ACK packet to the server once the packet is received
'''
def get_file(nextSeq,clientSeqNum):
	#creating the file based on the fileName request by the user
	object = open(fileName,'w')
	i = 0
	firstServerSeqNumber = nextSeq;
	#taking the current time of the clock to implement the timer functionality
	startTime = time.clock()
	currentTime = time.clock()
	checksumCorrect = True;
	#while i < 3:
	while ((currentTime - startTime) < 60):
	    currentTime = time.clock();
	    i = i +1
	    packet = receiveSocket.recvfrom(tcp_source_global)

	    #packet string from tuple
	    packet = packet[0]
	    ipHeader = packet[0:20]
	    header = unpack('!BBHHHBBH4s4s' , ipHeader)
	    version_ihl = header[0]
	    version = version_ihl >> 4
	    ihl = version_ihl & 0xF
            ipHeaderLength = ihl * 4

	    protocol = header[6]
	    ipChecksum = header[7] #incoming checksum from the header

	    #Only process the data if the IP checksum on the IP header is correct
  	    if(checksum(ipHeader) == 0):
	    	    #TCP protocol	
		    tcp_header = packet[ipHeaderLength:ipHeaderLength+20]
		    tcph = unpack('!HHLLBBHHH' , tcp_header)
		    #unpacking the header to retreive header details
		    source_port = tcph[0]
		    dest_port = tcph[1]
		    sequence = tcph[2]
		    acknowledgement = tcph[3]
		    doff_reserved = tcph[4]
		    tcp_doff = doff_reserved >> 4
			
		    tcpFlag = tcph[5]
		    window = tcph[6]
		    urgPointer = tcph[7]
		    urgFlag = (tcpFlag >> 3)
		    ackFlag = (tcpFlag >> 4)
		    finFlag = (tcpFlag >> 8)
		    synFlag = (tcpFlag >> 7)
		    rstFlag = (tcpFlag >> 6)
		    pshFlag = (tcpFlag >> 5)
		    window = tcph[6]
    	  	    		    
		    #Getting the checksum in the incoming packet
		    incomingChecksum = tcph[7]
		    tcph_length = doff_reserved >> 4
		    if (socket.inet_ntoa(header[8]) == destinationIp) and (sequence == nextSeq) and (acknowledgement == clientSeqNum):
	 		h_size = ipHeaderLength + tcph_length * 4
			data_size = len(packet) - h_size
			data = packet[h_size:]
			dataLength = len(data)
			
			#incase the length of the data is 6,it means the packet has been padded with Zeroes
		    	if len(data) == 6:
				dataLength = 0

	     	        nextSeq = sequence + dataLength
		        if (dataLength != 0):
                                #Call the verifyChecksum() to check if the checksum is correct
				checksumcorrect = verifyChecksum(tcp_source_global,sourceIp,destinationIp,
								incomingChecksum,sequence,acknowledgement,
								doff_reserved,tcpFlag,window,data)
                                #get data from the header only if the checksum of the TCP header is correct
				if(checksumCorrect):
					#Sending the ACK for the packet after the verification of the IP and TCP checksum
					sendAckOrFin(ackNumber = nextSeq,seqNum = clientSeqNum,ackFlag = 1,finFlag = 0)
					if firstServerSeqNumber == sequence:	
						data  = getDataFromFirstResponse(data);
						object.write(data) 
					else:
						object.write(data)
			if (dataLength == 0) and (firstServerSeqNumber != sequence):
				#Sending the ACK for the packet after the verification of the IP and TCP checksum
				sendAckOrFin(ackNumber = nextSeq+1,seqNum = clientSeqNum ,ackFlag = 1,finFlag = 0)
				#closing the sockets
				receiveSocket.close();
				sendSocket.close();
				sys.exit()


##################################################################
'''
The Main function of the sendAckOrFin() function is used to send the ACK packets to the destination address for
the packets that are recieved from the destination after the threeway handhshake;
'''
def sendAckOrFin(ackNumber,seqNum,ackFlag,finFlag):
	# Call the function in rawIp.py to get the IP header based on the arguments of this function	
	ipHeader = make_ip_header(sourceIp=sourceIp,destinationIp = destinationIp)
	#there is no user data in the ACK packets since the client is not gonna send any more data to the server
	user_data = ''
	# tcp header fields
	# Call the function in rawTcp.py to get the TCP header based on the arguments of this function
	tcpHeader = make_tcp_packet(sourceIp ,destinationIp,tcp_source_global,tcp_destination_global,
					seqNum,ackNumber,finFlag,0,0,ackFlag,user_data)

	#Making the final packet
	packet = ipHeader + tcpHeader + user_data

	#Send the ACK or FIN Packet
	sendSocket.sendto(packet,(destinationIp,0))
##################################################################	
# Main Process
# this is to complete the threeway handshake and to download the give file
tcp_handshake_syn();

