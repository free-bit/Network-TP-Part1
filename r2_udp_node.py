import sys
from socket import *
from threading import *

#Define sizes in terms of bytes
header_size=4
packet_size=46

def main(argv):
  router_addr_for_B = ('', 5010)
  router_addr_for_d = ('', 5011)

  d_addr=('10.10.5.2',5001)#link-4
  #Create two UDP sockets one for B one for d
  B_sock=socket(AF_INET, SOCK_DGRAM)
  B_sock.bind(router_addr_for_B)
  # B_sock.settimeout(2)
  b_index=0
  d_sock=socket(AF_INET, SOCK_DGRAM)
  d_sock.bind(router_addr_for_d)
  # d_sock.settimeout(2)
  d_index=0 
  try:
    while True:
      #Wait a message from B
      print("Waiting for a message from B on port number: {}...".format(5010))
      message_from_B, B_addr = B_sock.recvfrom(packet_size)
      #Forward the message to the destination d
      d_sock.sendto(message_from_B, d_addr)
      #Wait until getting a response from d
      print("Packet was forwarded to d.\n Waiting for a response from d on port number: {}...".format(5001))
      response_from_d=''
      response_from_d, d_addr = d_sock.recvfrom(packet_size)
      #Forward the response or the error to B
      B_sock.sendto(response_from_d, B_addr)
      print("Response was forwarded to B.")
  finally:
      print('Sockets are closed')
      B_sock.close()
      d_sock.close()

if __name__ == "__main__":
    main(sys.argv[1:])