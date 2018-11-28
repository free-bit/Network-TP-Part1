import sys
from time import *
from socket import *
from threading import *
from queue import *

#Define sizes in terms of bytes
header_size=4
packet_size=46
processed1=False
processed2=False

#Thread implementation
def router_handler(i, serv_addr, router_address, queue, condition):
  print('Starting UDP thread-{} on {} port {}'.format(i,*serv_addr))
  #Create a new UDP socket, bind the ip & port number
  sock = socket(AF_INET, SOCK_DGRAM)
  sock.bind(serv_addr)
  try:
    global processed1
    global processed2
    while True:
      condition.acquire()
      condition.wait()
      print("Thread-"+str(i)+" sends the packet.")
      packet = queue.get()
      sock.sendto(packet, router_address)
      response, address = sock.recvfrom(packet_size)
      print("Thread-"+str(i)+" got the response.")
      queue.put(response)
      if(i==1):
        processed1=True
      else:
        processed2=True
      condition.notify()
      condition.release()
  finally:
      print('Socket is closed')
      sock.close()

def main(argv):
    #Create a TCP/IP socket
    sock = socket(AF_INET, SOCK_STREAM)

    #Bind the socket to the port
    #Define IP & port number of the server
    UDP_IP = ''
    UDP_MAIN_PORT = 10000 #s will send packets to this port
    UDP_PORT1 = 10001 #r1 will send packets to this port
    UDP_PORT2 = 10002 #r2 will send packets to this port
    main_serv_addr = (UDP_IP, UDP_MAIN_PORT)
    serv_addr1 = (UDP_IP, UDP_PORT1)
    serv_addr2 = (UDP_IP, UDP_PORT2)
    router_addr1 = ('10.10.2.2', 5010)#link-1 (r1)
    router_addr2 = ('10.10.4.2', 5010)#link-3 (r2)
    print('Starting TCP server on {} port {}'.format(*main_serv_addr))
    sock.bind(main_serv_addr)
    sock.listen(1)
    q1=Queue()
    q2=Queue()
    condition1=Condition(Lock())
    condition2=Condition(Lock())
    t1=Thread(target=router_handler, args=(1, serv_addr1, router_addr1, q1, condition1))
    t2=Thread(target=router_handler, args=(2, serv_addr2, router_addr2, q2, condition2))
    t1.start()
    t2.start()
    try:
        while True:
            # Wait for a connection
            print('Waiting for a connection')
            conn, client_address = sock.accept()
            print('Connection from ip:{} on port number:{}'.format(*client_address))
            #Receive the packet
            while True:
                packet, address = conn.recvfrom(packet_size)
                # four_byte_header=packet[:header_size]
                # payload=bytearray("ACK Via:{} At:{}".format("r1",time()).encode('ascii'))
                # packet=four_byte_header+payload
                # conn.sendall(packet)
                global processed1
                global processed2
                processed1=False
                processed2=False
                if(packet):
                    condition1.acquire()
                    condition2.acquire()
                    packet_index=int(packet[:header_size])
                    print("Packet number {} is being copied and sent to routers:".format(packet_index))
                    #Duplicate the packet
                    q1.put(packet)
                    condition1.notify()
                    condition1.release()
                    q2.put(packet)
                    condition2.notify()
                    condition2.release()
                    while(not processed1 or not processed2):
                        condition1.acquire()
                        condition1.release()
                        condition2.acquire()
                        condition2.release()    
                    # if(not processed1):
                    #     with condition1:
                    #         condition1.wait()
                    #         response1=q1.get()
                    # if(not processed2):
                    #     with condition2:
                    #         condition2.wait()
                    #         response2=q2.get()
                    response1=q1.get()
                    response2=q2.get()
                    print(response1)
                    print(packet)
                    conn.sendall(response1)
                    conn.sendall(response2)
                else:
                    print("Connection is over")
                    break
    finally:
        # Close the connection and the socket
        conn.close()

if __name__ == "__main__":
    main(sys.argv[1:])

# print(gethostbyname(gethostname()))
#print(gethostbyname("ceng.metu.edu.tr"))
# Listen for incoming connections