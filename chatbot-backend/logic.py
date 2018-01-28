intents = ['balanceCheck', 'fundTransfer', 'viewTransactions', 'payment']

def satisfy_intent(account, intent, receiver=None, amount=None):

	if intent == 'balanceCheck':
		return account['balance']

	elif intent == 'viewTransactions':
		return account['transaction_history']

	elif intent == 'payment':
		pass

	elif intent == 'fundTransfer':
		if not receiver and not amount:
			return ['Whom or where would you like to send money to?']
		if not amount:
			return ['How much would you like to send?']
		return ['Confirm transfer: sending {} to {}'.format(amount, receiver)]
