import sys;
import socket;
from struct import *;
from urlparse import urlparse;
import time;
from util import checksum;

# This function is used to make Transport layer packet i.e TCP packet
# It take as argument the Source IP address, Destination IP address, the source and destination Port number,
# the sequence number and the sequnce that is to be acked, the flags and user data.
# It returns all the data packed into variable tcp_header
def make_tcp_packet(sourceIp,destinationIp,sourcePort,destPort,seqNum,ackNum,finFlag,synFlag,pshFlag,ackFlag,user_data):
	tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
	# tcp flags
	rstFlag = 0
	urgFlag = 0
	window = socket.htons (5840)    # Sets the maximum allowed window size
	check = 0
	urgent_ptr = 0
	 
	tcp_offset_res = (tcp_doff << 4) + 0
	flags = finFlag + (synFlag << 1) + (rstFlag << 2) + (pshFlag <<3) + (ackFlag << 4) + (urgFlag << 5)
	 
	# the ! in the pack format string means network order
	dummyheader = pack('!HHLLBBHHH',sourcePort,destPort,seqNum,ackNum, tcp_offset_res,flags,window, check,urgent_ptr)

	# now start constructing the packet
	packet ='';
	# pseudo header fields
	# The source and destination IP addresses are required for this.
	protocol = socket.IPPROTO_TCP
	tcp_length = len(dummyheader) + len(user_data)
	
	psh = pack('!4s4sBBH',socket.inet_aton(sourceIp),socket.inet_aton(destinationIp),0,protocol,tcp_length);
	psh = psh + dummyheader + user_data;

	# Passes the Pseudo header, the tcp header and the user data to the function checksum in util file.
	# It returns the TCP checksum which is stored in variable tcp_check
	finalChecksum = checksum(psh) # tcp_checksum
	 
	# make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
	# packs the tcp header, the calculated checksum and tcp_urg_ptr
	finalHeader = pack('!HHLLBBH' , sourcePort, destPort, seqNum, ackNum, tcp_offset_res, flags,window) + pack('H' , finalChecksum) + pack('!H' , urgent_ptr)
	 
	return finalHeader;

