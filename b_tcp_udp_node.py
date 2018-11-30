import sys
from time import *
from socket import *
from threading import *
from queue import *

#Define sizes in terms of bytes
header_size=4
packet_size=46
#Control flags for threads
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
      packet = queue.get()
      sock.sendto(packet, router_address)
      print("Thread-"+str(i)+" sent the packet to router.")
      response, address = sock.recvfrom(packet_size)
      queue.put(response)
      if(i==1):
        processed1=True
      else:
        processed2=True
      condition.notify()
      condition.release()
      print("Thread-"+str(i)+" forwarded the response from router to main TCP thread.")
  finally:
      print('Socket is closed')
      sock.close()

def main(argv):
    #Create a TCP/IP socket
    sock = socket(AF_INET, SOCK_STREAM)

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
    #Bind the socket to the port and start listening (at most one connection)
    sock.bind(main_serv_addr)
    sock.listen(1)
    #Initialize all variables required
    q1=Queue()
    q2=Queue()
    condition1=Condition(Lock())
    condition2=Condition(Lock())
    t1=Thread(target=router_handler, args=(1, serv_addr1, router_addr1, q1, condition1))
    t2=Thread(target=router_handler, args=(2, serv_addr2, router_addr2, q2, condition2))
    t1.start()
    t2.start()
    conn=0
    try:
        while True:
            # Wait for a connection
            print('Waiting for a connection')
            conn, client_address = sock.accept()
            print('Connection from ip:{} on port number:{}'.format(*client_address))
            while True:
                #Receive the packet
                packet, address = conn.recvfrom(packet_size)
                global processed1
                global processed2
                processed1=False
                processed2=False
                if(packet):
                    condition1.acquire()
                    condition2.acquire()
                    packet_index=int(packet[:header_size])
                    print("Packet number {} is being copied and sent to routers:".format(packet_index))
                    #Duplicate the packet and wake threads up
                    q1.put(packet)
                    condition1.notify()
                    condition1.release()
                    q2.put(packet)
                    condition2.notify()
                    condition2.release()
                    #Until having both responses, wait (non-busy) 
                    while(not processed1 or not processed2):
                        condition1.acquire()
                        condition1.release()
                        condition2.acquire()
                        condition2.release()
                    #Collect responses  
                    response1=q1.get()
                    response2=q2.get()
                    #Forward to s
                    conn.sendall(response1)
                    conn.sendall(response2)
                    print("Main thread has sent both responses.\n")
                else:
                    print("Connection is over")
                    break
    finally:
        #Close the connection and the socket
        try:
            print("Closing the connection...")
            conn.close()
        #If no connection established skip
        except AttributeError:
            pass

if __name__ == "__main__":
    main(sys.argv[1:])