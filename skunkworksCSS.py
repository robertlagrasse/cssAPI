# skunkworksCSS is a function library to make interfacing with the
# 8x8 Cloud Storage Service API easy.

# All API calls require a bearer token. Use the clientCredentialsAuthorize()
# function in the skunkworksAuth library to generate a bearer token.

import base64
import json
import requests
from requests_oauth2 import OAuth2BearerToken
import time
import random


################################################################################
    #  This function returns a list of your objects.
    # Reference: https://8x8gateway-8x8apis.apigee.io/docs/css/1/routes/objects/get
    # You can filter on specific object types in the fuction call, or accept default parameters(no filter)
    # ex: getCSS_ObjectsList(token, filter='type==callcenterrecording')

    # You can also sort in ASC or DESC(default) order on the following fields:
    # id
    # bucketId
    # customerId
    # userId
    # type
    # mimeType
    # objectName
    # objectState
    # createdTime (default)
    # udpatedTime
    # storedBytes
    # checksum
    # checksumType

    # The returned values will be sorted by createdTime by default.
    # Responses can be sorted by other fields.
    # ex: getCSS_ObjectsList(token, sortField='type==storedBytes', sortDirection='DESC')

    # Available sort fields -
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

    # By default, the function returns a complete list sorted by creation time.
    # Records are pulled in batches of 100, and added to a list.
    # When all records have been downloaded, the list is returned.
    # If you're expecting massive results, uncomment the sleep delay to rete limit your requests
    # Also think about bringing the response into a file depending upon memory constraints of the system

def getCSS_ObjectsList(accessToken, requestUrl='https://api.8x8.com/storage/us-west/v3/objects', filter='', pageKey=0, limit=100, sortField='createdTime', sortDirection='DESC'):
    complete = False
    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        data = []
        while (pageKey == 0 or not complete):
            s.params = {"Content-Type": "application/json",
                        'Accept': 'application/json',
                        'filter': filter,
                        'pageKey': pageKey,
                        'limit': limit,
                        'sortField': sortField,
                        'sortDirection': sortDirection}
            r = s.get(requestUrl)
            r.raise_for_status()
            pageKey = pageKey + 100
            complete = r.json()['lastPage']
            for item in r.json()["content"]:
                data.append(item)
            print('data size', ':', len(data))
            time.sleep(.1) 
    return data


################################################################################
# This function retrieves the metadata for the specified object id.
# It returns a json object.

def getCSS_ObjectMetaData(accessToken, objectId, requestUrl='https://api.8x8.com/storage/us-west/v3/objects'):
    # json formatted response from API as per documentation:
    # https://8x8gateway-8x8apis.apigee.io/docs/css/1/routes/objects/%7BobjectId%7D/metadata/get
    # Function returns json object with same structure
    metadataUrl = requestUrl + '/' + objectId + '/metadata'
    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        response = s.get(metadataUrl, stream = True)
        response.raise_for_status()
    return response.json()

################################################################################
# This function pulls the content of the object and writes to a binary file
# It returns the size of the file in bytes, or -1 if there was a problem writing.

def getCSS_ObjectContent(accessToken, objectId, filename='data.dat', textMode=False, requestUrl='https://api.8x8.com/storage/us-west/v3/objects', presignUrl=False):
    import os
    contentUrl = requestUrl + '/' + objectId + '/content'
    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        s.params = {"Content-Type": "application/json"}

        writeMode = 'wt'
        if textMode == False:
            writeMode = 'wb'

        outfile = open(filename, writeMode)

        print('Fetching content',end='')
        response = s.get(contentUrl, stream = True)
        for chunk in response.iter_content(chunk_size=1024):
            outfile.write(chunk)
            print('.',end='')
        print('\ndone')
        response.raise_for_status()

        outfile.close()

        try:
            size = os.path.getsize(filename)
        except:
            size = -1
    return size

################################################################################
# This function initiates the bulk download process. It expects a token, and
# a list of object ids. It returns a response object. response.text will contain
# a list of json objects formatted like this:
# [{'zipName': 'cd209587-b204-4934-b879-d1e2920ca2a3.zip', 'status': 'DONE'}, {'zipName': 'c59920c2-dd89-49db-9e09-bf901f81d2bd.zip', 'status': 'DONE'}, {'zipName': 'f9fa7e80-d220-4bc0-83c1-dd4697da4935.zip', 'status': 'NOT_STARTED'}]

def initiateCSS_BulkDownload(accessToken, ids, requestUrl = 'https://api.8x8.com/storage/us-west/v3/bulk/download/start'):
    contentUrl = requestUrl
    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        s.params = {
            "Accept": "application/json",
            "Content-Type": "application/json"
            }
        print('Initiating Request.')
        response = s.post(contentUrl, json=ids)
        response.raise_for_status()
    return response

################################################################################
# This function reports the status of all bulk download requests
# response.text is a list of json objects formatted like this:
# [{'zipName': 'cd209587-b204-4934-b879-d1e2920ca2a3.zip', 'status': 'DONE'}, {'zipName': 'c59920c2-dd89-49db-9e09-bf901f81d2bd.zip', 'status': 'DONE'}, {'zipName': 'f9fa7e80-d220-4bc0-83c1-dd4697da4935.zip', 'status': 'NOT_STARTED'}]

def getCSS_BulkStatus(accessToken, requestUrl = 'https://api.8x8.com/storage/us-west/v3/bulk/download/status'):
    contentUrl = requestUrl
    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        s.params = {
            "Accept": "application/json",
            "Content-Type": "application/json"
            }
        response = s.get(contentUrl)
        response.raise_for_status()
    return response

################################################################################
def getCSS_zipStatus(accessToken, zipName, requestUrl = 'https://api.8x8.com/storage/us-west/v3/bulk/download/status'):
    contentUrl = requestUrl + '/' + zipName

    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        s.params = {
            "Accept": "application/json",
            "Content-Type": "application/json"
            }
        response = s.get(contentUrl)
        response.raise_for_status()
    return response


################################################################################
# This function pulls the content of the zipfile and writes to a binary file
# It returns the size of the file in bytes, or -1 if there was a problem writing.

def getCSS_BulkContent(accessToken, zipName, filename='data.zip', requestUrl='https://api.8x8.com/storage/us-west/v3/bulk/download'):
    import os
    contentUrl = requestUrl + '/' + zipName
    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        s.params = {"Content-Type": "application/json"}

        writeMode = 'wb'
        outfile = open(filename, writeMode)

        print('Fetching content',end='')
        response = s.get(contentUrl, stream = True)
        for chunk in response.iter_content(chunk_size=1024):
            outfile.write(chunk)
            print('.',end='')
        print('\ndone')
        response.raise_for_status()

        outfile.close()

        try:
            size = os.path.getsize(filename)
        except:
            size = -1
    return size

################################################################################

# This function clears bulk download requests from the Server
def clearCSS_BulkRequests(accessToken, requestUrl='https://api.8x8.com/storage/us-west/v3/bulk/download/clear'):
    contentUrl = requestUrl
    with requests.Session() as s:
        s.auth = OAuth2BearerToken(accessToken)
        s.params = {
            "Accept": "application/json",
            }
        response = s.put(contentUrl)
        response.raise_for_status()
    return response

################################################################################
