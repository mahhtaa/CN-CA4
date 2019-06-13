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
		self.link_layer = LinkLayer(ip,port)
		self.link_layer.register_handler(DATA, self.packet_handler)
		self.link_layer.register_handler(CONTROL, self.update_dv)
		self.link_layer.register_handler(TRACEROUTE, self.traceroute)
		self.neighbors = {}
		for id,line in enumerate(lines[1:]):
			ip, port, vaddr_self, vaddr_neighbor = line.split()
			self.neighbors[vaddr_neighbor] = (id,vaddr_self,UP)
			self.link_layer.add_interface(ip, port, vaddr_neighbor, vaddr_self)

		self.distance_vector = {saddr:Route(saddr,0,[saddr]) for i,saddr,up in list(self.neighbors.values())}
		self.dv_lock = threading.Lock()
		self.traceroute_dest = None
		self.traceroute_ttl = None
		self.traceroute_hops = []

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
			command = input()
			command_words = command.split(' ', 3)


			if(command_words[0] == "interfaces"):
				print("id\trem\t\tloc")
				for naddr in self.neighbors:
					if self.neighbors[naddr][2] == UP:
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
					

			elif(command_words[0] == "down"):
				for naddr,info in self.neighbors.items():
					if info[0] == int(command_words[1]):
						self.down_interface(naddr,info[1])
						l = list(self.neighbors[naddr])
						l[2] = DOWN
						self.neighbors[naddr] = tuple(l)
						print("interface %d is now disabled" %info[0])
						break


			elif(command_words[0] == "up"):
				self.dv_lock.acquire()
				for naddr,info in self.neighbors.items():
					if info[0] == int(command_words[1]):
						self.distance_vector[info[1]] = Route(info[1],0,[info[1]])
						self.link_layer.up_interface(naddr)
						l = list(self.neighbors[naddr])
						l[2] = UP
						self.neighbors[naddr] = tuple(l)
						print("interface %d is now enabled" %info[0])
						self.dv_lock.release()
						break

			elif(command_words[0] == "send"):
				dest = command_words[1]
				if len(command_words[3]) > (MTU - MAXHEADER):
					print("size of IPpacket exceeds Maximum Transfer Size!")
					continue
				self.dv_lock.acquire()
				if dest in self.distance_vector:
					next_hop = self.distance_vector[dest].next_hop
					packet = IPPacket(self.neighbors[next_hop][1], dest, int(command_words[2]), command_words[3])
					self.link_layer.send(next_hop, packet)
				self.dv_lock.release()


			elif(command_words[0] == "traceroute"):
				dest = command_words[1]
				self.dv_lock.acquire()
				if dest in self.distance_vector:
					self.traceroute_dest = dest
					self.traceroute_ttl = 1
					self.traceroute_hops = []
					next_hop = self.distance_vector[dest].next_hop
					packet = IPPacket(self.neighbors[next_hop][1], dest, TRACEROUTE, "", 1)
					self.link_layer.send(next_hop, packet)
				self.dv_lock.release()


			elif(command_words[0] == "q"):
				for naddr,info in self.neighbors.items():
					self.down_interface(naddr,info[1])
				return


	def receive(self):
		while(True):
			self.link_layer.receive()

	def down_interface(self, naddr, saddr):
		self.dv_lock.acquire()
		if saddr in self.distance_vector:
			del self.distance_vector[saddr]
		for dest in deepcopy(self.distance_vector):
			if self.distance_vector[dest].next_hop == naddr:
				del self.distance_vector[dest]
		# send distance vector one last time before downing interface
		packet = IPPacket(self.neighbors[naddr][1], naddr, CONTROL, deepcopy(self.distance_vector))
		self.link_layer.send(naddr, packet)
		self.link_layer.down_interface(naddr)
		self.dv_lock.release()
				
	def update_dv(self, packet):
		neighbor_dv = packet.data
		if type(neighbor_dv)!=dict:
			return
		
		self.dv_lock.acquire()

		# if route included this hop and the destination is unreachable from this hop now, delete route
		for destination in deepcopy(self.distance_vector):
			if self.distance_vector[destination].next_hop == packet.previous_hop \
					and destination not in neighbor_dv:
				del self.distance_vector[destination]

		link_down = False
		for destination in deepcopy(self.distance_vector):
			if self.distance_vector[destination].next_hop == packet.previous_hop \
					and packet.previous_hop not in neighbor_dv:
				link_down = True
				del self.distance_vector[destination]
		if link_down:
			self.dv_lock.release()
			return
		
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
				elif path_through_neighbor > self.distance_vector[destination].cost \
						and self.distance_vector[destination].next_hop == packet.previous_hop:
					self.distance_vector[destination] = Route(packet.previous_hop, path_through_neighbor, route)
			else:
				self.distance_vector[destination] = Route(packet.previous_hop, path_through_neighbor, route)

		self.dv_lock.release()

	def traceroute(self, packet):
		interfaces = [interface[1] for interface in self.neighbors.values()]
		if packet.ttl > 0:
			packet.ttl -= 1
			if packet.ttl == 0:
				hops = [packet.previous_hop, self.neighbors[packet.previous_hop][1]]
				if packet.daddr in interfaces:
					if packet.daddr != self.neighbors[packet.previous_hop][1]:
						hops.append(packet.daddr)
				packet.data = hops
				packet.daddr = packet.saddr
				packet.saddr = self.neighbors[packet.previous_hop][1]
		elif packet.ttl == 0:
			if packet.daddr in interfaces:
				self.traceroute_hops.extend(packet.data)
				if self.traceroute_dest in packet.data:
					print("Traceroute from %s to %s" %(packet.daddr,self.traceroute_dest))
					for i,hop in enumerate(self.traceroute_hops):
						print(i,hop)
					print("Traceroute finished in %d hops" %len(self.traceroute_hops))
					return
				else:
					self.traceroute_ttl += 1
					packet.saddr = self.neighbors[packet.previous_hop][1]
					packet.daddr = self.traceroute_dest
					packet.ttl = self.traceroute_ttl
					packet.data = ""
		
		self.dv_lock.acquire()
		if packet.daddr in self.distance_vector:
			next_hop = self.distance_vector[packet.daddr].next_hop
			self.link_layer.send(next_hop, packet)
		self.dv_lock.release()



	def packet_handler(self, packet):
		interfaces = [interface[1] for interface in self.neighbors.values()]
		if packet.daddr in interfaces:
			packet.print_info(self.neighbors[packet.previous_hop][0])
		else:
			if packet.daddr in self.distance_vector:
				self.link_layer.send(self.distance_vector[packet.daddr].next_hop, packet)

	def exit(*args):
		print ("Goodbye!")
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