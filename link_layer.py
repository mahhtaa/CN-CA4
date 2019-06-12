from socket import *
import pickle
from params import *

class Link:
	def __init__(self, ip, port, vaddr_self):
		self.self_vaddr = vaddr_self
		self.neighbor_ip = ip
		self.neighbor_port = port
		self.socket = socket(AF_INET, SOCK_DGRAM)
		self.up = True

	def send(self, data):
		self.socket.sendto(data, (self.neighbor_ip, self.neighbor_port))


class LinkLayer:
	def __init__(self, ip, port, packet_handler, dv_handler):
		self.socket = socket(AF_INET, SOCK_DGRAM)
		self.socket.bind((ip, int(port)))
		self.interfaces = {}
		self.handlers = {DATA: packet_handler, CONTROL: dv_handler}

	def add_interface(self, ip, port, vaddr_neighbor, vaddr_self):
		self.interfaces[vaddr_neighbor] = Link(ip, int(port), vaddr_self)

	def down_interface(self, vaddr_neighbor):
		self.interfaces[vaddr_neighbor].up = False

	def up_interface(self, vaddr_neighbor):
		self.interfaces[vaddr_neighbor].up = True

	def send(self, vaddr, packet):
		if not self.interfaces[vaddr].up:
			return
		packet.previous_hop = self.interfaces[vaddr].self_vaddr
		data = pickle.dumps(packet)
		self.interfaces[vaddr].send(data)

	def receive(self):
		data, address = self.socket.recvfrom(MTU)
		packet = pickle.loads(data)
		if not self.interfaces[packet.previous_hop].up:
			return
		self.handlers[packet.protocol](packet)
