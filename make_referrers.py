#!/usr/bin/python

# Python Community Server
#
#     make_referrers.py: Per-user log analysis (for referrers & rankings)
#
#	c.f. analyse_logs.py, which generates sitewide data
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

import re, time, sys, ConfigParser, urlparse, StringIO, os.path

"""Log analysis

For referrers & rankings.

"""

logHeader = '''<html>
	<head>
		<title>Weblog referrer rankings</title>
		<link rel="stylesheet" href="http://www.myelin.co.nz/pycs.css" type="text/css" />
	</head>
	<body>
		<h1><a href="http://www.pycs.net/" class="quietLink">Python Community Server</a></h1>
		<table border="0" align="center"><tr><td>
		<h2>Referrer rankings for <a href="%s">%s</a>:</h2>
		<pre>
'''

def removeSessId( s ):
	return re.sub( 'PHPSESSID\=[a-z0-9]*', 'PHPSESSID=(censored)', s )

if __name__ == '__main__':
	LOGFILE = "/var/log/apache/rcs-access.log"
	rooturl = 'http://www.pycs.net'
	outputroot = '/var/lib/pycs/www/'
	if len( sys.argv ) > 1:
		LOGFILE = sys.argv[1]
		rooturl = sys.argv[2]
		if len( sys.argv ) > 2:
			outputroot = sys.argv[3]

	# read in referer log blacklist
	badRefs = [ line.rstrip() for line in open(
		os.path.join( os.path.abspath( os.path.split( sys.argv[0] )[0] ), 'refererBlacklist.txt' )
	).readlines() if line.rstrip ]
	#print "bad refs:",badRefs
		
	#db = metakit.storage( DBFILE, 1 )
	
	#logdata = db.getas( "hits[date:S,ip:S,page:S,ua:S,ref:S,err:S]" ).ordered( 6 )
	
	config = ConfigParser.ConfigParser()
	config.read( '/etc/pycs/pycs.conf' )
	def readAllOptions( section ):
		return dict( [
			( opt, config.get( section, opt ) )
			for opt in config.options( section )
		] )
	mainOpts = readAllOptions( 'main' )
	defaults = config.defaults()
	for v in mainOpts.keys():
		defaults[v] = mainOpts[v]
	aliases = readAllOptions( 'aliases' )
	for v in mainOpts.keys(): del aliases[v]

	# now 'aliases' contains a list of all usernums which have path aliases.
	# we need to pick out all URLs that start with /users/(usernum) or an
	# alias (from the list we just picked up).
	#
	# make a lookup table for this:
	def pathPart( url ):
		return urlparse.urlsplit(
			urlparse.urljoin( rooturl, url )
		)[2]

	#print pathPart( '/users/0000001' )
	#print pathPart( 'http://www.pycs.net/zia/' )

	#import pprint
	#pprint.pprint( aliases )

	class Blog:
		def __init__( self, usernum, url=None ):
			self.usernum = usernum
			self.url = url or urlparse.urljoin( rooturl, '/users/' + usernum )
			self.path = pathPart( self.url )
			htmlpath = os.path.join( outputroot, 'users/%s' % ( usernum, ) )
			if os.path.isdir( htmlpath ):
				self.log = open(
					os.path.join( htmlpath, 'referrers.html' ),
					'wt' )
				self.log.write( logHeader % ( self.url, self.url ) )
			else:
				self.log = None
		def __del__( self ):
			if self.log:
				self.log.write( '''</pre></td></tr></table>
	</body>
</html>''' )
				self.log.close()
		def __repr__( self ):
			return '<Blog: usernum %s, url %s at %s>' % ( self.usernum, self.url, id( self ) )
		def write( self, str ):
			if self.log:
				self.log.write( str )

	blogs = [ Blog( usernum, url ) for usernum,url in aliases.items() ]
	#pprint.pprint( blogs )

	def TestUrl( url ):
		#print "testurl:",url,type(url)
		path = pathPart( url )
		"Test a URL to see if it belongs to a blog, and return the relevant Blog instance if it does"
		for blog in blogs:
			if (
				( path.find( blog.path ) == 0 )
				or ( path.find( '/users/' + blog.usernum ) == 0 )
			):
				return blog
		m = re.match( r'^/users/(\d+)', path )
		if m:
			blog = Blog( m.group( 1 ) )
			blogs.append( blog )
			return blog
		return None
	
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
	
		pageData = pages.setdefault( page, { 'hits': 0, 'refs': {}, } )
		pageData['hits'] += 1
	
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
		blog = TestUrl( url )

		rankedRefs = [ ( refs[name]['hits'], name ) for name in refs.keys() ]
		rankedRefs.sort()
		rankedRefs.reverse()

		so = sys.stdout
		sys.stdout = StringIO.StringIO()
		try:	
			print '<a href="' + rooturl + url + '">' + url + '</a> -', hits, 'hits'
	
			for hits, url in rankedRefs:
				s = "\t(%d) " % ( hits, )
				if url.find( 'http' ) == 0:
					s += '<a href="' + url + '">' + url + '</a>'
				else:
					s += url
				print s
			print
		finally:
			buf = sys.stdout.getvalue()
			sys.stdout = so
			print buf
			if blog:
				blog.write( buf )
	
	print "</pre></body></html>"
