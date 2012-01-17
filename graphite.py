import requests
import json
import urllib

periods = {
    'hour': '-60minutes',
    'day': '-24hours',
    'week': '-7days',
    'month': '-30days',
    'year': '-365days',
}

basic_graph = {
    'width': 800,
    'from': '-2hours',
    'until': 'now',
    'height': 250,
    'fontName': 'Sans',
    'lineMode': 'connected',
    'hideLegend': 'false',
    'fontBold': 'true',
    'bgcolor': 'FFFFFF',
    'fgcolor': '000000',
}

def walker(hostname, path, deep=False):
    ids = []
    url = 'http://' + hostname + '/metrics/find/?query=%s&format=treejson&contexts=1&path=&node=GraphiteTree'
    def walk(path, deep):
        c = requests.get(url % path).content
        nodes = json.loads(c)
        for node in nodes:
            ids.append(node['id'])
            if node['expandable'] > 0 and deep:
                walk(node['id'] + '.*', deep)
        return ids
    return walk(path, deep)

def make_graph_url(hostname, overrides={}, targets=[]):
    d = basic_graph.copy()
    d.update(overrides)
    args = d.items()
    args = args + [('target', target) for target in targets]
    return 'http://' + hostname + '/render?' + urllib.urlencode(args)

def draw_graph(graph, host, plugin, hostname, period):
    d = {}
    d['from'] = periods[period]
    if plugin == 'interface':
        d['title'] = '%s interface on %s' % (graph, host)
        targets = [
            '''alias(scale(%(host)s.interface.%(graph)s.if_octets.tx, 8), "Transmitted Bits/s")''' % locals(),
            '''alias(scale(%(host)s.interface.%(graph)s.if_octets.rx, 8), "Received Bits/s")''' % locals(),
        ]
        return make_graph_url(hostname, d, targets)
    elif plugin == 'cpu':
        d['title'] = 'CPU%s on %s' % (graph, host)
        d['areaMode'] = 'stacked'
        d['max'] = '100'
        bits = dict(idle='Idle', softirq='Soft IRQ', user='User',
            interrupt='Interrupt', steal='Steal', wait='Wait', nice='Nice',
            system='System')
        targets = [ ('''alias(%(host)s.cpu.%(graph)s.cpu.%%s.value, "%%s")''' %
            locals()) % (k, v) for k, v in bits.items() ]
        return make_graph_url(hostname, d, targets)
    else:
        return '/404'
