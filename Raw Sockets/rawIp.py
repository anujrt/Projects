import sys;
import socket;
from struct import *;
from urlparse import urlparse;
import time;

# This file contains the method make_ip_header.
# This method takes source and destination IP addresses as the arguments.
# Returns the IP header, with all the field packed.
def make_ip_header(sourceIp,destinationIp):
	# ip header fields
	internetHeaderLength = 5
	version = 4
	tos = 0
	totalLength = 0  # kernel will fill the correct total length
	ipid = 54321   # Id of this packet
	fragment_offset = 0
	ttl = 255
	ip_checksum = 0    # kernel will fill the correct checksum
	internetHeaderLength_ver = (version << 4) + internetHeaderLength	
	 
	# the ! in the pack format string means network order.
	# Packs all the IP header fields and returns IP header.
	ip_header = pack('!BBHHHBBH4s4s',internetHeaderLength_ver,tos, 
			totalLength,ipid,fragment_offset,ttl,socket.IPPROTO_TCP,
			ip_checksum,socket.inet_aton(sourceIp),socket.inet_aton(destinationIp))
	return ip_header


