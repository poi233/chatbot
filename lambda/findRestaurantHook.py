"""
    This sample demonstrates an implementation of the Lex Code Hook Interface
    in order to serve a sample bot which manages orders for flowers.
    Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
    as part of the 'OrderFlowers' template.
    
    For instructions on how to set up and test this bot, as well as additional samples,
    visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
    """
import math
import dateutil.parser
import datetime
import time
import os
import logging
import yelp_util

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

API_KEY= "0rSI-Nmdw8nTVvaQCq6Ufp_VQzBXyMVFdwFjV-L3NNPliJPvAq9740TlOidT8ME1AX9oXlGLcwOiW7ZGQVN1-_8In-UkbfZ7fmJ7YSOVuohJTN4HcfABYLtas3CEXHYx"

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

def getYelpInfo(location, cuisine, date, dining_time, number_of_people):
    year = parse_int(date.split("-")[0])
    month = parse_int(date.split("-")[1])
    day = parse_int(date.split("-")[2])
    hour = parse_int(dining_time.split(":")[0])
    minute = parse_int(dining_time.split(":")[1])
    date_time = int("{:%s}".format(datetime.datetime(year, month, day, hour, minute)))
    yelp_response = yelp_util.search(API_KEY, "restaurant", location, cuisine, date_time)
    content = "We've found the following restaurants for you: "
    for count in range(0, len(yelp_response["businesses"])):
        tmp = "RESATURANT {}: {}, {}, {}\n".format(
                                                   count,
                                                   yelp_response["businesses"][count]['name'],
                                                   yelp_response["businesses"][count]['location']['address1'],
                                                   yelp_response["businesses"][count]['phone'])
        content += tmp
    return content

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


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_find_restaurant(location, cuisine, date, dining_time, number_of_people):
    location_types = ['brooklyn', 'queen', 'manhattan', 'long island']
    cuisine_types = ['chinese', 'japanese', 'hotpot', 'burgers']
    if location is not None and location.lower() not in location_types:
        return build_validation_result(False,
                                       'Location',
                                       'We do not provide service for {}, would you like another location?  '
                                       'We provide service for Brooklyn, Queen, Manhattan and Long Island.'.format(location))
    
    if cuisine is not None and cuisine.lower() not in cuisine_types:
        return build_validation_result(False,
                                       'Cuisine',
                                       'We do not provide service for {}, would you like another type of food?  '
                                       'We provide service for Chinese food, Japanese food, Hotpot and Burgers.'.format(cuisine))
    
    
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand that, what date would you like to eat?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date', 'You can eat today or after.  What day would you like to eat?')

if dining_time is not None:
    if len(dining_time) != 5 or dining_time[2] != ':':
        # Not a valid time; use a prompt defined on the build-time model.
        return build_validation_result(False, 'DiningTime', None)
        
        hour, minute = dining_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

if number_of_people is not None:
    number_of_people = parse_int(number_of_people)
    if math.isnan(number_of_people):
        return build_validation_result(False, 'NumberOfPeople', None)
        if number_of_people < 0 or number_of_people >= 10:
            return build_validation_result(False, "NumberOfPeople", "We provide service for people larger than 0 and less than 10.")

return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def find_restaurants(intent_request):
    """
        Performs dialog management and fulfillment for ordering flowers.
        Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
        in slot validation and re-prompting.
        """
    
    location = get_slots(intent_request)["Location"]
    cuisine = get_slots(intent_request)["Cuisine"]
    date = get_slots(intent_request)["Date"]
    dining_time = get_slots(intent_request)["DiningTime"]
    number_of_people = get_slots(intent_request)["NumberOfPeople"]
    source = intent_request['invocationSource']
    
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)
        
        validation_result = validate_find_restaurant(location, cuisine, date, dining_time, number_of_people)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
    
        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        
    return delegate(output_session_attributes, get_slots(intent_request))

# Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
# In a real bot, this would likely involve a call to a backend service.
return close(intent_request['sessionAttributes'],
             'Fulfilled',
             {'contentType': 'PlainText',
             'content': getYelpInfo(location, cuisine, date, dining_time, number_of_people)})


""" --- Intents --- """


def dispatch(intent_request):
    """
        Called when the user specifies an intent for this bot.
        """
    
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    
    intent_name = intent_request['currentIntent']['name']
    
    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestion':
        return find_restaurants(intent_request)
    
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
    
    return dispatch(event)
