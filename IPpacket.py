class IPPacket:
	def __init__(self, saddr, daddr, protocol, data):
		self.saddr = saddr
		self.daddr = daddr
		self.protocol = protocol
		self.data = data

	def print(self):
		print("saddr:", self.saddr)
		print("daddr:", self.daddr)
		print("protocol:", self.protocol)
		print("data\n-----------------------------")
		print(self.data)

