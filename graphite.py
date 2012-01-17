import requests
import json

periods = {
    'hour': '-60minutes',
    'day': '-24hours',
    'week': '-7days',
    'month': '-30days',
    'year': '-365days',
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

def draw_graph(graph, host, plugin, hostname, period):
    from_at = periods[period]
    if plugin == 'interface':
        interface_url = 'http://%(hostname)s/render?width=400&from=%(from_at)s&until=now&height=250&fontName=Sans&lineMode=connected&hideLegend=false&target=alias(scale(%(host)s.interface.%(graph)s.if_octets.tx%%2C8)%%2C%%20%%22Transmitted%%20Bits%%2Fs%%22)&target=alias(scale(%(host)s.interface.%(graph)s.if_octets.rx%%2C8)%%2C%%22Received%%20Bits%%2Fs%%22)&title=%(graph)s%%20interface&fontBold=true&bgcolor=FFFFFF&fgcolor=000000' % dict(locals())
        return interface_url
    else:
        return 'http://insom.me.uk/fnf'
