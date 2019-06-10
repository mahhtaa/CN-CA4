import sys
import time
from link_layer import *
from IPpacket import *
import threading

def links_data():
	with open(sys.argv[1]) as file:
		lines = file.readlines()
		return lines
	
class Node:
	def __init__(self):
		lines = links_data()
		ip, port = lines[0].split()
		self.link_layer = LinkLayer(ip,port)
		self.neighbors = {}
		self.neighbors_id = {}
		for i in len(lines):
			ip, port, vaddr_self, vaddr_neighbor = lines[i].split()
			self.neighbors[vaddr_neighbor] = vaddr_self
			self.neighbors_id[vaddr_neighbor] = i
			self.link_layer.add_interface(ip, port, vaddr_neighbor)

		self.distance_vector = {saddr:{saddr:0} for saddr in list(self.neighbors.values())}
		self.dv_lock = threading.Lock()

	def send_DV_to_neighbors(self):
		while(True):
			time.sleep(1)
			self.dv_lock.acquire()
			distance_vector = self.distance_vector
			self.dv_lock.release()
			for naddr in self.neighbors:
				packet = IPPacket(self.neighbors[naddr] ,naddr, CONTROL, distance_vector)
				self.link_layer.send(naddr, packet)

	def command_parser(self):
		while(True):
			command_words = input().split()
			if(command_words[0] == "interfaces"):
				print("id 		rem 		loc")
				for vaddr_neighbor in neighbors:
					print("%s 		%s 		%s", neighbors_id[vaddr_neighbor], vaddr_neighbor, neighbors[vaddr_neighbor])
			elif(command_words[0] == "routes"):
				print("cost 		dst 		loc")
				# #####about distsnce vectore
			elif(command_words[0] ==  "down"):
				print("")
			elif(command_words[0] == "up"):
				# 
				pass

			elif(command_words[0] == "send"):
				#
				pass

			elif(command_words[0] == "q"):
				#
				pass

	def recieve(self):
		while(True):
			packet = self.link_layer.receive()
			if(packet.protcol == DATA):
				packet.print()
			elif(packet.protcol == CONTROL):
				#forward & update
				pass
			else:	
				pass
				



def main():
	node = Node()
	
	functions = [node.send_DV_to_neighbors]
	threads = []
	for f in functions:
		new_thread = threading.Thread(target = f)
		threads.append(new_thread)
		new_thread.start()

	for t in threads:
		t.join()


if __name__ == '__main__':
	main()