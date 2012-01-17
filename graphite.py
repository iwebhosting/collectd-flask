import requests
import json

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
