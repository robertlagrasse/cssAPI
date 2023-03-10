# The Cloud Storage Service relies on client_credentials authorization
# You need a bearer token from the auth server to make CSS API requests

# The skunkworksCSS library was created to provide a simple set of interfaces
# for the CSS API. It contains a set of functions that manage the API calls,
# and return data to your program or write it to a file.

# These code samples demonstrate each of the functions, and are easy
# blueprints to modify for your own purposes.


import json
import sys
import time
import random

#sys.path.insert(0, '/Users/robert/Documents/python/skunklibs/skunkworksAuth/')
#sys.path.insert(0, '/Users/robert/Documents/python/skunklibs/skunkworksCSS/')

from skunkworksAuth import clientCredentialsAuthorize
from skunkworksCSS import getCSS_ObjectsList
from skunkworksCSS import getCSS_ObjectMetaData
from skunkworksCSS import initiateCSS_BulkDownload
from skunkworksCSS import getCSS_BulkStatus
from skunkworksCSS import getCSS_BulkContent
from skunkworksCSS import clearCSS_BulkRequests
from skunkworksCSS import getCSS_ObjectContent

# add directory containing skunkworks libraries to your path


credentials = 'creds.json'
response = clientCredentialsAuthorize(credentials=credentials)

if 'Error' in response.keys():
    print(json.dumps(response, indent=4, sort_keys=True))
    print('There was an error authenticating')
    exit()

token = response['access_token']
expiration = int(response['issued_at']) + int(response['expires_in'])

################################################################################
# OBJECT LISTS (How to find what you're looking for)
# Reference: https://8x8gateway-8x8apis.apigee.io/docs/css/1/routes/objects/get
#
# Everything stored in CSS in an object of some sort. You can retrieve a list of
# all of your objects using the getCSS_ObjectsList() function.
#
# A list of everything is seldom useful.
# You can filter on the following object types in the fuction call using the filter
# argument:
# calladditionalfields
# callcenterrecording
# chattranscription
# cm-report
# meeting
# meetings_transcriptions
# statehistory
# tcltransactions
# transcription
# voicemail
# waveform

# You can sort ASC or DESC using sortDirection. By default, the function
# sorts on createdTime. You can change that using the sortField parameter.
#
# The function returns a list of json objects. Each of these objects is tagged
# with an id. That id is unique to the object, and what you'll use to
# ask the API to do things with specific objects.

################################################################################
objectList = getCSS_ObjectsList(
    token, filter='type==callcenterrecording', sortDirection='DESC')
print('getCSS_ObjectsList returned', len(objectList), 'items.')
if len(objectList) > 0:
    print('This is the first object:\n', json.dumps(
        objectList[0], indent=4, sort_keys=True))

################################################################################
# METADATA (Information about an object)
################################################################################
# Use the object id to retrieve the metadata for the specified object
# In this example, I'll just use the object id of the first item in our objectList
if len(objectList) > 0:
    metadata = getCSS_ObjectMetaData(token, objectList[0]['id'])
    print('metadata from first object:\n', json.dumps(
        metadata, indent=4, sort_keys=True))

################################################################################
# Downloading object content
# To download an object, use the getCSS_ObjectContent() function.
# By default, the function saves a binary file. If you're downloading
# a text object, you can pass textMode=True to the function.

################################################################################

# Get the id of the first object in the objectList
objectid = objectList[0]['id']

# specify where the file should be saved
filename = 'callcenterrecording.mp3'

# download and save the file. Filesize is returned in bytes.
# filesize will be -1 if there was an error.
filesize = getCSS_ObjectContent(token, objectid, filename)
print('Object file size in bytes:', filesize)

################################################################################
# BULK DOWNLOADS (Multi Stage Process!)
# How bulk downloads work:
# Identify the object id for each object you want, and add it to a list []
# Send a token and the list to the API using initiateCSS_BulkDownload()
# initiateCSS_BulkDownload will return list of json objects formatted like this:
# [{'zipName': 'cd209587-b204-4934-b879-d1e2920ca2a3.zip', 'status': 'DONE'}, {'zipName': 'c59920c2-dd89-49db-9e09-bf901f81d2bd.zip', 'status': 'DONE'}, {'zipName': 'f9fa7e80-d220-4bc0-83c1-dd4697da4935.zip', 'status': 'NOT_STARTED'}]
# each of these is a zipfile and a status.
# It takes time to generate the zip file itself.
# Generate the request
# Wait until status on all files is DONE
# Retrieve each file using getCSS_BulkContent()
# Clean up after yourself
# Downloading the zip file doesn't remove it from the server.
# Pass your token to clearCSS_BulkRequests()
# Wait
# Check Status with getCSS_BulkStatus()

################################################################################

if len(objectList) > 0:
    print('Picking 5 objects at random, and placing them in a list[]')
    ids = []
    for i in range(0, 5):
        pick = random.randint(0, len(objectList)-1)
        ids.append(objectList[pick]['id'])

    print('List contains the following object ids:')
    for id in ids:
        print(id)

    print('\n Initiating bulk download request.\n')
    status = initiateCSS_BulkDownload(token, ids)
    print('API Returned:\n')
    print(json.dumps(status.text, indent=4, sort_keys=True))

print('Waiting for zipfiles...\n')

unfinished = True
while unfinished:
    time.sleep(1)
    unfinished = False
    response = json.loads(getCSS_BulkStatus(token).text)

    for item in response:
        print(item['zipName'], item['status'])
        if item['status'] != "DONE":
            unfinished = True

print('Zip file(s) ready on server. Initiating download.')
for item in response:
    print('Downloading: ' + item['zipName'])
    filesize = getCSS_BulkContent(token, item['zipName'], item['zipName'])
    print('Complete. Filesize: ' + str(filesize))

print('Downloads complete. Clearing bulk requests from server.')
response = clearCSS_BulkRequests(token)
print(response)

print('Finished.')
