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
    elif plugin == 'df':
        d['title'] = '%s space on %s' % (graph, host)
        d['areaMode'] = 'stacked'
        bits = dict(free='Free', reserved='Reserved', used='Used')
        targets = [ ('''alias(%(host)s.df.%(graph)s.df_complex.%%s.value, "%%s")''' %
            locals()) % (k, v) for k, v in bits.items() ]
        return make_graph_url(hostname, d, targets)
    elif plugin == 'disk':
        d['title'] = '%s IOs on %s' % (graph, host)
        bits = dict(merged='Merged', octets='Octets', ops='Operations', time='Time')
        targets_read = [ ('''alias(%(host)s.disk.%(graph)s.disk_%%s.read, "%%s Read")''' % 
            locals()) % (k, v) for k, v in bits.items() ]
        targets_write = [ ('''alias(%(host)s.disk.%(graph)s.disk_%%s.write, "%%s Write")''' % 
            locals()) % (k, v) for k, v in bits.items() ]
        return make_graph_url(hostname, d, targets_read + targets_write)
    elif plugin == 'load':
        d['title'] = 'Load on %s' % (host)
        bits = [('shortterm', '1 Minute'), ('midterm', '5 Minute'), ('longterm', '15 Minute')]
        targets = [ ('''alias(%(host)s.load.load.%%s, "%%s")''' % 
            locals()) % (k, v) for k, v in bits ]
        return make_graph_url(hostname, d, targets)
    elif plugin == 'memory':
        d['title'] = 'Memory on %s' % (host)
        d['areaMode'] = 'stacked'
        bits = [('used', 'Used'), ('buffered', 'Buffered'), ('cached', 'Cached'), ('free', 'Free')]
        targets = [ ('''alias(%(host)s.memory.memory.%%s.value, "%%s")''' %
            locals()) % (k, v) for k, v in bits ]
        return make_graph_url(hostname, d, targets)
    else:
        return '/404'
