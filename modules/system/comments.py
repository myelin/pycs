#!/usr/bin/python

# Python Community Server
#
#     comments.py: Comment page
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


import re
import default_handler
import metakit
import StringIO
import urllib
import string
import cgi
import binascii
import base64
import time
import strptime
import html_cleaner
import comments
import md5

# order by user & paragraph
commentTable = set.getCommentTable()

[path, params, query, fragment] = request.split_uri()

# see if someone is logged in already
loggedInUser = None
headers = util.IndexHeaders( request )
cookies = util.IndexCookies( headers )
if cookies.has_key( 'userInfo' ):
	import re
	import binascii
	cookieU, cookieP = re.search( '"(.*?)_(.*?)"', cookies['userInfo'] ).groups()
	cookieU = binascii.unhexlify( cookieU )
	try:
		loggedInUser = set.FindUser( cookieU, cookieP )
	except set.PasswordIncorrect:
		pass

# Decode information in query string and form		
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

# check the format spec in the query
format = 'html'
if query.has_key( 'format' ):
	format = query['format']

# check whether a full feed is requested and possible (only with rss and not
# with any command except GET)
fullfeed = 0
if query.has_key('full') and format == 'rss' and not( request.command.lower() in ('put', 'post') ):
	try: fullfeed = int(query['full'])
	except: fullfeed = 1

formatter = None
if format == 'rss':
	if fullfeed:
		import comments.rssfull
		formatter = comments.rssfull.formatter( set )
	else:
		import comments.rss
		formatter = comments.rss.formatter( set )
elif format == 'html':
	import comments.html
	formatter = comments.html.formatter( set, loggedInUser )
	if query.has_key('link'):
		formatter.link = query['link']

request['Content-Type'] = formatter.contentType()

noCookies = 1 # we don't know about the user info
if cookies.has_key( 'commentInfo' ):
	#s += "decoding cookie " + cookies['commentInfo'] + "<br>"
	try:
		# print 'cookies header: ' + cookies['commentInfo']
		formatter.storedEmail, formatter.storedName, formatter.storedUrl = map(
			base64.decodestring,
			string.split( urllib.unquote( cookies['commentInfo'] ), '&' )
		)
		noCookies = 0
	except ValueError:
		# Broken cookie
		print "ValueError"
		pass
	except binascii.Error:
		# some other sort of broken cookie
		print "binascii.Error"
	except:
		# Something else broken? :)
		raise
if noCookies:
	formatter.storedEmail = ""
	formatter.storedName = ""
	formatter.storedUrl = "http://"
	
#s += "Path %s<br>params %s<br>query %s<br>fragment %s<br>" % (path, params, query, fragment)

formatter.u = query['u'] #str(int(query['u']))

if query.has_key('c'):

	# We are being called to supply the number of comments; have to
	# generate JavaScript to do this.  Don't display any forms etc.

	c = query['c']
	if c == 'counts':
		paragraphs = []
		counts = []

		posts = commentTable.select( { 'user': formatter.u } )
		for post in posts:
			paragraphs.append( post.paragraph )
			counts.append( len( post.notes ) )
		
		s = "anID = [" + string.join(
			['"%s"' % (x,) for x in paragraphs]
			, ", " ) + "]; "
		
		s += "anCount = [" + string.join(
			['"%d"' % (x,) for x in counts]
			, ", " ) + "]; "

		s += "nPosts = %d;\n" % (len(counts),)
		s += """				
		function commentCounter( nID ) {
			for ( idx = 0; idx < nPosts; idx ++ ) {
				if ( anID[idx] == nID ) {
					document.write( anCount[idx] );
					return;
				}
			}
			document.write ( "0" );
			return;
		}
		"""
		
	else:
		s = "unknown 'c' value: %s ..." % ( html_munge( c ), )

elif format == 'html' and not query.has_key('p'):
	s = """<p>no postid supplied - you might be looking for one of the following links:</p>
	<li><a href="comments.py?u=%(usernum)s&format=rss&full=1">recent comments, abbreviated, in rss </a></li>
	<li><a href="comments.py?u=%(usernum)s&format=rss&full=2">recent comments, unabbreviated, in rss</a></li>
	<li><a href="comments.py?u=%(usernum)s&format=rss&full=3">all comments, in full, in rss</a> (don't subscribe to this one - it'll suck a huge amount of bandwidth when you build up a decent number of comments!)</li>
	""" % {'usernum': formatter.u,
	}
