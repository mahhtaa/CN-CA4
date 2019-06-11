import sys
import time
import threading
from signal import *
from copy import deepcopy
from link_layer import *
from IPpacket import *
from route import *
from exceptions import *

def links_data():
	with open(sys.argv[1]) as file:
		lines = file.readlines()
		return lines
# exit program with CTRL + C

class Node:
	def __init__(self):
		lines = links_data()
		ip, port = lines[0].split()
		self.link_layer = LinkLayer(ip,port, self.packet_handler, self.update_dv)
		self.neighbors = {}
		for id,line in enumerate(lines[1:]):
			ip, port, vaddr_self, vaddr_neighbor = line.split()
			self.neighbors[vaddr_neighbor] = (id,vaddr_self)
			self.link_layer.add_interface(ip, port, vaddr_neighbor, vaddr_self)

		self.distance_vector = {saddr:Route(saddr,0,[]) for i,saddr in list(self.neighbors.values())}
		self.dv_lock = threading.Lock()

	def send_DV_to_neighbors(self):
		while(True):
			time.sleep(1)
			self.dv_lock.acquire()
			distance_vector = deepcopy(self.distance_vector)
			self.dv_lock.release()
			for naddr in self.neighbors:
				packet = IPPacket(self.neighbors[naddr][1], naddr, CONTROL, distance_vector)
				self.link_layer.send(naddr, packet)

	def commandline(self):
		while(True):
			print(">", end = " ")
			command_words = input().split()
			
			if(command_words[0] == "interfaces"):
				print("id\trem\t\tloc")
				for naddr in self.neighbors:
					print("%s\t%s\t%s" %(self.neighbors[naddr][0], naddr, self.neighbors[naddr][1]))
			
			elif(command_words[0] == "routes"):
				print("cost\tdst\t\tloc")
				self.dv_lock.acquire()
				DV = deepcopy(self.distance_vector)
				self.dv_lock.release()
				for dest in DV:
					loc = self.neighbors[DV[dest].next_hop][1] if DV[dest].next_hop in self.neighbors \
																	else DV[dest].next_hop
					print("%s\t%s\t%s" %(DV[dest].cost, dest, loc))
					

			elif(command_words[0] ==  "down"):
				# for naddr, in self.neighbors.items()

			elif(command_words[0] == "up"):
				pass

			elif(command_words[0] == "send"):
				dest = command_words[1]
				self.dv_lock.acquire()
				if dest in self.distance_vector:
					next_hop = self.distance_vector[dest].next_hop
					packet = IPPacket(self.neighbors[next_hop][1], dest, int(command_words[2]), " ".join(command_words[3:]))
					self.link_layer.send(next_hop, packet)
				self.dv_lock.release()


			elif(command_words[0] == "q"):
				return

	def receive(self):
		while(True):
			self.link_layer.receive()
				
	def update_dv(self, packet):
		neighbor_dv = packet.data
		if type(neighbor_dv)!=dict:
			return
		
		self.dv_lock.acquire()

		# if route included this hop and the destination is unreachable from this hop now, delete route
		for destination in self.distance_vector:
			if self.distance_vector[destination].next_hop == packet.previous_hop \
											and destination not in neighbor_dv:
				del self.distance_vector[destination]

		for destination in neighbor_dv:
			# don't update if the route includes the node itself
			interfaces = [interface[1] for interface in self.neighbors.values()]
			try:
				for hop in neighbor_dv[destination].route:
					if hop in interfaces:
						raise LoopException()
			except LoopException:
				continue

			# calculate cost of path to destination through neighbor
			path_through_neighbor = 1 + neighbor_dv[destination].cost
			route = deepcopy(neighbor_dv[destination].route)
			route.insert(0,packet.previous_hop)

			if destination in self.distance_vector:
				if path_through_neighbor < self.distance_vector[destination].cost:
					self.distance_vector[destination] = Route(packet.previous_hop, path_through_neighbor, route)
				elif self.distance_vector[destination].next_hop == packet.previous_hop:
					self.distance_vector[destination] = Route(packet.previous_hop, path_through_neighbor, route)
			else:
				self.distance_vector[destination] = Route(packet.previous_hop, path_through_neighbor, route)

		self.dv_lock.release()

	def packet_handler(self, packet):
		interfaces = [interface[1] for interface in self.neighbors.values()]
		if packet.daddr in interfaces:
			packet.print_info(self.neighbors[packet.previous_hop][0])
		else:
			if packet.daddr in self.distance_vector:
				self.link_layer.send(self.distance_vector[packet.daddr].next_hop, packet)

	def exit(*args):
		print ("")
		sys.exit()


def main():
	node = Node()
	
	functions = [node.commandline, node.send_DV_to_neighbors, node.receive]
	threads = []
	
	signal(SIGINT, node.exit)
	
	for f in functions:
		new_thread = threading.Thread(target = f)
		new_thread.daemon = True
		threads.append(new_thread)
		new_thread.start()

	cmd = threads[0]
	cmd.join()
	# exit program with q
	node.exit()

if __name__ == '__main__':
	main()