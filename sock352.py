
import binascii
import socket as syssock
import struct
import sys
import random

# these functions are global to the class and
# define the UDP ports all messages are sent
# and received from

#Bit flags
SOCK352_SYN = 0x01
SOCK352_FIN = 0x02
SOCK352_ACK = 0x04
SOCK352_RESET = 0x08
SOCK352_HAS_OPT = 0xA0

global sock
def init(UDPportTx,UDPportRx):  #INitialize UPS socket
    global sock
    sock = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)
    return

class socket:

    def __init__(self):
        global sock
        self.sock = sock
        self.fmt = '!BBBBHHLLQQLL'
        self.version = 0x1
        self.flags=0
        self.opt_ptr=0
        self.protocol=0
        self.header_len=struct.calcsize(self.fmt)
        self.checksum=0
        self.source_port=0
        self.dest_port=0
        self.sequence_no=0
        self.ack_no=0
        self.window=0
        self.payload_len=0
        self.addr = 0
        return

    def bind(self,address):
        self.sock.bind(address)
        return

    def connect(self,address):
        count = 0
        while count < 4:
            self.flags = SOCK352_SYN  					# set flag to SYN
            self.sequence_no = random.randint(0,500) 	# sequence number
            request =self.help_pack() 					# pack request ready to send
            self.sock.settimeout(0.2)  					# Timeout for 0.2

            index = 0
            while index<4:
                try:
                    self.sock.sendto(request, address)
                    data,address=self.sock.recvfrom(self.header_len)  # recieve ACK
                except syssock.timeout:
                    if(index<5):
                        index=index+1
                    else:
                        print "Connection Failed. 3 Attempts"
                        sys.exit(1)
                else:
                    index=5

            header = struct.unpack(self.fmt,data)
            if(header[1]==SOCK352_ACK and header[9]==self.sequence_no+1):  #if ACK is seq+1
                print "Server ACK received"
                self.flags = SOCK352_ACK 				# set flag to ACK
                self.sequence_no = self.sequence_no + 1 # set sequence number
                self.ack_no = header[8] + 1				# set ACK number
                ack = self.help_pack()  				#pack and send back ACK and the connection finished
                self.sock.sendto(ack, address)
                self.addr = address 					#connection formed
                count=7
            elif(header[1]==SOCK352_RESET and header[9]==self.sequence_no+1):
                if count<5:
                    count += 1
                else:
                    print "Connection Failed"
                    sys.exit(1)
        return

    def listen(self,backlog):
        pass
        return

    def accept(self):
        data, address = self.sock.recvfrom(self.header_len)    #recieve the request
        clientsock = socket()                                  # create new socket for client
        header = struct.unpack(self.fmt,data)

        # make sure it is connection request
        while(header[1]!=SOCK352_SYN):
            clientsock.flags=SOCK352_RESET  				#set flag to reset
            clientsock.sequence_no = random.randint(0,500)  #set sequence number
            clientsock.ack_no = sequence_no+1  				#set the ACK number
            reset = clientsock.help_pack() 					#packet struct
            clientsock.sock.settimeout(0.2)  				#set time out to 0.2

            index = 0
            while index<6:
                try:
                    clientsock.sock.sendto(reset, address)
                    data,address=clientsock.sock.recvfrom(clientsock.header_len)
                except syssock.timeout:
                    if index<5:
                        index=index+1
                    else:
                        print "Connection Failed. "
                        sys.exit(1)
                else:
                    index=7
            header = struct.unpack(self.fmt,data)
        print "Client request received. "

        # connection now ready
        clientsock.flags=SOCK352_ACK	# set flag to ACK
        clientsock.sequence_no = 0		# set sequence number
        clientsock.ack_no = header[8]+1	# set ack = seq + 1
        ack = clientsock.help_pack()
        clientsock.sock.settimeout(0.2)

        index = 0
        while index<6:
            try:
                clientsock.sock.sendto(ack, address)
                data,address=clientsock.sock.recvfrom(clientsock.header_len)
            except syssock.timeout:
                if(index<5):
                    index=index+1
                else:
                    print "Connection Failed."
                    sys.exit(1)
            else:
                index=7
        clientsock.sock.settimeout(None)
        header = struct.unpack(self.fmt,data)
        while header[1]!=SOCK352_ACK or header[9]!=clientsock.sequence_no+1:
            clientsock.flags=SOCK352_RESET	# RESET bit set
            clientsock.sequence_no=0		# set sequence number
            clientsock.ack_no = header[8]+1	# update ack_no
            reset = clientsock.help_pack()
            index = 0
            while index<6:
                try:
                    clientsock.sock.sendto(reset, address)
                    data,address=clientsock.sock.recvfrom(clientsock.header_len)
                except syssock.timeout:
                    if(index<5):
                        index=index+1
                    else:
                        print "Connection Failed. "
                        sys.exit(1)
                else:
                    index=7
            clientsock.sock.settimeout(None)
            header = struct.unpack(self.fmt,data)
        print "Client ACK arrived. "

        clientsock.addr = address
        return (clientsock,address)

    def close(self):
        # send fin request
        self.flags = SOCK352_FIN
        packet = self.help_pack()
        self.sock.sendto(packet,self.addr)
        print "Socket closed."
        self.sock.close()

    def send(self,buffer):
        bytessent = 0     # fill in your code here
        max_size = 64 * 1024
        remain_part = len(buffer)
        if remain_part > max_size:  # counter
            to_sent = max_size
        else:
            to_sent = remain_part

        # set header
        self.sequence_no = 0
        self.payload = to_sent
        while (remain_part > 0):									# when still things to send
            segment = buffer[bytessent : bytessent + to_sent] 		# get  segment
            packet = struct.pack('!BBBBHHLLQQLL%ds' %(len(segment)),
        	self.version, self.flags, self.opt_ptr, self.protocol, self.header_len,
        	self.checksum, self.source_port, self.dest_port,
       		self.sequence_no, self.ack_no, self.window, self.payload_len, segment)
            self.sock.settimeout(0.2) 								# set time out to 0.2
            i = 0
            while i < 6:
				index = 0
				while index < 6:
					try:
						self.sock.sendto(packet,self.addr)
						data,address = self.sock.recvfrom(self.header_len)
					except syssock.timeout:
						if index < 5 :
							index += 1
						else:
							print "Connection Failed. Due to Send()."
							sys.exit(1)
					else:
						index = 7
				self.sock.settimeout(None)
				header = struct.unpack(self.fmt,data)
				if header[9] == self.sequence_no and header[1] == SOCK352_ACK:
					print "ACK received in send()"
					bytessent = to_sent
					remain_part = remain_part - bytessent
					if (remain_part >= max_size):
						to_sent = max_size
					else:
						to_sent = remain_part

					self.sequence_no = self.sequence_no+1 #set sequence number
					self.payload_len = bytes_to_sent #set payload length
					header = self.help_pack() #set header
					i=7
				else:
					if(i<5):
						i=i+1
						while i < 6:
							index = 0
							while index < 6:
								try:
									self.sock.sendto(packet, self.addr)
									data,address=self.sock.recvfrom(self.header_len) # recieve the ACK
								except syssock.timeout:
									if index < 5:
										index = index + 1
									else:
										print "Connection Failed. Due to Send()"
										sys.exit(1)
								else:
									index = 7
							self.sock.settimeout(None)
					else:
						print "Connection Failed. Due to Send()"
						sys.exit(1)
        return bytessent


    def recv(self,nbytes):
        bytesreceived = 0     # fill in your code here
        actual_receive = 0
        data = 0
        max_size = 64 * 1024
        while actual_receive < nbytes:
            # receive and unpack packet
            data,address = self.sock.recvfrom(min(nbytes - actual_receive, self.header_len + max_size))
            (version,flags,opt_ptr,protocol,header_len,checksum,source_port,dest_port,sequence_no,ack_no,window,payload_len,data) = struct.unpack('!BBBBHHLLQQLL%ds'%(len(data)-40), data)

            if(len(data) != payload_len):    # check if some bytes lost
                continue

            actual_receive += payload_len

            if(bytesreceived == 0):
                bytesreceived = data
            else:
                bytesreceived += data

            self.flags = SOCK352_ACK
            self.ack_no = sequence_no
            ack = self.help_pack()
            self.sock.sendto(ack, self.addr)
        return bytesreceived

    # ======= help pack the header packet ==========
    def help_pack(self):
        packet = struct.pack(self.fmt,self.version,self.flags,self.opt_ptr,self.protocol,self.header_len,self.checksum,self.source_port,self.dest_port,self.sequence_no,self.ack_no,self.window,self.payload_len)
        return packet