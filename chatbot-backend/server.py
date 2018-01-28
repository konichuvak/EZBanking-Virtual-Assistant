# imports from environment
from collections import OrderedDict
import os, re, json, requests, argparse, time
from nuance_nlu.nlu import parse_text, parse_voice
from logic import satisfy_intent
# imports from local modules
from websocket_server import WebsocketServer # taken from https://github.com/Pithikos/python-websocket-server with slight modifications to its API

# CONSTANTS
LOGGER_CACHE_SIZE = 100
CLIENTS_CACHE_SIZE = 100
INTENTS_BEFORE_ESCALATE = 1 # escalate after same question (same intent) appears this number of times in the dialogue
HOST = '0.0.0.0' # accept any host
PORT = 10000
EZ_CHATBOT_CLIENT_ACCESS_TOKEN = '7f0f7c36961241fb851870e3c19efdad'
NUANCE_CONFIDENCE_THRESHOLD = 0.5

ACCOUNTS = [{
            'account_num' : '1234 5678 1111 9999',
            'pin' : '1234',
            'balance' : [ 
                        'Chequing Balance: $1111',
                        'Savings Balance: $9999', 
                        'Credit Card Balance: $3333', 
                        ], 
            'transaction_history' : 
                    [
                    '1 January 2018, 9:00  AM | CREDIT CARD PAYMENT XXXX 4444 | USD 10000  ',
                    '2 January 2018, 11:00 AM | ETHEREUM TOKEN SALE           | RUB 999999 ',
                    '3 January 2018, 6:00  PM | LAMBORGINI DEALERSHIP CENTER  | ETH 1'
                    ]
            },
            {
            'account_num': '6789 1234 5678 1111',
            'pin' : '9876',
            'balance' : [
                        'Chequing Balance: $1000', 
                        'Savings Balance: $0', 
                        'Credit Card Balance: $0'
                        ],
            'transaction_history' : [
                    '1 January 2018, 9:00  AM | IOTA TOKEN SALE         | USD 300000 ',
                    '2 January 2018, 11:00 AM | CONCORDIA BOOKSTORE     | Mi  10   ',
                    '3 January 2018, 6:00  PM | AWS YEARLY SUBSCRIPTION | RUB 10000'
                                    ]

            }]

def run_ws(ws_server):
    """
    Add request processing functions to a websocket server and make it handle requests unitl an explicit terminate() request (or SIGINT signal).
    This process runs forever!
    
    Parameters
    ----------
    ws_server : websocket_server.websocket_server.WebsocketServer

    """
    ws_server.set_fn_new_client(new_client) # Listen for client entering chat
    ws_server.set_fn_client_left(client_left) # Listen for client leaving chat
    ws_server.set_fn_message_received(message_received) # Listen for client input (and respond)
    ws_server.run_forever() # Run forever (until client leaves chat)

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

    """
    clients[client['id']] = ClientSession(client['id'])    
    #logger.entry_start(client)
    if debug:
        print("New client connected and was given id {}".format(client['id']))

def client_left(client, ws_server):
    """
    Called for every client disconnecting.

    Parameters
    ----------
    client : dict
        Some info about client. Ex: {'id': 1, 'handler': <websocket_server.websocket_server.WebSocketHandler object at 0x000001C44ECF0208>, 'address': ('127.0.0.1', 19273)}
    ws_server : websocket_server.websocket_server.WebsocketServer
        Websockets Server object

    """
    #logger.entry_end(client)
    if debug:
        print("Client({}) disconnected".format(client['id']))

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

    """
    client_session = clients[client['id']]
    nlu_analysis = None
    response_objects = []
    #json_list = parse_voice(client_session.id)
    #print(json_list)
    if not client_session.valid_acc_num:
        response_objects = ask_acc_num(message, client_session)
    elif not client_session.authorized:
        response_objects = ask_acc_pin(message, client_session)
    else:
        if message == '*mic_on*':
            json_list = parse_voice(client['id'])
            
            for response in json_list:
                try:
                    transcriptions = response['transcriptions']
                    response_objects.append({
                                            'response' : transcriptions[0],
                                            'sender': "Client"
                                            })
                except KeyError:
                    pass
            if len(response_objects) == 0:
                intent = 'NO_MATCH'
                confidence = 0
                response_objects.append({
                                    'response' : 'Can you please say that again',
                                    'sender': "EZ Chatbot"
                                    })
            else:
                for response in json_list:
                    try:
                        if response['result_format'] == 'nlu_interpretation_results':
                            nlu_analysis = response
                            intent = nlu_analysis['nlu_interpretation_results']['payload']['interpretations'][0]['action']['intent']['value']
                            confidence = nlu_analysis['nlu_interpretation_results']['payload']['interpretations'][0]['action']['intent']['confidence']
                            message = nlu_analysis['nlu_interpretation_results']['payload']['interpretations'][0]['literal']
                    except KeyError:
                        pass
            #response_objects = literals['transcriptions']
        else:
            json_list = parse_text(message, client['id'])
            nlu_analysis = json_list[1]
            intent = nlu_analysis['nlu_interpretation_results']['payload']['interpretations'][0]['action']['intent']['value']
            confidence = nlu_analysis['nlu_interpretation_results']['payload']['interpretations'][0]['action']['intent']['confidence']

        if nlu_analysis:
            if intent != client_session.intent['intent']:
                client_session.intent['receiver'] = None
                client_session.intent['amount'] = None
                client_session.intent['intent'] = intent

            if client_session.intent['receiver'] == None:    
                try:
                    client_session.intent['receiver'] = nlu_analysis['nlu_interpretation_results']['payload']['interpretations'][0]['concepts']['Receiver'][0]['literal']
                except KeyError:
                    client_session.intent['receiver'] = None
            
            if client_session.intent['amount'] == None:                    
                try:
                    client_session.intent['amount'] = nlu_analysis['nlu_interpretation_results']['payload']['interpretations'][0]['concepts']['nuance_AMOUNT'][0]['literal']
                except KeyError:
                    client_session.intent['amount'] = None

        if intent == 'NO_MATCH' or intent == 'NO_INTENT' or confidence < NUANCE_CONFIDENCE_THRESHOLD:
            dialogflow_action, dialogflow_response = handle_by_dialogflow(message, client)
            response_objects.append(dialogflow_response)
        else:
            responses_str = satisfy_intent(client_session.account, client_session.intent['intent'], client_session.intent['receiver'], client_session.intent['amount'])
            response_objects.extend([{'response': response, 'sender': "EZ Chatbot"} for response in responses_str])
    payload = prepare_response_payload(response_objects)
    ws_server.send_message(client, payload)
    payload_dict = unpack_payload(payload)

    if debug:
        print("Client({}) said: {}".format(client['id'], message))
        print("Bot responded: {}".format(payload))

