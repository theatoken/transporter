# coding=utf8
import bottle
from bottle import route, response, request
import json
import base64
import requests




@route('/delegate/<path>')
def index(path):
    uri, content_type = json.loads(base64.urlsafe_b64decode(path))

    #parsed_uri = urlparse(uri)
    #domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

    r = requests.get(uri, headers=request.headers)
    r.raise_for_status()

    response.content_type = content_type
    return r.raw

app = bottle.default_app()

