import sys
import struct
from time import *
from socket import *

#Define sizes in terms of bytes
read_n_bytes=42
header_size=4
packet_size=46

def getFraction(binary_repr):
  fraction=0.0
  ctr=1
  for bit in binary_repr:
    if(bit=="1"):
     fraction+=1/2**ctr
    ctr+=1
  return fraction

def getNTPTime(host = "pool.ntp.org"):
    port = 123
    buf = 1024
    host_address = (host,port)

    #Subtract 70 years of difference
    diff = 2208988800

    #Connect to ntp server
    client=socket(AF_INET, SOCK_DGRAM)
    client.settimeout(1)
    delay=10000
    offset=0
    delay_offset_pair=(delay, offset)
    #Send requests at least getting 8 replies
    i=0
    while i<8:
      req=('\x1b'+47*'\0').encode()
      client.sendto(req, host_address)
      #Save current time
      client_tx=time()
      #Wait response
      data=0
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
      i+=1
    #if all packets fail, restart
    if(not offset):
      getNTPTime()
    return offset
    client.close()

def parseResponse(res):
  packet_index=int(res[:header_size])
  str_list=str(res[header_size:]).split(' ')
  ack=str_list[0]
  router_name=str_list[1][len("Via:"):]
  time=float(str_list[2][len("At:"):-1])
  return (packet_index, router_name, time)

def main(argv):
  #Create a TCP/IP socket
  sock = socket(AF_INET, SOCK_STREAM)
  #Connect the socket to the port where the server is listening
  server_address = ('', 10000)
  print('Connecting to {} port {}'.format(*server_address))
  sock.connect(server_address)
  #Find offset of self clock wrt NTP
  #Positive offset means NTP is ahead
  #Negative offset means NTP is behind
  offset=getNTPTime()

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
        #Packet of size 46 bytes is formed
        packet=four_byte_header+sensor_reading
        sock.sendall(packet)
        print("Packet sent")
        packet_e2e_delay[packet_index]=time()-offset
        packet_index+=1
        #Wait two responses
        response1=sock.recv(packet_size)
        print("Response-1 retrieved")
        response2=sock.recv(packet_size)
        print("Response-2 retrieved")
        #Trying to parse two responses to the same packet
        try:
          inc_packet_index1, router_name1, arrival_time1=parseResponse(response1)
          inc_packet_index2, router_name2, arrival_time2=parseResponse(response2)
          if(inc_packet_index1!=inc_packet_index2):
            raise Exception
          sending_time=packet_e2e_delay[inc_packet_index1]
          packet_e2e_delay[inc_packet_index1]=[(arrival_time1-sending_time, router_name1),\
                                               (arrival_time2-sending_time, router_name2)]
        #Parsing failed
        except Exception as e:
          print(e)
          pass
  finally:
      if(len(argv)==1):
        stat = open("r1_"+argv[0],'w')
        stat2 = open("r2_"+argv[0],'w')
        for key, value in packet_e2e_delay.items():
          stat.write(str(value[0][0])+"\n")
          stat2.write(str(value[1][0])+"\n")
        stat.close()
        stat2.close()
      # print(packet_e2e_delay)
      print('Closing socket...')
      sock.close()

if __name__ == "__main__":
    main(sys.argv[1:])