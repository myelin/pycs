#!/usr/bin/python

# Python Community Server
#
#     analyse_logs.py: Log analysis (for referrers & rankings)
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

#import metakit
#import string
import re
import time
import sys
import os.path

"""Log analysis

For referrers & rankings.

"""

def removeSessId( s ):
	return re.sub( 'PHPSESSID\=[a-z0-9]*', 'PHPSESSID=(censored)', s )

if __name__ == '__main__':
	if len( sys.argv ) > 1:
		LOGFILE = sys.argv[1]
		rooturl = sys.argv[2]
	else:
		LOGFILE = "/var/log/apache/rcs-access.log"
		rooturl = 'http://www.pycs.net'
	DBFILE = "analysed_logs.db"

	# read in referer log blacklist
	badRefs = [ line.rstrip() for line in open(
		os.path.join( os.path.abspath( os.path.split( sys.argv[0] )[0] ), 'refererBlacklist.txt' )
	).readlines() if line.rstrip ]
	#print "bad refs:",badRefs
	
	#db = metakit.storage( DBFILE, 1 )
	
	#logdata = db.getas( "hits[date:S,ip:S,page:S,ua:S,ref:S,err:S]" ).ordered( 6 )
	
	f = open( LOGFILE, "rt" )
	
	splitter = re.compile( r'^(.*?) (.*?) (.*?) \[(.*?)\] \"(.*?)\" (.*?) (.*?) \"(.*?)\" \"(.*?)\"$' )
	req_splitter = re.compile( r'^(\w*?) (.*?) (.*?)$' )
	
	nPages = 0
	nNew = 0
	
	pages = {}
	
	while 1:
		s = f.readline()
		if s == None: break
		if s == '': break
		if s[-1] == "\n": s = s[:-1]
	
		try:
			ip, a, b, date, req, err, clen, ref, ua = splitter.search( s ).groups()
		except:
			sys.stderr.write( "exception thrown while trying to split a line!\n" )
			sys.stderr.write( "line: " + s + "\n" )
			continue

		gotBad = 0
		for bad in badRefs:
			pos = ref.find( bad )
			if pos != -1 and pos == len( ref ) - len( bad ):
				#sys.stderr.write( "found bad referrer: " + ref + " (" + bad + ")\n" )
				gotBad = 1
				break
		if gotBad:
			continue

		try:		
			method, page, proto = req_splitter.search( req ).groups()
		except:
			#sys.stderr.write( "exception thrown while trying to split a request!\n" )
			#sys.stderr.write( "req: " + req + "\n" )
			#sys.stderr.write( "line: " + s + "\n" )
			continue

		ref = removeSessId( ref )
		page = removeSessId( page )
	
		#if page != '/' and page.find( '/users' ) != 0:
		#	continue
			
		if page.find( '.gif' ) != -1:
			continue
		
		#if ua.find( 'Googlebot' ) == 0:
		#	ref = "(googlebot)"
		#elif ua.find( 'Scooter' ) == 0:
		#	ref = "(scooter)"
		#elif ua.find( 'LinkWalker' ) == 0:
		#	ref = '(linkwalker)'
		#elif ua.find( 'Flickbot' ) == 0:
		#	ref = "(flickbot)"
		#elif ua.find( 'Rumours' ) == 0:
		#	ref = "(rumours-agent)"
		
		if ref == '-':
			ref = "%s; %s" % ( ip, ua )
	
		pageData = pages.setdefault( page, { 'hits': 0, 'refs': {}, 'bytes': 0, } )
		pageData['hits'] += 1
		pageData['bytes'] += ( clen == '-' and [0] or [int( clen )] )[0]
	
		#if ref.find( 'rcs.myelin.cjb.net' ) != -1:
		#	continue
	
		refData = pageData['refs'].setdefault( ref, { 'hits': 0, } )
		refData['hits'] += 1
		#print 'referrer',ref,'hits',refData['hits']
	
		#r = logdata.find( date=date, ip=ip, page=page, ua=ua, ref=ref, err=err )
		#if r == -1:
		#	#print "adding page",page, ", ref ",ref
		#	logdata.append( date=date, ip=ip, page=page, ua=ua, ref=ref, err=err )
		#	nNew += 1
		#else:
		#	print "already got", date, ip, page, ua, ref, err
		#nPages += 1
	
	#db.commit()
	
	#print "%d pages, %d new (%d ignored)" % ( nPages, nNew, nPages - nNew )
	
	print """<html>
<head>
	<title>Referrer rankings!</title>
	<link rel="stylesheet" href="http://www.myelin.co.nz/myelin.css" type="text/css" />
</head>
<body>"""
	
	print "<h1>Hits and referrer rankings as of", time.ctime(), "</h1>"
	
	print "<pre>"
	
	rankedPages = [ ( pages[url]['hits'], pages[url]['refs'], url ) for url in pages.keys() ]
	rankedPages.sort()
	rankedPages.reverse()
	
	for hits, refs, url in rankedPages:
		print '<a href="' + rooturl + url + '">' + url + '</a> -', hits, 'hits', "(%d bytes)" % ( pages[url]['bytes'], )
	
		rankedRefs = [ ( refs[name]['hits'], name ) for name in refs.keys() ]
		rankedRefs.sort()
		rankedRefs.reverse()
	
		for hits, url in rankedRefs:
			s = "\t%d: " % ( hits, )
			if url.find( 'http' ) == 0:
				s += '<a href="' + url + '">' + url + '</a>'
			else:
				s += url
			print s
	
		print
	
	print "</pre></body></html>"
