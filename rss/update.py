#!/usr/bin/env python

# (C) 2003 Phillip Pearson
# MIT license (like the rest of PyCS)
# but this depends on the GPL 'rssparser.py' from Mark Pilgrim
# so an app built arount this will be covered by the GPL.

import urllib, sgmllib, rssparser, pprint, os, os.path, re

root = 'http://www.pycs.net/'
system = root + 'system/'

class opener(urllib.FancyURLopener):
    version = "All your RSS are belong to us/0.01"

def get(url):
    return opener().open(url).read()

class parser(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.urls = {}
    def start_a(self, attrs):
        for k,v in attrs:
            if k == 'href':
                url = urllib.basejoin(system, v)
                if not url.startswith(root): break
                if url.startswith(system): break
                url = url[len(root):]
                bits = url.split('/')
                if bits[0] == 'users':
                    url = root + '%s/%s' % (bits[0], bits[1])
                else:
                    url = root + bits[0]
                url += '/'
                self.urls[url] = 1

def munge(url):
    ret = []
    for c in url:
        if c.isalnum():
            ret.append(c)
        else:
            ret.append('_%02x' % ord(c))
    return "".join(ret)
                        
if __name__ == '__main__':
    updates = get(urllib.basejoin(system, 'weblogUpdates.py'))
    p = parser()
    p.feed(updates)
    p.close()
    if not os.path.isdir('cache'):
        os.mkdir('cache')
    recent = []
    max_recent = 10
    if os.path.isfile('cache/recent'):
        recent = eval(open('cache/recent').read())
    for url in p.urls.keys():
        cachePath = 'cache/' + munge(url)
        print url
        print "\t",cachePath
        page = get(url)
        urls = re.findall(r'\<link rel=\"alternate\" type=\"application\/rss\+xml\" title=\"RSS\" href\=\"(.*?)\"', page)
        if len(urls):
            rssUrl = urls[0]
        else:
            rssUrl = url + 'rss.xml'
        print "\t",rssUrl
        modified = None
        olddata = None
        if os.path.isfile(cachePath):
            olddata = eval(open(cachePath).read())
            modified = olddata.get('modified', None)
        data = rssparser.parse(rssUrl, modified=modified)
        print len(data['items'])
        if not len(data['items']):
            continue
        guids = {}
        def getguid(item):
            return item.get('guid',item.get('link', item['description']))
        if olddata:
            print "I know about",len(olddata['items']),"items"
            for item in olddata['items']:
                guid = getguid(item)
                guids[guid] = 1
            print "\tnow I know about",len(guids),"guids"
        chan = data['channel']
        for item in data['items']:
            guid = getguid(item)
            if not guids.has_key(guid):
                print "\t\tnew item:",guid
                item['channel_title'] = chan['title']
                item['channel_link'] = chan['link']
                recent.append(item)
        if data['modified'] and modified != data['modified']:
            open(cachePath, 'w').write(`data`)
    print "Buffer now contains",len(recent),"recent items"
    if len(recent) > max_recent:
        print "chop that to",max_recent
        recent = recent[-max_recent:]
    open('cache/recent', 'w').write(`recent`)
