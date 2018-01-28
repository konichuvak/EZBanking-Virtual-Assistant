from datetime import datetime
import time
import os
from .log_database import LogDatabase
from collections import OrderedDict

from rasa_nlu.model import Metadata, Interpreter
from rasa_nlu.config import RasaNLUConfig

class DBLogger:

	def __init__(self, db_name, table_name, cache_size):
		self.logs = self.LimitedSizeDict(size_limit = cache_size) # dict of DBLog instances
		self.db = LogDatabase(db_name = db_name)
		self.table_name = table_name
		self.db.create_table(table_name = self.table_name)
		#self.interpreter = self.NLUInterpreter(model_name ='current')

	def entry_start(self, client):
		self.logs[client['id']] = self.DBLog(client)

	def entry_append(self, client, message, sender):
		self.logs[client['id']].append(message, sender)
		#if sender is 'client':
		#	intent_ranking = self.get_intent_ranking(message)

	def entry_end(self, client):
		if len(self.logs[client['id']].text) > 0: # if log not empty
			self.db.sql_insert_log(table_name = self.table_name, log_id = self.logs[client['id']].log_id, 
				chat_log = self.logs[client['id']].text, rating = self.logs[client['id']].rating, unix = self.logs[client['id']].timestamp)


	#def get_intent_ranking(self, message):
	#	self.interpreter.parse(message)

	def entry_rate(self, client, rating):
		self.logs[client['id']].rating = int(rating)

	class DBLog:

		def __init__(self, client):
			self.text = ''
			self.timestamp = int(time.time())
			self.rating = -1
			self.log_id = client['id'] # unique id

		def append(self, message, sender):
			self.text += str(sender + ' : ' + message + '\n')


	class LimitedSizeDict(OrderedDict):
		"""Dictionary with limited size. When limit is exceeded, kv-pairs are popped in FIFO order."""

		def __init__(self, *args, **kwds):
			self.size_limit = kwds.pop("size_limit", None)
			OrderedDict.__init__(self, *args, **kwds)
			self._check_size_limit()

		def __setitem__(self, key, value):
			OrderedDict.__setitem__(self, key, value)
			self._check_size_limit()

		def _check_size_limit(self):
			if self.size_limit is not None:
				while len(self) > self.size_limit:
					self.popitem(last=False)
"""
	class NLUInterpreter():
	 #Rasa NLU interpreter used for logging NLU analysis for each log entry.

		def __init__(self, model_name):
			self.model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'nlu', model_name))
			self.interpreter = Interpreter.load(self.model_dir, RasaNLUConfig(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'nlu_model_config.json'))))

		def parse(self, text):
			return self.interpreter.parse(text)"""




