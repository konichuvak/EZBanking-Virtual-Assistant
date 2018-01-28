import sqlite3
import os
from datetime import datetime

class LogDatabase:

	def __init__(self, db_name):

		self.db_name = db_name
		db_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'db', '{}.db'.format(db_name)))
		self.connection = sqlite3.connect(db_path, check_same_thread=False)
		self.c = self.connection.cursor()

	def create_table(self, table_name):
		self.c.execute("CREATE TABLE IF NOT EXISTS {}(id TEXT PRIMARY KEY, chat_log TEXT, datestamp TEXT, rating INT, unix INT)".format(table_name))

	def sql_insert_log(self, table_name, log_id, chat_log, rating, unix):
		datestamp = str(datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))
		try:
			sql = """INSERT INTO {} (id, chat_log, datestamp, rating, unix) VALUES ("{}", "{}", "{}", {}, {});""".format(table_name, log_id, chat_log, datestamp, rating, unix)
			self.c.execute(sql)
			self.connection.commit()
		except Exception as e:
			print('EXCEPTION: (sql_insert_log)',str(e), str(sql))
