"""
This module provides functionality to interface with Alexa devices linked to an associated Amazon account.
"""

import requests
import json
import os
import sys
import logging
import traceback
import simplejson
 
class OneLineExceptionFormatter(logging.Formatter):
    """ Class that formats multi-line exceptions into a single line

    Source: https://www.loggly.com/ultimate-guide/python-logging-basics/
    """
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)
 
    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result

def getCookie():
    """ Loads a cookie containing the Amazon account information from the filesystem
    
    Note: this method first looks in the working directory of the script for a file
    named .cookie.json. If that file isn't found, an attempt is made to look in /tmp/.cookie.json.
    This cookie should contain information about a user logged into alexa.amazon.com and is required 
    to perform the different Alexa operations defined in this module. 
    A google search can return results on how to retrieve a cookie.
    """
    try:
        cookie = ''
        cookiePath = '.cookie.json'
        
        if not os.path.isfile(cookiePath):
            logging.info("Cookie not found in current directory. Trying /tmp/.cookie.json")
            cookiePath = '/tmp/.cookie.json'
        
        if not os.path.isfile(cookiePath):
            exitMessage = "/tmp/.cookie.json not found. Exiting"
            logging.error(exitMessage)
            exit(exitMessage)

        with open(cookiePath, 'r') as f:
            cookie = f.read()
            
        return json.loads(cookie)
    except:
        logging.error(traceback.format_exc())

def getCsrf():
    """ Extracts the csrf prevention token from the cookie """
    try:
        cookie = getCookie()
        csrf = ''
        
        for section in cookie:
            if section['name'] == 'csrf':
                return {'csrf': section['value']}

        return csrf
    except:
        logging.error(traceback.format_exc())

def normalizeCookie():
    """ This converts the format of a cookie from json format to key=value pairs,
    which is needed for to properly make the requests to the Alexa service
    """
    try:
        cookie = getCookie()
        cookieString = ''

        for section in cookie:
            cookieString += '{}={}; '.format(section['name'], section['value'])
        return cookieString
    except:
        logging.error(traceback.format_exc())

def initializeLogging():
    """ Returns a logger that's been configured with a file and stream handler """
    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler('/var/log/alexaControl.log')
    singleLineFormatter = OneLineExceptionFormatter('%(asctime)s - %(levelname)s - %(message)s')

    #streamHandler.setFormatter(singleLineFormatter)
    fileHandler.setFormatter(singleLineFormatter)

    root = logging.getLogger() 
    root.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
    #root.addHandler(streamHandler)
    root.addHandler(fileHandler)

def constructHeaders():
    """ Constructs the headers dict used in the HTTP requests 
    
    Returns: 
    Dict containing the headers needed for making HTTP requests
    """
    headers = {}
    headers['Accept-Encoding'] = 'gzip, deflate, br'
    headers['Accept-Language'] = 'en-US,en;q=0.9'
    headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    headers['Referer'] = 'https://alexa.amazon.com/spa/index.html'
    headers['Cookie'] = normalizeCookie()
    headers['Content-Type'] = 'application/json; charset=UTF-8'
    headers['Connection'] = 'keep-alive'
    headers['csrf'] = getCsrf()['csrf']
    return headers

devices = []
deviceAttributes = []
headers = constructHeaders()
initializeLogging()

def getDeviceList(args=None):
    """ Retrieves a list of the devices linked to the Amazon account in a readable format: #.) deviceName 
    
    Returns:
    List containing the devices linked to the Amazon account.
    """
    deviceList = []
    if len(devices) == 0:
        retrieveDevices()
        
    for i, device in enumerate(devices):
        deviceList.append("{0}.) {1}".format(i+1, device['accountName']))
    return deviceList

def getDevices(args=None):
    """ Retrieves a dict containing the devices linked to the Amazon account
    
    Returns:
    Dict containing the devices linked to the Amazon account
    """
    if len(devices) == 0:
        retrieveDevices()
    return {'devices': devices}
        
def listDevices(args=None):
    """ Prints a list of the devices linked to the Amazon account in a readable format: #.) deviceName 
    
    Note: this method prints the entries as a 1-based list. The actual device indexes are zero-based.
    """

    if len(devices) == 0:
        retrieveDevices()
        
    for i, device in enumerate(devices):
        print("{0}.) {1}".format(i+1, device['accountName']))

