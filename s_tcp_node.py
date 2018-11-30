import sys
import struct
from time import *
from socket import *

#Define sizes in terms of bytes
read_n_bytes=42
header_size=4
packet_size=46

#Find fractional part of time information provided by NTP response
def getFraction(binary_repr):
  fraction=0.0
  ctr=1
  for bit in binary_repr:
    if(bit=="1"):
     fraction+=1/2**ctr
    ctr+=1
  return fraction

#Calculate NTP offset of this system
def getNTPTime(host = "pool.ntp.org"):
    port = 123
    buf = 1024
    host_address = (host,port)

    #Subtract 70 years of difference
    diff = 2208988800

    #Connect to NTP server
    client=socket(AF_INET, SOCK_DGRAM)
    client.settimeout(1)
    delay=10000
    offset=0
    delay_offset_pair=(delay, offset)
    #Send requests until getting 8 replies
    i=0
    while i<8:
      req=('\x1b'+47*'\0').encode()
      client.sendto(req, host_address)
      #Save current time
      client_tx=time()
      #Wait response
      data=0
      #If sent packet is lost, resend it without incrementing i
      try:
        data=client.recv(buf)
      except timeout:
        continue
      #Save current time
      client_rx=time()
      #Parse response
      response=struct.unpack('!12I', data)
      #Calculate receive timestamp
      decimal = response[8]-diff
      binary_repr=format(response[9],"b")
      binary_repr="0"*(32-len(binary_repr))+binary_repr
      fraction = getFraction(binary_repr)
      server_rx=decimal+fraction
      #Calculate transmit timestamp
      decimal = response[10]-diff
      binary_repr=format(response[11],"b")
      binary_repr="0"*(32-len(binary_repr))+binary_repr
      fraction = getFraction(binary_repr)
      server_tx=decimal+fraction
      #Bytes corrupted, discard
      if(server_rx>=server_tx):
        continue
      #Calculate:
      #The delay between the client and the server
      #The offset of the client clock from the server clock
      #NTP uses the minimum of the last eight delay measurements. 
      #The selected offset is one measured at the lowest delay.
      delay=(client_rx-client_tx)-(server_tx-server_rx)
      if(delay<delay_offset_pair[0]):
        offset=(server_rx-client_tx+server_tx-client_rx)/2
        delay_offset_pair=(delay, offset)
      #Send next request
      i+=1
    client.close()
    return offset

#Parse response coming from destination d
def parseResponse(res):
  packet_index=int(res[:header_size])
  str_list=str(res[header_size:]).split(' ')
  ack=str_list[0]
  router_name=str_list[1][len("Via:"):]
  time=float(str_list[2][len("At:"):-1])
  return (packet_index, router_name, time)

#Source node implementation
def main(argv):
  #Find offset of self clock wrt NTP
  #Positive offset means NTP is ahead
  #Negative offset means NTP is behind
  offset=0
  #If offset is precalculated, to use that value pass it as 2nd arg
  #Otherwise calculate offset
  if(len(argv)>=2):
    offset=float(argv[1])
  else:
    offset=getNTPTime()
    with open('ntp_offset.txt','w') as file:
      file.write(str(offset))
  #Create a TCP/IP socket
  sock = socket(AF_INET, SOCK_STREAM)
  #Connect the socket to the port where the B is listening
  server_address = ('10.10.1.2', 10000)#link-0
  print('Connecting to {} port {}'.format(*server_address))
  sock.connect(server_address)

  try:
    #Hold sending and arrival times here
    packet_e2e_delay={}
    packet_index=0
    with open('sensor_data.txt','rb') as data:
      while(1):
        sensor_reading=bytearray(data.read(read_n_bytes))
        data.read(1)
        if(not sensor_reading):
          break
        #Size of packet_index is fixed to 4 bytes (32 bits). Therefore, number of packets is fixed to 2^32
        #First four bytes used as a simple header to track packet number.
        four_byte_header=bytearray("{0:04d}".format(packet_index).encode('ascii'))
        #Packet of size 46 bytes is formed, format: [4 byte header][42 byte long line]
        packet=four_byte_header+sensor_reading
        #Wait 15ms to avoid congestion in actual routers
        sleep(0.015)
        #Send packet, calculate transmission time and open a new record
        sock.sendall(packet)
        sending_time=time()+offset
        packet_e2e_delay[packet_index]=[]
        print("Packet-{} sent".format(packet_index))
        #Wait two responses
        response1=sock.recv(packet_size)
        response2=sock.recv(packet_size)
        print("Responses retrieved")
        #Trying to parse two responses to the same packet
        inc_packet_index1=-1
        inc_packet_index2=-1
        arrival_time1=-1
        arrival_time2=-1
        router_name1=''
        router_name2=''
        try:
          inc_packet_index1, router_name1, arrival_time1=parseResponse(response1)
        except:
          print("Parsing of the first response failed")
        try:  
          inc_packet_index2, router_name2, arrival_time2=parseResponse(response2)
        except:
          print("Parsing of the second response failed")
        #If there is no obvious corruption in the packets store results
        if(inc_packet_index1==packet_index and arrival_time1!=-1 and (router_name1=='r1' or router_name1=='r2')):
          packet_e2e_delay[packet_index].append((1000*(arrival_time1-sending_time), router_name1))
        if(inc_packet_index2==packet_index and arrival_time2!=-1 and (router_name2=='r1' or router_name2=='r2')):
          packet_e2e_delay[packet_index].append((1000*(arrival_time2-sending_time), router_name2))
        packet_index+=1
  finally:
      #If filename is provided as the 1st arg, create two files and write results
      if(len(argv)>=1):
        stat = open("r1_"+argv[0],'w')
        stat2 = open("r2_"+argv[0],'w')
        for key, value in packet_e2e_delay.items():
          if(value[0][1]=='r1'):
            stat.write(str(value[0][0])+"\n")
          else:
            stat2.write(str(value[0][0])+"\n")
          if(value[1][1]=='r2'):
            stat2.write(str(value[1][0])+"\n")
          else:
            stat.write(str(value[1][0])+"\n")
        stat.close()
        stat2.close()
      print('Closing socket...')
      sock.close()

if __name__ == "__main__":
    main(sys.argv[1:])