# AlexaControl
Python script that allows interfacing with an Alexa device from the command line


# Usage
`python alexaControl.py <command> <arg1> <arg2> ...`

Current available commands with associated arguments:

| Command | Args | Description
| --- | --- | --- |
| speak | deviceIndex, message | Sends a speak command to the Alexa device at the specified  index. Indexes can be retrieved via the getDevices command. |
| getWeather | deviceIndex | Sends a command to the specified Alexa device to tell the weather |
| getDevices | None | Retrieves the devices linked to the Amazon account |
| listDevices | None | Prints a list of the devices linked to the Amazon account in a readable format: #.) deviceName |

# Linking Amazon Account
The script works by using a cookie file containing the account information. This can be retrieved by logging into https://amazon.alexa.com and extracting the cookie that gets stored to the browser. The script expects the cookie to be in json format.