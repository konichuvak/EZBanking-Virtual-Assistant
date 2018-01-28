from datetime import datetime
import os
import sys

class Logger:

	def __init__(self):
		self.entries = {}
		script_dir = os.path.dirname(__file__)
		if sys.platform == 'linux':
			rel_path = "log_entries/"
		else:
			rel_path = "log_entries\\"
		self.abs_file_path = os.path.join(script_dir, rel_path)

	def entry_start(self, client):
		filename = 'entry_id{}.txt'.format(client['id'])
		self.entries[client['id']] = open(self.abs_file_path + filename, 'a')
		self.entries[client['id']].write("client: {} ip: {} connected at {}\n".format(client['id'], client['address'][0], str(datetime.now())))

	def entry_append(self, client, message, sender):
		self.entries[client['id']].write(sender + " : " + message + '\n')

	def entry_end(self, client):
		self.entries[client['id']].write("client: {} ip: {} disconnected at {}\n".format(client['id'], client['address'][0], str(datetime.now())))
		self.entries[client['id']].write('\n')
		self.entries[client['id']].close()