def ask_acc_num(account_num, client_session):
    if re.match('\d\d\d\d ?\d\d\d\d ?\d\d\d\d ?\d\d\d\d', account_num):
        for account in ACCOUNTS:
            if account['account_num'] == account_num:
                client_session.valid_acc_num = True
                client_session.account_num = account_num
                return [{
                        'response': "Please enter your access code.",
                        'sender': "EZ Chatbot"
                        }]
        return [{
                'response': "Entered account number doesn't exist. Please try again.",
                'sender': "EZ Chatbot"
                }]
    else:
        return [{
                'response': "This doesn't look like a valid account number. Please try again.",
                'sender': "EZ Chatbot"
                }]

def ask_acc_pin(account_pin, client_session):
    for account in ACCOUNTS:
        if account['account_num'] == client_session.account_num and account['pin'] == account_pin:
            client_session.authorized = True
            client_session.account = account
            return [{
                    'response': "You have been authorized",
                    'sender': "EZ Chatbot"
                    },
                    {'response': "How can I help you today?",
                    'sender': "EZ Chatbot"
                    }]
    return [{
            'response': "The entered PIN is incorrect.",
            'sender': "EZ Chatbot"
            }]


##------------------------------------------------------------------------##
#------------------------------- Misc Helpers -----------------------------#
##------------------------------------------------------------------------##


def prepare_response_payload(response_objs):
    """
    Prepare payload that will be sent to frontend. Packages multiple responses in a row, buttons in a usable format.

    Parameters
    ----------
    response_objs : list
        List of strings representing bot responses.
    Returns
    --------
    str
        Serialized str containing JSON with list of string responses

    """
    text_responses = []
    buttons = []
    for response_obj in response_objs:
        text_responses.append(response_obj)
    json_payload = json.dumps(dict(responses=text_responses, buttons=buttons))
    return json_payload


def unpack_payload(payload):
    """
    Unpack payload returned by prepare_response_payload() to dict.

    Parameters
    ----------
    payload : str
        Serialized str containing a JSON doc

    Returns
    --------
    dict
        JSON doc as dict

    """
    payload_dict = json.loads(payload)
    return payload_dict

def handle_by_dialogflow(message, client):
    """
    Pass user input to DialogFlow agent (only Small Talk agent is used)

    Parameters
    ----------
    client : dict
        Some info about client. Ex: {'id': 1, 'handler': <websocket_server.websocket_server.WebSocketHandler object at 0x000001C44ECF0208>, 'address': ('127.0.0.1', 19273)}
    message : str
        Text input from a client

    Returns
    --------
    tuple of str
        action (kind of like intent) and response returned by the agent

    """
    headers = {
              'Authorization': 'Bearer ' + EZ_CHATBOT_CLIENT_ACCESS_TOKEN,
              'Content-Type' : 'application/json'
              }
    body = {
            'lang' : 'en',
            'sessionId' : client['id'],
            'timezone' : 'America/New_York',
            'query' : message
            }
    r = requests.post('https://api.dialogflow.com/v1/query?v=20150910', data=json.dumps(body), headers=headers)
    response_obj = json.loads(r.content.decode('utf-8'))
    action = response_obj['result']['action']
    response_str = response_obj['result']['fulfillment']['speech']
    response = {
                'response': response_str,
                'sender': "EZ Chatbot"
            }
    return action, response

class ClientSession:
    """ Session variables """
    def __init__(self, client_id):
        self.id = client_id
        self.valid_acc_num = False
        self.authorized = False
        self.account_num = None
        self.account = None
        self.intent = {'intent' : None, 'amount' : None, 'receiver' : None}

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

def parse_args():
    parser = argparse.ArgumentParser(description='Run EZ Chatbot on port 10000')
    parser.add_argument('-d', '--debug', action="store_true", dest="debug",
                       help='send debug messages to stdout (default: no output by default)')
    args = parser.parse_args()
    return args.debug

if __name__=="__main__":

    # global vars
    debug = parse_args()
    clients = LimitedSizeDict(size_limit = CLIENTS_CACHE_SIZE) # dict of Conversations for each client    
    run_ws(WebsocketServer(port=PORT, host=HOST))