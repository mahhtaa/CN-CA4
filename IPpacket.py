class IPPacket:
	def __init__(self, saddr, daddr, protocol, data):
		self.previous_hop = None
		self.saddr = saddr
		self.daddr = daddr
		self.protocol = protocol
		self.data = data

	def print_info(self, arrived_link):
		print("\n---Node received packet!---")
		print("\tarrived link\t\t: %s" %arrived_link)
		print("\tsource IP\t\t: %s" %self.saddr)
		print("\tdestination IP\t\t: %s" %self.daddr)
		print("\tprotocol\t\t: %d" %self.protocol)
		print("\tpayload length\t\t: %s" %len(self.data))
		print("\tpayload\t\t\t: %s" %self.data)