else:	

	# Displaying comments or accepting a new POSTed one. The list of
	# notes is a direct view (when only notes for one paragraph are
	# requested) or a list of tuples of notes and paragraphs, if a
	# fullfeed is requested. This is a bit hacky but prevents duplicate
	# implementation

	if not(fullfeed):
		formatter.p = query['p']
		#s += "user %s, paragraph %s<br>" % (u, p)

		formatter.xmlFeedLink = "%s%s?u=%s&p=%s&format=rss" % ( set.ServerUrl(), path, formatter.u, formatter.p )

	s = formatter.header()

	# a full feed lists all comments, a paragraph feed only comments to
	# one paragraph
	if fullfeed:
		vw = commentTable.select( { 'user': formatter.u } )
	else:
		vw = commentTable.select( { 'user': formatter.u, 'paragraph': formatter.p } )
	if len(vw) == 0:
		# Never heard of that post or that user, return empty list
		notes = None
		nComments = 0
	else:
		# Got it - grab the 'notes' view or construct a list of
		# (note, paragraph) tuples
		#print "(existing post)"
		if fullfeed:
			notes = []
			nComments = 0
			for p in vw:
				for n in p.notes:
					notes.append( (n, p) )
				nComments += len(p.notes)
		else:
			notes = vw[0].notes
			nComments = len(notes)
			if not hasattr(formatter, 'link'):
				formatter.link = vw[0].link
			else:
				if not formatter.link:
					formatter.link = vw[0].link
	
	if request.command.lower() in ('put', 'post'):
	
		# We have a new comment to add
		
		#s += "looks like you're adding a comment:<br>"
		#s += "(data %s)" % (`form`,)
		
		if form.has_key( 'delete' ):
			# it's a DELETE command
			
			u = int( formatter.u )
			if ( ( not set.conf.has_key( 'adminusernum' ) ) or
				( int( loggedInUser.usernum ) != int( set.conf['adminusernum'] ) )
			) and ( u != int( loggedInUser.usernum ) ):
				raise "Unauthorised attempt to delete comment"
				
			delIdx = form['delete']
			formatter.note = _("Comment deleted.") #"delete comment u=%s, p=%s, cmt=%s" % ( formatter.u, formatter.p, delIdx )
			notes.delete( int( delIdx ) )
			set.Commit()
			
		else:
			# it's an ADD command
			formatter.storedEmail = util.MungeHTML( form['email'] )
			formatter.storedName = util.MungeHTML( form['name'] )
			formatter.storedUrl = util.MungeHTML( form['url'] )
			
			rawCookie = '%s&%s&%s' % (
				base64.encodestring( formatter.storedEmail ),
				base64.encodestring( formatter.storedName ),
				base64.encodestring( formatter.storedUrl ),
			)
			
			outCookie = ''
			for c in rawCookie:
				if c not in ( ' ', "\n", "\r" ):
					outCookie += c
			
			request['Set-Cookie'] = 'commentInfo=%s; expires=Fri, 31-Dec-9999 00:00:00 GMT' % (
				urllib.quote( outCookie )
			)
			#s += "set " + request['Set-Cookie'] + "<br>"
			
			newComment = {
				'email': formatter.storedEmail,
				'name': formatter.storedName,
				'url': formatter.storedUrl,
				'comment': form['comment'],
				'date': time.strftime( comments.STANDARDDATEFORMAT ),
				}
			
			nComments += 1
			
			# If we don't have a row in for this user/paragraph, make one
			if notes == None:
				#print "new comment"
				notes = metakit.view()
				
				# Make a row in 'comments' for this paragraph
				commentTable.append( {
					'user': formatter.u,
					'paragraph': formatter.p,
					'link': form.get('link',''),
					'notes': notes,
					} )
				
				# Pull the row out again
				vw = commentTable.select( { 'user': formatter.u, 'paragraph': formatter.p } )
				notes = vw[0].notes
				
				# ... and add this particular comment in
				notes.append( newComment )
				set.Commit()
			else:
				# It's already there - add more comments
				notes.append( newComment )
				set.Commit()
			
			formatter.note = _("New comment added - thanks for participating!")
	
	s += formatter.startTable()
	
	# Display comment table			

	if notes:
		if fullfeed:
			# fullfeeds are sorted by date in reverse (newest
			# note first)
			notes.sort(lambda a,b: -1*cmp(a[0].date,b[0].date))
			if fullfeed < 3:
				now = time.strftime( "%Y-%m-%d %H:%M:%S", time.gmtime( time.time() - 14*24*3600 ) )
				notes = filter( lambda a: a[0].date >= now, notes )

		for iCmt in range( len( notes ) ):
			# a fullfeed has to pass in the paragraph to the
			# formatter, while a paragraph related feed does
			# not
			cmt = notes[iCmt]
			if fullfeed:
				cmtObj = comments.comment( cmt[0], iCmt )
				s += formatter.comment( cmtObj, paragraph=cmt[1], level=fullfeed )
			else:
				cmtObj = comments.comment( cmt, iCmt )
				s += formatter.comment( cmtObj )
	s += formatter.endTable()
	
	s += formatter.footer()

# check for headers for conditional GET
etag = '"%s"' % md5.new(s).hexdigest()
checktag = ''
for header in request.header:
	m = re.match(r'If-None-Match:\s+(.*)$', header)
	if m:
		checktag = m.group(1)

if checktag and checktag == etag:
	# Got an entitytag and no changes, report no changes
	request.error( 304 )
else:
	# Dump it all in the request object and send it off
	request['Content-Length'] = len(s)
	request['ETag'] = etag
	request.push( s )
	request.done()

