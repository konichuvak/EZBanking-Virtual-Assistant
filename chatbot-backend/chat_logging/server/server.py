import sqlite3
from flask import Flask
import sqlite3
from flask import g
import os
app = Flask(__name__)

DATABASE = '/path/to/database.db'
DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db', 'helpbot_logs.db'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
	sql = "SELECT * FROM domo_helpbot_logs LIMIT 100".format('1513276377-1')
	r = str(query_db(sql))
	return r

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv