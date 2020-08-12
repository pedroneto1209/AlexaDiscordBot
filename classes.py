from random import shuffle
import main

class AllGuilds:
	def __init__(self, id: int):
		self.id = id
		self.queues = []

	async def to_put(self, search: str):
		self.queues.append(search)
		#print(f'{self.queues} {self.id} {self}')

	async def to_remove(self):
		self.queues.pop(0)
		#print(f'{self.queues} {self.id} {self}')

	async def to_shuffle(self):
		shuffle(self.queues)
		#print(f'{self.queues} {self.id} {self}')

	async def to_clear(self):
		self.queues.clear()
		#print(f'{self.queues} {self.id} {self}')
