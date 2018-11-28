import sys
from socket import *
from threading import *

#Define sizes in terms of bytes
header_size=4
packet_size=46

def main(argv):
  router_addr_for_B = ('', int(argv[0]))#5010-5012
  router_addr_for_d = ('', int(argv[1]))#5011-5013

  D_PORT = int(argv[2])#5000 or 5001
  D_ADDR_LIST = [('10.10.3.2', D_PORT),\
                 ('10.10.5.2', D_PORT)]
  # B_PORT = 5005
  # B_ADDR_LIST = [('10.10.1.2',B_PORT),\
  #                ('10.10.2.1',B_PORT),\
  #                ('10.10.4.1',B_PORT)]

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
      print("Waiting for a message from B...")
      message_from_B, B_addr = B_sock.recvfrom(packet_size)
      #Forward the message to the destination d
      d_sock.sendto(message_from_B, ('', D_PORT))#TODO: tuple
      #Wait until getting a response from d
      print("Packet was forwarded to d.\n Waiting for a response from d...")
      response_from_d=''
      response_from_d, d_addr = d_sock.recvfrom(packet_size)
      print("Response was forwarded to B.")
      #Forward the response or the error to B
      B_sock.sendto(response_from_d, B_addr)
  finally:
      print('Sockets are closed')
      B_sock.close()
      d_sock.close()

if __name__ == "__main__":
    if(len(sys.argv)<2):
      print("Expected the port number for destination")
      sys.exit()
    main(sys.argv[1:])