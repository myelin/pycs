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
elif format == 'mt':
	import comments.export_mt
	
	formatter = comments.export_mt.formatter(set)
	fullfeed = 3
	
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

if not query.has_key('u'):
	usernum = None
else:
	usernum = formatter.u = int(query['u']) #str(int(query['u']))
postid = query.get("p", None)

if query.has_key('c'):

	# We are being called to supply the number of comments; have to
	# generate JavaScript to do this.  Don't display any forms etc.

	c = query['c']
	if c == 'counts':
		rows = [row for row in set.pdb.execute("SELECT postid, COUNT(id) FROM pycs_comments WHERE usernum=%d AND is_spam=0 GROUP BY postid", (usernum,))]
		if rows:
			paragraphs, counts = zip(*rows)
		else:
			paragraphs = counts = []
		
		s = "anID = [%s]; " % ", ".join(['"%s"' % (x,) for x in paragraphs])
		s += "anCount = [%s]; " % ", ".join(['"%d"' % (x,) for x in counts])
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

elif not query.has_key('u'):
	s = """<p>no usernum supplied; the comment link bringing you to this page is broken!</p>"""
elif format == 'html' and not query.has_key('p'):
	s = """<p>no postid supplied - you might be looking for one of the following links:</p>
	<li><a href="comments.py?u=%(usernum)s&format=rss&full=1">recent comments, abbreviated, in rss </a></li>
	<li><a href="comments.py?u=%(usernum)s&format=rss&full=2">recent comments, unabbreviated, in rss</a></li>
	<li><a href="comments.py?u=%(usernum)s&format=rss&full=3">all comments, in full, in rss</a> (don't subscribe to this one - it'll suck a huge amount of bandwidth when you build up a decent number of comments!)</li>
	""" % {'usernum': usernum,
	       }
else:	

	# Displaying comments or accepting a new POSTed one.

	if request.command.lower() == 'post':
	
		# We have a new comment to add
		
		#s += "looks like you're adding a comment:<br>"
		#s += "(data %s)" % (`form`,)
		
		if form.has_key( 'delete' ):
			# it's a DELETE command
			
			if ( ( not set.conf.has_key( 'adminusernum' ) ) or
				( int( loggedInUser.usernum ) != int( set.conf['adminusernum'] ) )
			) and ( usernum != int( loggedInUser.usernum ) ):
				raise "Unauthorised attempt to delete comment"

			cid = int(form['delete'])
			set.pdb.execute("DELETE FROM pycs_comments WHERE usernum=%d AND id=%d", (usernum, cid))
			print "Deleted comment with id %d and usernum %d (logged in user %s)" % (cid, usernum, loggedInUser.usernum)
			formatter.note = _("Comment deleted.")
			
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

			cmttext = form['comment']
			if not cmttext:
				print "Didn't add blank comment"
				formatter.note = _("I can't add a blank comment!  Try again, with a real comment this time.")
			else:
				set.pdb.execute("INSERT INTO pycs_comments (id, usernum, postid, postlink, postername, posteremail, posterurl, commenttext, commentdate, is_spam) VALUES (NEXTVAL('pycs_comments_id_seq'), %s, %s, %s, %s, %s, %s, %s, NOW(), 0)", (usernum, postid, form.get('link', ''), formatter.storedName, formatter.storedEmail, formatter.storedUrl, cmttext, ))
				print "Added comment to usernum %d postid %s by %s, %d bytes" % (usernum, `postid`, `formatter.storedName`, len(cmttext))
				formatter.note = _("New comment added - thanks for participating!")

	if not(fullfeed):
		formatter.p = postid
		#s += "user %s, paragraph %s<br>" % (u, p)

		formatter.xmlFeedLink = "%s%s?u=%s&p=%s&format=rss" % ( set.ServerUrl(), path, formatter.u, formatter.p )

	s = formatter.header()

	# a full feed lists all comments, a paragraph feed only comments to
	# one paragraph
	sql = "SELECT id, postid, postlink, postername, posteremail, posterurl, commentdate, commenttext FROM pycs_comments WHERE is_spam=0 AND usernum=%d"
	sqlargs = [usernum]
	if fullfeed:
		if fullfeed < 3:
			sql += " AND commentdate > (NOW() - INTERVAL '14 days')"
		sql += " ORDER BY commentdate DESC"
	else:
		sql += " AND postid=%s"
		sqlargs.append(formatter.p)

	#print sql, sqlargs
	notes = []
	for cid, postid, clink, pname, pemail, plink, cdate, ctext in set.pdb.execute(sql, tuple(sqlargs)):
		notes.append(comments.comment(cid, usernum, postid, pname, plink, pemail, cdate, ctext))
		if clink: formatter.link = clink
	
	s += formatter.startTable()
	
	# Display comment table			

	if notes:
		for cmtObj in notes:
			# a fullfeed has to pass in the paragraph to the
			# formatter, while a paragraph related feed does
			# not
			if fullfeed:
				s += formatter.comment( cmtObj, paragraph=cmtObj.postid, level=fullfeed )
			else:
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

