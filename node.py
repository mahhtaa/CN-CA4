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
		for line in lines[1:]:
			ip, port, vaddr_self, vaddr_neighbor = line.split()
			self.neighbors[vaddr_neighbor] = vaddr_self
			self.link_layer.add_interface(ip, port, vaddr_self, vaddr_neighbor)

		self.distance_vector = {saddr:{saddr:0} for saddr in list(self.neighbors.values())}
		self.dv_lock = threading.Lock()

	def send_DV_to_neighbors():
		while(True):
			time.sleep(1)
			self.dv_lock.acquire()
			distance_vector = self.distance_vector
			self.dv_lock.release()
			for naddr in self.neighbors:
				packet = IPpacket(self.neighbors[naddr] ,naddr, CONTROL, distance_vector)
				self.link_layer.send(naddr, packet)

	


def main():
	node = Node()
	
	functions = [node.send_DV_to_neighbors]
	threads = []
	for f in functions:
		new_thread = threading.Thread(target = f, args = (node,))
		threads.append(new_thread)
		new_thread.start()

	for t in threads:
		t.join()


if __name__ == '__main__':
	main()