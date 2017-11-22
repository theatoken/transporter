# coding=utf8
import bottle
from bottle import route, response, request
import json
import base64
import requests
import logging



@route('/delegate/<path>')
def index(path):
    uri, content_type = json.loads(base64.urlsafe_b64decode(path))

    #parsed_uri = urlparse(uri)
    #domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    logging.error('get url:%s  content-type:%s', uri, content_type)
    r = requests.get(uri) if request.method.lower() == 'get' else requests.post(uri, data=request.body)
    r.raise_for_status()

    response.content_type = content_type
    logging.error(r.content)
    return r.content

app = bottle.default_app()

