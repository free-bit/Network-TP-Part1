import sys
import struct
from time import *
from socket import *
from threading import *

#Define sizes in terms of bytes
header_size=4
packet_size=46
router1_IP=''
router2_IP=''
offset=0

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

#Thread implementation
def sock_listener(i, serv_addr):
  #Create a new UDP socket, bind the ip & port number 
  sock = socket(AF_INET, SOCK_DGRAM)
  sock.bind(serv_addr)
  try:
    print('Thread-{} is listening to port:{}'.format(i, serv_addr[1]))
    while True:
      packet, address = sock.recvfrom(packet_size)
      four_byte_header=packet[:header_size]
      packet_index=int(four_byte_header)
      router_name=''
      if(serv_addr[1]==5000):
        router_name='r1'
      else:
        router_name='r2'
      print('Thread-{} has received packet-{} from router:{}-{}/{}'.format(i, packet_index, router_name, *address))
      payload=bytearray("ACK Via:{} At:{}".format(router_name, time()-offset).encode('ascii'))
      response=four_byte_header+payload
      sock.sendto(response, address)
  finally:
      print('Socket is closed')
      sock.close()

def main(argv):
  #Define IP & port number of the server
  UDP_IP = ''
  UDP_PORT1 = 5000 #r1 will send packets to this port
  UDP_PORT2 = 5001 #r2 will send packets to this port
  serv_addr1 = (UDP_IP, UDP_PORT1)
  serv_addr2 = (UDP_IP, UDP_PORT2)
  global offset
  offset=getNTPTime()
  #Initialize and start threads
  print('Server d is running at IP:{} on ports:{} & {}'.format(serv_addr1[0],serv_addr1[1],serv_addr2[1]))
  t1=Thread(target=sock_listener, args=(1, serv_addr1,))
  t2=Thread(target=sock_listener, args=(2, serv_addr2,))
  t1.start()
  t2.start()
  t1.join()
  t2.join()

if __name__ == "__main__":
    main(sys.argv[1:])