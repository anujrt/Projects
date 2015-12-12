#chmod +x freegeoip
import socket
import struct
from threading import Thread
import sys
import time
import math
from urllib2 import urlopen
from contextlib import closing
import json
import sys
import time
from subprocess import check_output
from subprocess import CalledProcessError
import subprocess

#############The geolocation of the server################

# NOTE: Location stored in this dictionary is in format (latitude,longitude)
all_data = [{'ip': '52.0.73.113', 'subdivisions': frozenset(['VA']), 'location': (39.0437, -77.4875), 'country': 'US', 'timezone': 'America/New_York', 'continent': 'NA'},
{'ip': '52.16.219.28', 'subdivisions': frozenset(['L']), 'location': (53.3331, -6.2489), 'country': 'IE', 'timezone': 'Europe/Dublin','continent': 'EU'},
{'ip': '52.11.8.29', 'subdivisions': frozenset(['OR']), 'location': (45.7788, -119.529), 'country': 'US', 'timezone': 'America/Los_Angeles', 'continent': 'NA'},
{'ip': '52.8.12.101', 'subdivisions': frozenset(['CA']), 'location': (37.3394, -121.895), 'country': 'US', 'timezone': 'America/Los_Angeles', 'continent': 'NA'},
{'ip': '52.28.48.84', 'subdivisions': frozenset(['HE']), 'location': (50.1167, 8.6833), 'country': 'DE', 'timezone': 'Europe/Berlin', 'continent': 'EU'},
{'ip': '52.68.12.77', 'subdivisions': frozenset(['13']), 'location': (35.685, 139.7514), 'country': 'JP', 'timezone': 'Asia/Tokyo', 'continent': 'AS'},
{'ip': '52.74.143.5', 'subdivisions': frozenset([]), 'location': (1.2931, 103.8558), 'country': 'SG', 'timezone': 'Asia/Singapore', 'continent': 'AS'},
{'ip': '52.64.63.125', 'subdivisions': frozenset(['NSW']), 'location': (-33.8666, 151.2082), 'country': 'AU', 'timezone': 'Australia/Sydney', 'continent': 'OC'},
{'ip': '54.94.214.108', 'subdivisions': frozenset(['SP']), 'location': (-23.5475, -46.6361), 'country': 'BR', 'timezone': 'America/Sao_Paulo', 'continent': 'SA'} ]


global dom_in_request_datagram
dom_in_request_datagram = ''

def pack(data, addr, udp_socket):
    samecountry_dnsserver_ip = ''
    ip = addr
    flag = 0
    details_of_selected_replica = []
    location_city = ''
    location_state = ''
    location_country = ''
    location_zip = 0
    location_longitude = 0
    location_latitude = 0
    min_distance = 10000000


    try:
	check_output(["pidof","freegeoip"])
    except CalledProcessError:
	p=subprocess.Popen('./freegeoip -silent=true -addr=":43456"', shell=True, stdout=subprocess.PIPE)	
    
    # print "Ip address", ip[0]
    # Passes the ip[0] field i.e the IP address of the client. Sends the URL request to the
    # locally running freegeoip instance on port 8080
    url = 'http://127.0.0.1:43456/json/'+ip[0]
    try:
	
	#print "Try clause"
        with closing(urlopen(url)) as response:
            location = json.loads(response.read())
 	    #print location
            location_city = location['city']
	    location_state = location['region_name']
            location_country = location['country_code']
            location_zip = location['zip_code']
            location_longitude = location['longitude']
            location_latitude = location['latitude']
    except:
	pass;
    # print "Longitude and latitude of the client", location_longitude," ",location_latitude
    # This loop will select two replica address, if there is only one replica in the country than that,
    # or else the replica closest to it. Calculated using distance formula.
    for i in range(0,len(all_data)):
        location = all_data[i].get('location')
	
	#print "longitude ", location[1],"latitude ",location[0]
	# Distance Formula
        longitude = math.pow((location[1] - location_longitude),2)
        latitude = math.pow((location[0] - location_latitude),2)
        distance = math.sqrt(longitude+latitude)

	# If the distance between the client and the current replica is less than the previous minimum,
        # change the distance and the ip address of the replica selected to the ip address of the current
        # replica server.
        if min_distance > distance:
            min_distance = distance
            details_of_selected_replica = [(all_data[i].get('ip'),math.sqrt(longitude),math.sqrt(latitude))]
            nearest_replica_ip = all_data[i].get('ip')
        if location_country == all_data[i].get('country'):
            samecountry_replica_ip = all_data[i].get('ip')
            flag = flag + 1

    replica_selected = socket.inet_aton (nearest_replica_ip)

    # DNS packet packing starts here.
    response_packet = ''
    dom = ''
    aname = '\xc0\x0c'
    data_index=12
    next_byte=ord(data[data_index])
    while next_byte != 0:
        dom+=data[data_index+1:data_index+next_byte+1]+'.'
        data_index+=next_byte+1
        next_byte=ord(data[data_index])
    global dom_in_request_datagram
    dom_in_request_datagram = str(dom[0:(len(dom) - 1)])

    # If the domain name is provided in DNS request and Domain name for which the name resolution is requested 
    # is same as that of the domain name specified while starting the dns server, only then the response is sent.
    if dom and dom_in_request_datagram == domain_name:
    	response_packet += data[:2]
    	# Rescursive look up or not. Won't request for a recursive look up but still, just in case.
    	if data[2:4] == '\x01\x00':
    		response_packet += '\x81\x80'
    	else:
    		response_packet += '\x80\x00'
    	#Adding question count
    	response_packet += data[4:6]
    	#Adding Answer count. Setting it as 1
    	response_packet += '\x00\x01'
    	#Adding the Number of records in authority and additional record section
    	response_packet += '\x00\x00\x00\x00'
    	#Header created
    	#Adding question section
    	response_packet += data[12:]
    	#Adding answer packet
    	response_packet += aname
    	response_packet += '\x00\x01' #Indicating it is Type A record
    	response_packet += '\x00\x01' #Indicating it is an IP address
    	response_packet += '\x00\x00\x00\x05' #Indicating the reponses' time to live is 5 seconds
    	response_packet += '\x00\x04' #Indicating the length of the reponse data is 4 octets
    	response_packet += replica_selected
    	udp_socket.sendto(response_packet, addr)
    	return




if __name__ == '__main__':
  global domain_name
  domain_name = sys.argv[4]
  #print domain_name
  #print 'Server Started'
  global port_number
  port_number = int(sys.argv[2])
  #global data_queue
  #data_queue = Queue(maxsize = 100)

  try:
    global udp_socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('',port_number))
    while True:
    	data, addr = udp_socket.recvfrom(1024) #4096 indicates the number of bytes the socket reads at a time
    	t = Thread(target = pack, args = (data, addr, udp_socket,))
    	t.start()
  except KeyboardInterrupt:
    udp_socket.close()
