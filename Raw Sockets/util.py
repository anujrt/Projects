import sys;
import socket;
from struct import *;
from urlparse import urlparse;
import time;

'''
This file contains functions to calculate checksum, verfiy checksum,
display MAC address in HEX format, and to get data from the first response
'''

checksumflag = True;
tcp_destination_global = 80



# Used to calculate the carry around of two values
def carry_around_add(firstBit, secondBit):
    carryBit = firstBit + secondBit
    return (carryBit & 0xffff) + (carryBit >> 16)

# Calculates the checksum for the msg that is passed.
# The message passed is the TCP header. The checksum for the
# data is returned
def checksum(data):
	s = 0
	if (len(data) % 2 != 0):
		data = data + '\x00';

	for i in range(0, len(data), 2):
		w = ord(data[i]) + (ord(data[i+1]) << 8)
		s = carry_around_add(s, w)
	return ~s & 0xffff	

# Convert a string of 6 characters of ethernet address into a dash separated hex string
def eth_addr (addr) :
  ethAddr = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (ord(addr[0]) , ord(addr[1]) , ord(addr[2]), ord(addr[3]), ord(addr[4]) , ord(addr[5]))
  return ethAddr


# Function to verify the checksum received in a TCP header
# The function takes all the fields of the TCP header and the source ad destination IP addresses.
# It returns the Boolean value TRUE if the incoming checksum is equal to the calculated checksum (setting the checksum field
# to 0
def verifyChecksum(tcp_source_global,sourceIp,destinationIp,incomingChecksum,
			seqNum,acknowledgement,offset_value,flags,window,data):

	tcp_source = tcp_destination_global   # source port
	tcp_dest = tcp_source_global   # destination port

	# the ! in the pack format string means network order
	dummyheader = pack('!HHLLBBHHH' , tcp_source, tcp_dest, seqNum, 
				acknowledgement, offset_value, flags, window, 0,0)

	# now start constructing the packet
	packet ='';
	user_data ='';
	# pseudo header fields
	source_address = socket.inet_aton( sourceIp )   # source IP address
	dest_address = socket.inet_aton( destinationIp )    # destination IP address
	protocol = socket.IPPROTO_TCP
	headerlength = len(dummyheader) + len(data)
	
	pseudoHeader = pack('!4s4sBBH',dest_address,source_address,0,protocol , headerlength);
	pseudoHeader = pseudoHeader + dummyheader + data;  # concatenates the pseudo header, the tcp header and the tcp data
	
	finalChecksum = checksum(pseudoHeader) # passes the concatinated packet to checksum fucntion and that returns the checksum
	return (incomingChecksum == finalChecksum); # returns the result of the comparision


# Returns the data from the first response or an error stating the data was not found
def getDataFromFirstResponse(data):
	OK_RESPONSE_CODE = "200";
	LINE_DELIM = "\r\n"
	HEADER_DELIM = "\r\n\r\n"
	statusIndex = data.find(LINE_DELIM);
	dataStringIndex = data.find(HEADER_DELIM)
	
	if statusIndex > 0:
		responseString = data[0:statusIndex];
		responseCode = responseString.split()[1]	
#		print responseString
#		print '(',responseCode,')'
#		print len(responseCode)
		if responseCode != OK_RESPONSE_CODE:
			print "Response code is not 200"
			sys.exit();			
	else:
		print "Response is not correct"
		sys.exit();
	
	if dataStringIndex > 0:
#		print 'data is::' ,data[dataStringIndex + len(HEADER_DELIM):]
		return data[dataStringIndex + len(HEADER_DELIM):]
	else:
		print "Data not found"
		sys.exit();

