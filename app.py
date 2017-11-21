# coding=utf8
import bottle
from bottle import route, run, response
from urlparse import urlparse
import json
import base64
import requests
import re


def gen_uri(url, content_type):
    param = base64.urlsafe_b64encode(json.dumps([url, content_type]))
    return "http://13.114.161.7:9090/delegate/%s" % param

def go_up_url(domain, base_path, url):
    ct = url.count('../')
    if ct:
        seq = base_path[:0-ct]
        the_file = url.replace("../", '')
        seq.append(the_file)
        return "%s%s" % (domain, "/".join(seq))
    else:
        return "%s/%s" % (domain, url)


def replace_content(domain, parent_path, content, re_str, content_type):
    re_script = re.compile(re_str, re.I)
    for url in re_script.findall(content):
        if url.startswith("<%"):
            continue
        if url.startswith("javascript:"):
            continue
        if url.startswith("{{"):
            continue

        if url.startswith('http:') or url.startswith('https:'):
            content = content.replace(url, gen_uri(url, content_type))
        else:
            if url.startswith("/"):
                new_url = "%s%s" % (domain, url)
                content = content.replace(url, gen_uri(new_url, content_type))
            else:
                new_url = go_up_url(domain, parent_path, url)
                content = content.replace(url, gen_uri(new_url, content_type))

    return content


class html_processor(object):
    def __init__(self, html, domain, base_path):
        self.html = html
        self.domain = domain
        self.parent_path = base_path

    def css_links(self):
        self.html = replace_content(self.domain,
                                    self.parent_path,
                                    self.html,
                                    r'<\s*link\s+href=\"(\S+)\"[^>]*>',
                                    'text/css')

    def script_links(self):
        self.html = replace_content(self.domain,
                                    self.parent_path,
                                    self.html,
                                    r'<\s*script\s+src=\"(\S+)\"[^>]*>',
                                    'text/javascript')
        
    def image_links(self):
        self.html = replace_content(self.domain,
                                    self.parent_path,
                                    self.html,
                                    r'<\s*img\s+src=\"(\S+)\"[^>]*>',
                                    'image/*')

    def a_href_links(self):
        self.html = replace_content(self.domain,
                                    self.parent_path,
                                    self.html,
                                    r'<a href=\"([^\"]+)\"',
                                    'text/html')


    def gen(self):
        self.css_links()
        self.script_links()
        self.image_links()
        self.a_href_links()
        return self.html


class js_processor(object):
    def __init__(self, js, domain, base_path):
        self.js = js
        self.domain = domain
        self.parent_path = base_path

    def gen(self):
        return self.js


class css_processor(object):
    def __init__(self, css, domain, base_path):
        self.css = css
        self.domain = domain
        self.parent_path = base_path

    def css_url(self):
        """
        url()
        :return:
        :rtype:
        """
        self.css = replace_content(self.domain,
                                   self.parent_path,
                                   self.css,
                                   r'url\(([^\)]+)\)',
                                   'image/*')

    def gen(self):
        self.css_url()
        return self.css

class image_processor(object):
    def __init__(self, data):
        self.data = data

    def gen(self):
        return self.data


@route('/delegate/<path>')
def index(path):
    uri, content_type = json.loads(base64.urlsafe_b64decode(path))
    parsed_uri = urlparse(uri)
    domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    path_split_arr = parsed_uri.path.split('/')
    parant_path = []
    if len(path_split_arr) > 1:
        parant_path = path_split_arr[:-1]

    r = requests.get(uri, headers={'referer': domain})
    r.raise_for_status()
    processor = None
    if content_type.startswith('text/html'):
        processor = html_processor(r.text, domain, parant_path)

    if content_type.startswith('text/css'):
        processor = css_processor(r.text, domain, parant_path)

    if content_type.startswith('image/'):
        processor = image_processor(r.raw)

    if content_type.startswith('text/javascript'):
        processor = js_processor(r.text, domain, parant_path)

    response.content_type = content_type
    return processor.gen()

app = bottle.default_app()

