#!/usr/bin/env python

# (C) 2003 Phillip Pearson
# MIT license (like the rest of PyCS)

import os.path

outputpath = os.path.expanduser('~/pycs/var/lib/pycs/www/allyourrss.html')

if __name__ == '__main__':
    recent = eval(open('cache/recent').read())
    print len(recent)

    recent.reverse()
    f = open(outputpath, 'w')
    f.write('<html><body>')
    for item in recent:
        if item.has_key('title'):
            t = item['title']
            if item.has_key('link'):
                t = '<a href="%s">%s</a>' % (item['link'], t)
            f.write('<h3>%s</h3>' % t)
        f.write('<h6>via <a href="%s">%s</a></h6>' % (item['channel_link'], item['channel_title']))
        f.write('<div>%s</div>' % item['description'])
        f.write('<hr>')
    f.write('</body></html>')
    f.close()
