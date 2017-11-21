import os
import sys
import json
import hashlib
import codecs
from collections import OrderedDict
import requests
from requests.exceptions import RequestException, HTTPError
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('tpa')

class FatalError(Exception):
    """
    This class does not send message text to kafka.
    """
    def __init__(self, message):
        super(Exception, self).__init__(message)

def gen_sha1_from_strings(list_of_strings):
    #s = u' '.join(list_of_strings).encode('utf-8').strip()
    s = u' '.join(list_of_strings).encode('utf-8')
    return hashlib.sha1(s).hexdigest()

def gen_sha1_from_file_context(file_path):
    # TODO --- modify to handle huge file w/o consuming much memory
    #with open(file_path, 'rb') as fi:
    with open(file_path, 'r') as fi:
        return hashlib.sha1(''.join(fi.readlines()).encode('utf8')).hexdigest()

def save_text(path, text):
    try:
        with open(path, 'w') as fo:
            fo.write(text)
    except (IOError, OSError) as e:
        message = "Failed to save text. {}".format(str(e))
        logger.error(message)
        raise FatalError(message)

def GET(url, request_id, auth=None, data=None):
    try:
        if auth:
            username= auth['username']
            userpasswd = auth['userpasswd']
    except KeyError as e:
        raise FatalError("Failed on GET. Failed to access key in auth. '{}'".format(str(e)))

    try:
        if auth:
            if data:
                r = requests.get(url, auth=(username, userpasswd), data=data)
            else:
                r = requests.get(url, auth=(username, userpasswd))
        else:
            if data:
                headers = {'Content-type': 'application/json'}
                r = requests.get(url, headers=headers, data=data)
            else:
                r = requests.get(url)
        r.raise_for_status()
        #return json.loads(r.text)
        return json.loads(r.text, object_pairs_hook=OrderedDict)
    except RequestException as e:
        raise FatalError("Failed on GET. '{}', {}".format(url, str(e)))
    except HTTPError as e:
        raise FatalError("Failed on GET. '{}', {}, {}".format(url, str(e), r.content))
    except ValueError as e:
        raise FatalError("Failed to load GET response. '{}', {}".format(url, str(e)))

def POST(url, request_id, headers=None, data=None):
    try:
        if headers and data:
            r = requests.post(url, headers=headers, data=data)
        else:
            r = requests.post(url)
        r.raise_for_status()
        return json.loads(r.text)
    except (RequestException) as e:
        raise FatalError("Failed on POST. '{}', {}".format(url, str(e)))
    except (HTTPError) as e:
        raise FatalError("Failed on POST. '{}', {}, {}".format(url, str(e), r.content))
    except ValueError as e:
        raise FatalError("Failed to load POST response. '{}', {}".format(url, str(e)))

def PUT(url, request_id, auth, data):
    logger.info("PUT url: '{}', creds: '{}, data: '{}'".format(url, auth, data))
    try:
        if auth:
            username= auth['username']
            userpasswd = auth['userpasswd']
    except KeyError as e:
        raise FatalError("Failed on PUT. Failed to access key in auth. '{}'".format(str(e)))

    headers = {'Content-type': 'application/json'}
    body = data.encode('utf-8')
    try:
        if auth:
            r = requests.put(url, auth=(username, userpasswd), headers=headers, data=body)
        else:
            r = requests.put(url, headers=headers, data=body)
        logger.info("PUT response: '{}', text: '{}'".format(r, r.content))
        r.raise_for_status()
        return json.loads(r.text)
    except (RequestException) as e:
        raise FatalError("Failed on PUT. '{}', {}, {}".format(url, str(e), r.content))
    except (HTTPError) as e:
        raise FatalError("Failed on PUT. '{}', {}, {}".format(url, str(e), r.content))
    except ValueError as e:
        raise FatalError("Failed to load PUT response. '{}', {}".format(url, str(e)))


"""
All providers return response via the following response functions.

for 2xx status, log it as INFO, otherwise ERROR.

'kafka' argument is a dictionary, which is passed to TpaLogger constructor.


"""
def response_OK(request_id, message, results, kafka):
    return _create_response(request_id, 200,  message, results, kafka)

def response_ACCEPTED(request_id, message, results, kafka):
    return _create_response(request_id, 202, message, results, kafka)

def response_BAD_REQUEST(request_id, message, kafka):
    return _create_response(request_id, 400, message, None, kafka)

def response_NOT_FOUND(request_id, message, kafka):
    return _create_response(request_id, 404, message,  None, kafka)

def response_INTERNAL_SERVER_ERROR(request_id, message, kafka):
    return _create_response(request_id, 500, message, None, kafka)

def response_NOT_IMPLEMENTED(request_id, message, kafka):
    return _create_response(request_id, 501, message, None, kafka)

def _create_response(request_id, status_code, message, results, kafka):
    d = {'reqid': request_id, 'status_code': status_code, 'message': message, 'results': results}
    try:
        s = json.dumps(d)
        if status_code == 200 or status_code == 202:
            if kafka:
                with TpaLogger(**kafka) as o:
                    o.info(s)
            else:
                with TpaLogger() as o:
                    o.info(s)
        else:
            if kafka:
                with TpaLogger(**kafka) as o:
                    o.error(s)
            else:
                with TpaLogger() as o:
                    o.error(s)
    except ValueError as e:
        logger.error("Failed to dump response {} data for logging. {}".format(status_code, str(e))) 

    return d 

class TpaLogger():
    """
    Need to call close() explicitly when this class is instatiated explicitly.

    Expecting following in kwargs in order to send the message to kafka. Otherwise
    the message is only send to logger.
 
        'broker_server'
        'broker_port'
        'topic'
        'key'
    """
    def __init__(self, **kwargs):
        if kwargs:
            try:
                self.kp = KafkaProducer(bootstrap_servers="{}:{}".format(kwargs['broker_server'], kwargs['broker_port']))
                self.topic = kwargs['topic']
                self.key = kwargs['key']
            except KeyError as e:
                logger.error("TpaLogger failed to access key in kafka param. '{}'".format(str(e)))
                logger.error("TpaLogger will not be using kafka.")
                self.kp = None
                self.topic = None
                self.key = None
        else:
            self.kp = None
            self.topic = None
            self.key = None

    def __enter__(self):
        return self
   
    def __exit__(self, exc_type, exc_value, traceback):
        if self.kp:
            self.kp.close()

    def info(self, message):
        try:
            if self.kp:
                self.kp.send(self.topic, key=self.key, value="{} [I] {}".format(str(datetime.now()), message).encode())
        except KafkaTimeoutError as e:
            logger.error("KafkaTimeoutError occurred. {}".format(str(e)))
        logger.info("{}".format(message))

    def warn(self, message):
        try:
            if self.kp:
                self.kp.send(self.topic, key=self.key, value="{} [W] {}".format(str(datetime.now()), message).encode())
        except KafkaTimeoutError as e:
            logger.error("KafkaTimeoutError occurred. {}".format(str(e)))
        logger.warn("{}".format(message))

    def error(self, message):
        try:
            if self.kp:
                self.kp.send(self.topic, key=self.key, value="{} [E] {}".format(str(datetime.now()), message).encode())
        except KafkaTimeoutError as e:
            logger.error("KafkaTimeoutError occurred. {}".format(str(e)))
        logger.error("{}".format(message))

