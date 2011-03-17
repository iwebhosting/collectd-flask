#!/usr/bin/python
from flask import Flask, render_template, request
from json import loads
from httplib2 import Http
import sys
import fnmatch

COLLECTD_WEB_URL = 'http://example.com/cgi-bin'
COLLECTD_WEB_PREFIX = 'http://example.com'

app = Flask(__name__)
app.debug = True
app.config.from_object(__name__)
app.config.from_envvar('CF_SETTINGS', silent=True)

h = Http()

cache = {}

def json_request(action, **parameters):
    key = repr((action, parameters))
    if cache.has_key(key):
        return cache[key]
    uri = ['%s/cgi-bin/collection.modified.cgi?action=%s' % (app.config['COLLECTD_WEB_URL'], action)]
    uri = uri + ['%s=%s' % (k, v) for k, v in parameters.items()]
    res, body = h.request(';'.join(uri))
    decoded_object = loads(body)
    cache[key] = decoded_object
    if app.debug:
        print >>sys.stderr, key
    return decoded_object

def get_hosts(pattern=None):
    #TODO dont curl for this, walk the filesystemi
    if pattern:
        return [h for h in json_request('hostlist_json') if fnmatch.fnmatch(h, pattern)]
    return json_request('hostlist_json')

def get_plugins_for_host(hostname, pluginpattern=None):
    #TODO dont curl for this, walk the filesystem
    if pluginpattern:
        return [p for p in json_request('pluginlist_json', host=hostname) if fnmatch.fnmatch(p, pluginpattern)]
    return json_request('pluginlist_json', host=hostname)

def graph(hosts, plugins, period='month'):
    graphs = {}
    for host in hosts:
        graphs[host] = {}
        for plugin in plugins[host]:
            graphs[host][plugin] = [app.config['COLLECTD_WEB_PREFIX'] + x for x in json_request('graphs_json', host=host, plugin=plugin)[period]]
    return render_template('graph.html', hosts=hosts, plugins=plugins, graphs=graphs, period=period)

@app.route('/')
def index():
    period = request.args.get('period', 'month')
    hosts = get_hosts()
    plugins = {}
    for host in hosts:
        plugins[host] = get_plugins_for_host(host)
    return render_template('index.html', hosts=hosts, plugins=plugins, period=period)

@app.route('/<hostpattern>/')
def graph_by_host(hostpattern):
    hosts = get_hosts(hostpattern)
    plugins = {}
    for h in hosts:
        plugins[h] = get_plugins_for_host(h)
    return graph(hosts, plugins, request.args.get('period', 'month'))

@app.route('/<hostpattern>/<pluginpattern>/')
def graph_by_host_with_plugin(hostpattern, pluginpattern):
    hosts = get_hosts(hostpattern)
    plugins = {}
    for h in hosts:
        plugins[h] = get_plugins_for_host(h, pluginpattern)
    return graph(hosts, plugins, request.args.get('period', 'month'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')