def makeRequest(url, method, data=None):
    """ Sends a speak command to the specified Alexa device
    
    Parameters:
    url (string): Url for the request object
    method (string): HTTP method used to make the request
    data (dict): Associated data for the request. Optional

    Returns: JSON object containing response data
    """

    try:
        response = ''
        
        if method == 'GET':
            response = requests.get(url, headers=constructHeaders())
            
        elif method == 'POST':
            response = requests.post(url, data=data, headers=constructHeaders())
        else:
            pass

        logging.debug("Status code: {}".format(response.status_code))

        try:
            res = response.json()
            return res
        except simplejson.errors.JSONDecodeError:
            logging.debug("Response either doesn't contain JSON or an error occurred during parsing. Returning raw content.")
            return response.content.decode('UTF-8')
    except:
        logging.error(traceback.format_exc())

def testApi(args=None):
    """ Sends a speak command to the specified Alexa device (WIP)
    
    Returns:
    JSON object containing response data from the request
    """
    try:
        response = makeRequest('https://alexa.amazon.com/api/devices-v2/device?cached=false', 'GET')
        return response
    except:
        logging.error(traceback.format_exc())

def retrieveDevices():
    """ Makes a request to retrieve a dict containing the devices linked to the Amazon account
    
    Returns:
    Dict containing the devices linked to the Amazon account
    """

    try:
        global devices
        if len(devices) == 0:
            response = makeRequest('https://alexa.amazon.com/api/devices-v2/device?cached=false', 'GET')
            devices = response['devices']
        return devices
    except:
        logging.error(traceback.format_exc())

def getDeviceAttribute(index, attribute):
    """ Retrieves the specified attribute from Alexa device at the specified index
    
    Parameters:
    index (int): Index of the device. This can be retrieved via the getDevices method
    attribute (string): Name of the attribute to retrieve

    Returns:

    """

    try:
        device = getDevices()[index]
        return device[attribute]
    
    except:
        logging.error(traceback.format_exc())

def constructAlexaCmd(device, type, message=None):
    """ Constructs an Alexa cmd object that can be used in a request to an Alexa device
    
    Parameters:
    device (Dict): Target Alexa device to which a request will be n made
    type (str): Alexa behavior type
    message (string): Message used in a speak command. Optional

    Returns:
    JSON formatted string
    """
    operationPayload = {"deviceType":str(device['deviceType']),
                            "deviceTypeId":str(device['deviceType']),
                            "deviceSerialNumber":str(device['serialNumber']),
                            "locale":"en-US",
                            "customerId":str(device["deviceOwnerCustomerId"])}

    if speak:
        operationPayload['textToSpeak'] = message

    startNode = {"@type":"com.amazon.alexa.behaviors.model.OpaquePayloadOperationNode",
                    "type":type,
                    "operationPayload":operationPayload}
        
    sequenceJson = {"@type":"com.amazon.alexa.behaviors.model.Sequence",
                        "startNode":startNode}
    alexaCmd = json.dumps({"behaviorId":"PREVIEW","sequenceJson":json.dumps(sequenceJson), "status":"ENABLED"})
    logging.debug('Alexa command: {}'.format(alexaCmd))

    return alexaCmd

def getWeather(args):
    """ Sends a command to the specified Alexa device to tell the weather
    
    Parameters:
    args (List): List of args passed from the command line
    args[0] (int): Index of the device. This can be retrieved via the getDevices method

    Returns:
    JSON object containing response data from the request
    """

    try:
        deviceIndex = int(args[0])
        device = getDevices()['devices'][deviceIndex]
        url = "https://alexa.amazon.com/api/behaviors/preview"    
        alexaCmd = constructAlexaCmd(device, "Alexa.Weather.Play")
        return makeRequest(url, 'POST', alexaCmd)

    except:
        logging.error(traceback.format_exc())

def speak(args):    
    """ Sends a speak command to the specified Alexa device
    
    Parameters:
    args (List): List of args passed from the command line
    args[0] (int): Index of the device. This can be retrieved via the getDevices method
    args[1] (string): Message to Alexa device to speak

    Returns:
    JSON object containing response data from the request
    """

    try:
        deviceIndex = int(args[0])
        message = args[1]
        url = "https://alexa.amazon.com/api/behaviors/preview"
        device = getDevices()["devices"][deviceIndex]
        alexaCmd = constructAlexaCmd(device, "Alexa.Speak", message)
        return makeRequest(url, 'POST', alexaCmd)

    except:
        logging.error(traceback.format_exc())

def execute(command, args):
    """ Evaluates and executes a command passed from the command line"""
    exe = eval(command)
    return exe(args) 

def run():
    """ Script entry point """
    try:
        command = sys.argv[1]
        args = sys.argv[2:]
        print(execute(command, args))
    except:
        logging.error(traceback.format_exc())

if __name__ == '__main__':
    run()