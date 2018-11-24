import sys
from time import *
from socket import *
from threading import *

#Define sizes in terms of bytes
header_size=4
packet_size=46
router1_IP=''
router2_IP=''

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
      payload=bytearray("ACK Via:{} At:{}".format(router_name,time()).encode('ascii'))
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