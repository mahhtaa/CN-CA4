from socket import *
import pickle
from params import *

class Link:
	def __init__(self, ip, port):
		self.neighbor_ip = ip
		self.neighbor_port = port
		self.socket = socket(AF_INET, SOCK_DGRAM)

	def send(self, data):
		self.socket.sendto(data, (self.neighbor_ip, self.neighbor_port))


class LinkLayer:
	def __init__(self, ip, port):
		self.socket = socket(AF_INET, SOCK_DGRAM)
		self.socket.bind((ip, int(port)))
		self.interfaces = {}

	def add_interface(self, ip, port, vaddr_neighbor):
		self.interfaces[vaddr_neighbor] = Link(ip, int(port))

	def send(self, vaddr, packet):
		data = pickle.dumps(packet)
		self.interfaces[vaddr].send(data)

	def receive(self):
		data, address = self.socket.recvfrom(MTU)
		packet = pickle.loads(data)
		return packet
