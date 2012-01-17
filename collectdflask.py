#!/usr/bin/python
from graphite import walker as G
from graphite import draw_graph as GG
from flask import Flask, render_template, request
import sys
import re
from os import listdir
from os.path import isdir, join

GRAPHITE_WEB_HOST = 'example.com:8080'

app = Flask(__name__)
app.debug = True
app.config.from_object(__name__)
app.config.from_envvar('CF_SETTINGS', silent=True)

def get_hosts(pattern=None):
    graphite_hostname = app.config['GRAPHITE_WEB_HOST']
    hosts = [h for h in G(graphite_hostname, '*')]
    hosts.sort()
    if pattern:
        pattern_re = re.compile(pattern)
        return [x for x in hosts if pattern_re.match(x)]
    return hosts

def get_plugins_for_host(hostname, pattern=None):
    graphite_hostname = app.config['GRAPHITE_WEB_HOST']
    plugins = [p.replace('%s.' % hostname, '') for p in G(graphite_hostname, '%s.*' % hostname)]
    if pattern:
        pattern_re = re.compile(pattern)
        return [x for x in plugins if pattern_re.match(x)]
    return plugins

def get_graphs_for_plugin(hostname, plugin, pattern=None):
    graphite_hostname = app.config['GRAPHITE_WEB_HOST']
    plugins = [p.replace('%s.%s.' % (hostname, plugin), '') for p in G(graphite_hostname, '%s.%s.*' % (hostname, plugin))]
    if pattern:
        pattern_re = re.compile(pattern)
        return [x for x in plugins if pattern_re.match(x)]
    return plugins

def graph(hosts, plugins, period='month', pattern=None):
    graphs = {}
    for host in hosts:
        graphs[host] = {}
        for plugin in plugins[host]:
            plugins_for_period = [GG(x) for x in get_graphs_for_plugin(host, plugin)]
            if pattern:
                pattern_re = re.compile(pattern)
                graphs[host][plugin] = [x for x in plugins_for_period if pattern_re.search(x)]
            else:
                graphs[host][plugin] = plugins_for_period
    return render_template('graph.html', hosts=hosts, plugins=plugins, graphs=graphs, period=period, patterna=pattern or '')

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
    graph_pattern = request.args.get('pattern')
    hosts = get_hosts(hostpattern)
    plugins = {}
    for h in hosts:
        plugins[h] = get_plugins_for_host(h)
    return graph(hosts, plugins, request.args.get('period', 'month'), graph_pattern)

@app.route('/<hostpattern>/<pluginpattern>/')
def graph_by_host_with_plugin(hostpattern, pluginpattern):
    graph_pattern = request.args.get('pattern')
    hosts = get_hosts(hostpattern)
    plugins = {}
    for h in hosts:
        plugins[h] = get_plugins_for_host(h, pluginpattern)
    return graph(hosts, plugins, request.args.get('period', 'month'), graph_pattern)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
