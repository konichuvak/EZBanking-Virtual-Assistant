# WebsocketServer is taken from https://github.com/Pithikos/python-websocket-server with slight modifications to its API

from websocket_server import WebsocketServer
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_core.agent import Agent
import os
import logger

# Ignore CPU instructions warning
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # See https://stackoverflow.com/questions/47068709/your-cpu-supports-instructions-that-this-tensorflow-binary-was-not-compiled-to-u


def run_ws(ws_server):
	"""
	Add request processing functions to a websocket server and make it handle requests unitl an explicit terminate() request.
	This process runs forever!
	
	Parameters
	----------
	ws_server : websocket_server.websocket_server.WebsocketServer

	Returns
	-------
	None

	"""
	try:
		ws_server.set_fn_new_client(new_client) # Listen for client entering chat
		ws_server.set_fn_client_left(client_left) # Listen for client leaving chat
		ws_server.set_fn_message_received(message_received) # Listen for client input (and respond)
		ws_server.run_forever() # Run forever (until client leaves chat)
	except KeyboardInterrupt:
		print("Terminating gracefully...")
		ws_server.terminate()
		print("All processes terminated.")
		sys.exit()


##------------------------------------------------------------------------##
#------------------- Websocket Request Handlers ---------------------------#
##------------------------------------------------------------------------##

def new_client(client, ws_server):
	"""
	Called for every client connecting (after handshake).

	Parameters
	----------
	client : dict
		Some info about client. Ex: {'id': 1, 'handler': <websocket_server.websocket_server.WebSocketHandler object at 0x000001C44ECF0208>, 'address': ('127.0.0.1', 19273)}
	ws_server : websocket_server.websocket_server.WebsocketServer
		Websockets Server object

	Returns
	-------
	None

	"""
	print("New client connected and was given id %d" % client['id'])
	logger.entry_start(client)



def client_left(client, ws_server):
	"""
	Called for every client disconnecting.

	Parameters
	----------
	client : dict
		Some info about client. Ex: {'id': 1, 'handler': <websocket_server.websocket_server.WebSocketHandler object at 0x000001C44ECF0208>, 'address': ('127.0.0.1', 19273)}
	ws_server : websocket_server.websocket_server.WebsocketServer
		Websockets Server object

	Returns
	-------
	None

	"""
	print("Client(%d) disconnected" % client['id'])
	logger.entry_end(client)


def message_received(client, ws_server, message):
	"""
	Called when a client sends a message.

	Parameters
	----------
	client : dict
		Some info about client. Ex: {'id': 1, 'handler': <websocket_server.websocket_server.WebSocketHandler object at 0x000001C44ECF0208>, 'address': ('127.0.0.1', 19273)}
	ws_server : websocket_server.websocket_server.WebsocketServer
		Websockets Server object
	message : str
		Text input from a client

	Returns
	-------
	None

	"""
	response = helpbot.handle_message(text_message=message, sender_id=client['id'])
	ws_server.send_message(client, response[0])
	print("Client(%d) said: %s" % (client['id'], message))
	print("Bot responded: %s" %  (response))
	logger.entry_append(client, message, 'client')
	logger.entry_append(client, response[0], 'helpbot')




def main():
	global helpbot
	script_dir = os.path.dirname(__file__)
	helpbot = Agent.load(path=script_dir + "../models/dialogue", interpreter=RasaNLUInterpreter(script_dir + "../models/nlu/current"))
	global logger
	logger = logger.Logger()
	run_ws(WebsocketServer(port=9001, host='0.0.0.0'))


if __name__=="__main__":
	main()
