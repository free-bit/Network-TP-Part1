import sys
from time import *
from socket import *

#Define sizes in terms of bytes
read_n_bytes=42
header_size=4
packet_size=46



def parseResponse(res):
  packet_index=int(res[:header_size])
  str_list=str(res[header_size:]).split(' ')
  ack=str_list[0]
  router_name=str_list[1][len("Via:"):]
  time=float(str_list[2][len("At:"):-1])
  return (packet_index, router_name, time)

def main(argv):
  # Create a TCP/IP socket
  sock = socket(AF_INET, SOCK_STREAM)
  # sock.settimeout(10)
  # Connect the socket to the port where the server is listening
  server_address = ('', 10000)
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
        #Packet of size 46 bytes is formed
        packet=four_byte_header+sensor_reading
        sock.sendall(packet)
        print("Packet sent")
        packet_e2e_delay[packet_index]=time()
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