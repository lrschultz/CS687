# Lambda Function for VIQC Chatbot
# Author: Lisa Schultz
# Date: 12/5/2020
# Reference: Code based on and modified from AWS Order Flowers example Lamdba function in help documentation. https://docs.aws.amazon.com/lex/latest/dg/gs-cli.html

import math
import dateutil.parser
import datetime
import time
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
	return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
	return {
		'sessionAttributes': session_attributes,
		'dialogAction': {
			'type': 'ElicitSlot',
			'intentName': intent_name,
			'slots': slots,
			'slotToElicit': slot_to_elicit,
			'message': message
		}
	}


def close(session_attributes, fulfillment_state, message):
	response = {
		'sessionAttributes': session_attributes,
		'dialogAction': {
			'type': 'Close',
			'fulfillmentState': fulfillment_state,
			'message': message
		}
	}

	return response


def delegate(session_attributes, slots):
	return {
		'sessionAttributes': session_attributes,
		'dialogAction': {
			'type': 'Delegate',
			'slots': slots
		}
	}


""" --- Helper Functions --- """
def parse_int(n):
	try:
		return int(n)
	except ValueError:
		return float('nan')
		
def build_validation_result(is_valid, violated_slot, message_content):
	if message_content is None:
		return {
			"isValid": is_valid,
			"violatedSlot": violated_slot,
		}

	return {
		'isValid': is_valid,
		'violatedSlot': violated_slot,
		'message': {'contentType': 'PlainText', 'content': message_content}
	}


def validate_score(scored_risers, completed_rows, completed_stacks):
	if parse_int(scored_risers) < 0 or parse_int(scored_risers) > 28:
		# Not a valid number of Scored Risers
		return build_validation_result(False, 
										'scored_risers',
										'The number of scored risers you entered, {}, is not valid. ' 
										'Please enter a valid number of Scored Risers between 0 and 27'.format(scored_risers))
	if parse_int(completed_rows) < 0 or parse_int(completed_rows) > 9:
		# Not a valid number Completed Rows
		return build_validation_result(False, 
										'completed_rows',
										'The number of Completed Rows you entered, {}, is not valid. ' 
										'Please enter a valid number of Completed Rows between 0 and 8'.format(completed_rows))
	if parse_int(completed_stacks) < 0 or parse_int(completed_stacks) > 10:
		# Not a valid number of Completed Stacks
		return build_validation_result(False, 
										'completed_stacks',
										'The number of Completed Stacks you entered, {} is not valid. '
										'Please enter a valid number of Completed Stacks between 0 and 8'.format(completed_stacks))
	
	# Return if all data is valid 
	return build_validation_result(True, None, None)										
										


""" --- Functions that control the bot's behavior --- """

def calc_score(intent_request):

	scored_risers = get_slots(intent_request)["scored_risers"]
	completed_rows = get_slots(intent_request)["completed_rows"]
	completed_stacks = get_slots(intent_request)["completed_stacks"]
	score = parse_int(scored_risers) + 3 * parse_int(completed_rows) + 30 * parse_int(completed_stacks)
	source = intent_request['invocationSource']
	
	if source == 'DialogCodeHook':
		# Perform basic validation on the supplied input slots.
		# Use the elicitSlot dialog action to re-prompt for the first violation detected.
		slots = get_slots(intent_request)

		validation_result = validate_score(scored_risers, completed_rows, completed_stacks)
		if not validation_result['isValid']:
			slots[validation_result['violatedSlot']] = None
			return elicit_slot(intent_request['sessionAttributes'],
							   intent_request['currentIntent']['name'],
							   slots,
							   validation_result['violatedSlot'],
							   validation_result['message'])
		
		
		output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
		
		if parse_int(scored_risers) is not None:
			output_session_attributes['score'] = parse_int(scored_risers) + 3 * parse_int(completed_rows) + 30 * parse_int(completed_stacks)
			score = parse_int(scored_risers) + 3 * parse_int(completed_rows) + 30 * parse_int(completed_stacks)

		return delegate(output_session_attributes, get_slots(intent_request))
		
	# Return the final match score to the user.
	return close(intent_request['sessionAttributes'],
				 'Fulfilled',
				 {'contentType': 'PlainText',
				  'content': 'The final score for the match with {} Scored Risers, {} Completed Rows, and {} Completed Stacks is {} points'.format(scored_risers, completed_rows, completed_stacks, score)})



""" --- Intents --- """


def dispatch(intent_request):
	"""
	Called when the user specifies an intent for this bot.
	"""

	logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

	intent_name = intent_request['currentIntent']['name']

	# Dispatch to your bot's intent handlers
	if intent_name == 'Calc_Score':
		return calc_score(intent_request)

	raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
	"""
	Route the incoming request based on intent.
	The JSON body of the request is provided in the event slot.
	"""
	# By default, treat the user request as coming from the America/New_York time zone.
	os.environ['TZ'] = 'America/New_York'
	time.tzset()
	logger.debug('event.bot.name={}'.format(event['bot']['name']))
	print('event')
	print(event)

	return dispatch(event)
