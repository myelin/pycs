#!/usr/bin/python

# Python Community Server
#
#     analyse_logs.py: Log analysis (for referrers & rankings)
#	EXPERIMENTAL - not going properly yet
#
# Copyright (c) 2002, Phillip Pearson <pp@myelin.co.nz>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to 
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of 
# the Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import metakit
import string
import re

"""Log analysis

For referrers & rankings.

"""

LOGFILE = "/var/log/apache/rcs-access.log"
DBFILE = "analysed_logs.db"

db = metakit.storage( DBFILE, 1 )

logdata = db.getas( "hits[date:S,ip:S,page:S,ua:S,ref:S,err:S]" ).ordered( 6 )

f = open( LOGFILE, "rt" )

splitter = re.compile( r'^([\d\.]*?) (.*?) (.*?) \[(.*?)\] \"(.*?)\" (\d*?) (\d*?) \"(.*?)\" \"(.*?)\"$' )
req_splitter = re.compile( r'^(\w*?) (.*?) (.*?)$' )

nPages = 0
nNew = 0

while 1:
	s = f.readline()
	if s == None: break
	if s == '': break
	if s[-1] == "\n": s = s[:-1]

	ip, a, b, date, req, err, clen, ref, ua = splitter.search( s ).groups()
	method, page, proto = req_splitter.search( req ).groups()

	r = logdata.find( date=date, ip=ip, page=page, ua=ua, ref=ref, err=err )
	#print r
	if r == -1:
		#print "adding page",page, ", ref ",ref
		logdata.append( date=date, ip=ip, page=page, ua=ua, ref=ref, err=err )
		nNew += 1
	#else:
	#	print "already got", date, ip, page, ua, ref, err
	nPages += 1

db.commit()

print "%d pages, %d new (%d ignored)" % ( nPages, nNew, nPages - nNew )

print "<html><head></head><body>"

print "<pre>"


def sort_by_hits( list ):
	augmented = map( lambda x: (x[1], x), list.items() )
	augmented.sort()
	return [ x[1] for x in augmented ]

print "user agents:"
for a, ct in sort_by_hits( dat.agents ):
	print "\t%d: %s" % (ct, a)

print "pages:"
for p, ct in sort_by_hits( dat.pages ):
	print "\t%d: %s" % (ct, p)

print "referrers:"
for r, ct in sort_by_hits( dat.refs ):
	print "\t%d: %s" % (ct, r)

print "</pre></body></html>"
