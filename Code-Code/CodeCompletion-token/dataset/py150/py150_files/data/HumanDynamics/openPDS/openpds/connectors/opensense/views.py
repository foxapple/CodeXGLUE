#-*- coding: utf-8 -*-
import os
import json
import random

from django.http import HttpResponse, HttpResponseBadRequest

from openpds import settings
from openpds.authorization import PDSAuthorization
from openpds.connectors.opensense import getfunfdata, getmotiondata
from openpds.core.models import Profile
from openpds import getInternalDataStore


def data(request):
    print "\n\n DATA REACHED \n\n"

    '''parse json data and upload them to your PDS'''
    # does not allow get method when uploading json data. currently not parsing jsons correctly
    if request.method == 'GET':
        return HttpResponseBadRequest("GET requests disallowed", content_type = 'text/json')

    # get necessary info from outside request
    device_id = request.POST['device_id']
    # flie_hash = request.POST['file_hash']
    # temp token to insert data
    # 'bearer_token' = 3f4851fd8a
    token = request.POST['bearer_token']
    data = json.loads(request.POST['data'])
    result = {}
    funfresult = {}

    # use token to authorize writing to the PDS
    authorization = PDSAuthorization("ios_write", audit_enabled=True)
    if (not authorization.is_authorized(request)):
        print "authorization not received"
        return HttpResponse("Unauthorized", status=401)

    # Get the relevant internal data store
    datastore_owner, ds_owner_created = Profile.objects.get_or_create(uuid = device_id)
    internalDataStore = getInternalDataStore(datastore_owner, "Living Lab", "Social Health Tracker", token)

    # write to the datastore
    result = extractAndInsertData(data, internalDataStore, token)

    # write to funf data
    funfresult = insertfunf(data, internalDataStore, token)
    blankdata = getfunfdata.insertblankdata()
    try:
        internalDataStore.saveData(blankdata, 'funf')
        blankdata = {'status':'ok', 'entries_inserted':1}
    except Exception as e:
        print "\n\nException from os_connector on pds: %s\n" %e
        blankdata = {'success':False, 'error_message':e.message}

    # let the client know what happened
    print result
    if result.get('status'):
        return HttpResponse(json.dumps(result), content_type='application/json')
    else:
        return HttpResponseBadRequest(json.dumps(result), \
            content_type='application/json')


def extractAndInsertData(data, internalDataStore, token):
    result = {}
    print '\n======================\nextractAndInsertData:'
    print data
    print '\n======================\n'

    try:
        #insert each json object in data list, saveData only takes one input 'data'
        for json_object in data:
            internalDataStore.saveData(json_object, 'opensense')
        result = {'status':'ok', 'entries_inserted':len(data)}
    except Exception as e:
        print "\n\nException from os_connector on pds: %s\n" %e
        result = {'success':False, 'error_message':e.message}
    return result

def insertfunf(data, internalDataStore, token):
    funfresult = {}
    motiondata = []
    print '\n======================\nextractAndInsertData:'
    print data
    print '\n======================\n'

    for object in data:
            if object['probe'] == 'motion':
                motiondata.append(object)

    #pdb.set_trace()
    #calls function with only motion data to calculate activity
    #activitydata is dictionary of all ActivityProbe instances
    activitydata = getmotiondata.ondatareceived(motiondata)


    activityresult = {}
    #insert activitydata
    for object in activitydata:
        #pdb.set_trace()

        try:
            internalDataStore.saveData(object, 'funf')
            activityresult = {'status':'ok', 'entries_inserted': 1}
        except Exception as e:
            print "\n\nException from os_connector on pds: %s\n" %e
            funfresult = {'success':False, 'error_message':e.message}
    for object in data:

            funfdata = getfunfdata.getfunfdata(object)

            try:
                internalDataStore.saveData(funfdata, 'funf')
                funfresult = {'status':'ok', 'entries_inserted':1}
            except Exception as e:
                print "\n\nException from os_connector on pds: %s\n" %e
                funfresult = {'success':False, 'error_message':e.message}
    return funfresult

def register(request):
    ''' register a device using the open-sense library'''
    print "register device called"
    data = request.POST

    if not data.get('device_id'):
        responseData = {'error': 'Missing device_id parameter'}
        return HttpResponseBadRequest(json.dumps(data), content_type='application/json')

    else:
        key = generateKey()
        responseData = {'key': key}
        return HttpResponse(json.dumps(responseData), content_type = 'application/json')


def config(request):
    '''send the config file to open-sense, if it is requested'''
    response = open(os.path.join(settings.STATIC_ROOT, 'img/opensense/config.json')).read()
    return HttpResponse(json.dumps(response), content_type = 'application/json')


def generateKey():
    validCharacters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%'

    sr = random.SystemRandom()
    key = ''

    for i in range(0, 40):
        index = sr.randint(0, 40)
        key += validCharacters[index]

    return key

def test(request):
    print "foobar"
    return "foobar"
