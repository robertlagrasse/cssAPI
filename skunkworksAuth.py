################################################################################
# There are a number of different APIs across the 8x8 Universe
# These APIs authenticate and authorize in different ways, and require
# information from a number of sources.
#
# This function library is intended to normalize the authentication process.
# It will provide a standard authentication object, which can then be passed
# to whichever API you'd like to call, using a standard python library.
#
# Building function libraries for each capability provided through our APIs
# rounds out the tool kit necessary to build anything you like,
# using 8x8 services like building blocks.

# ********** This will evolve to provide a skunkworksAuth class/object.
# ********** This object will be the universal authentication solution.
# ********** Instantiate, and send to any skunkworks API with your request

################################################################################
# clientCredentialsAuthorize() requests bearer tokens for use with the following
# API endpoints:
#
# Cloud Storage Service
# Quality Management/Speech Analytics
# Real Time Metrics
# Historical Metrics


# This function returns a json formatted response object.
# The token itself is contained in response.json()["access_token"]
# By default, it will use the https://api.8x8.com/oauth/v2/token endpoint, and
# look for credentials stored in creds.json in the current directory.
# The contents of your credentials file should be formatted like this:
# {"key":"yourkey",
# "secret":"yoursecret"}
#
# *** Generate the key pair in the 8x8 admin console. ***
# *** Store the key pair in a file as formatted above ***
# *** DO NOT PUT CREDENTIALS IN YOUR CODE ***

import base64
import json
import requests
import time
from requests_oauth2 import OAuth2BearerToken

def clientCredentialsAuthorize(credentials='creds.json', authendpoint='https://api.8x8.com/oauth/v2/token'):
    # Credentials for the appliction are stored in a json formatted file
    with open(credentials) as f:
        content = f.read()
    creds = json.loads(content)

    # Application Key and secret are base64 encoded to send to auth server
    # # TODO: Clean this us. The b64 encoding can likely be done on the request object itself.
    key = (creds["key"])
    secret = (creds["secret"])
    message = key+':'+secret
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')

    # Headers built for the request per documentation
    # Reference: https://8x8gateway-8x8apis.apigee.io/getting-started#client-credentials

    authheader = {'Authorization': 'Basic ' + base64_message,
                  'Content-type': 'application/x-www-form-urlencoded'}
    my_data = {'grant_type': 'client_credentials'}

    # Send request to authendpoint.
    response = requests.post(authendpoint, data=my_data, headers=authheader)

    if (response.status_code == 200):
        result = response.json()
        result['issued_at'] = int(time.time())
        return result
    else:
        return response.json()

################################################################################
# vccJWTauthorize() requests bearer tokens for use with the following
# API endpoints:
#
# Virtual Contact Center Chat
# This function returns a json formatted response object.
# The token itself is contained in response.json()["token"]
# By default, it will use the https://api.8x8.com/vcc/chat/v1/authorize
# endpoint, and look for credentials stored in vccchat.creds in the current
# directory. The contents of your credentials file should be formatted
# like this:
# {"username":"vcc_tenantname",
# "ActionRequestToken":"vcc_action_request_token",
# "apigeeAPI":"apigee_API_key"}
#
# The information you'll need to create these files is in two different places.
# "username" is the name of your vcc tenant as listed in
# VCC Configuration Manager > Integrations > API Token > username
# "ActionRequestToken" is found on the same screen.
#
# "apigeeAPI" is named as it is to point you to the right place when you need
# to generate an API key for this application.
# You'll need an account at https://8x8gateway-8x8apis.apigee.io/
# Create an app, and enable Contact Center Chat API
# Once created, it shows up in the apps list. Get the API key, not the secret.
#
# Important note - the API key you can generate for VCC chat in the admin
# console is irritatingly not connected to this service in any way. Using a
# key from this resource will not work.
#
# *** Generate the key pair in the 8x8 admin console. ***
# *** Store the key pair in a file as formatted above ***
# *** DO NOT PUT CREDENTIALS IN YOUR CODE ***

def vccJWTauthorize(credentials='vccchat.creds', authendpoint='https://api.8x8.com/vcc/chat/v1/authorize'):
    with open(credentials) as f:
        content = f.read()
    creds = json.loads(content)

    requestUrl = authendpoint

    apigeeAPI = creds['apigeeAPI']
    ActionRequestToken = creds['ActionRequestToken']
    username = creds['username']

    message = username+':'+ActionRequestToken
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')

    authheader = {'Authorization': 'Basic ' + base64_message,
                  '8x8-apikey': apigeeAPI,
                  'Content-type': 'application/x-www-form-urlencoded'}

    response = requests.post(requestUrl, headers=authheader)

    if (response.status_code == 200):
        result = response.json()
        result['issued_at'] = int(time.time())
        result['expireAt'] = int(time.time()+3500)
        result['apikey'] = apigeeAPI
        result['tenantId'] = username
        return result
    else:
        return response.json()
