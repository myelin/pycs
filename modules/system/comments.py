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

# order by user & paragraph
comments = set.db.getas(
	'comments[user:S,paragraph:S,notes[name:S,email:S,url:S,comment:S]]'
	).ordered( 2 )

[path, params, query, fragment] = request.split_uri()
s = """
<html>
<head>
<title>Comments</title>
<style type="text/css">
<!--
textarea { width: 100% }
.black { background-color: black }
td { background-color:  lightgrey }
.cmt { background-color: #eeeeee }
-->
</style>
</head>
<body>
"""

# Decode information in query string and form		
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

headers = util.IndexHeaders( request )
cookies = util.IndexCookies( headers )

noCookies = 1

if cookies.has_key( 'commentInfo' ):
	#s += "decoding cookie " + cookies['commentInfo'] + "<br>"
	try:
		# print 'cookies header: ' + cookies['commentInfo']
		storedEmail, storedName, storedUrl = map(
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
	storedEmail = ""
	storedName = ""
	storedUrl = "http://"
	
#s += "Path %s<br>params %s<br>query %s<br>fragment %s<br>" % (path, params, query, fragment)

u = query['u']
if query.has_key('c'):

	# We are being called to supply the number of comments; have to
	# generate JavaScript to do this.  Don't display any forms etc.

	c = query['c']
	if c == 'counts':
		paragraphs = []
		counts = []

		posts = comments.select( { 'user': u } )
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
					return
				}
			}
			document.write ( "0" );
			return
		}
		"""
		
	else:
		s = "unknown 'c' value: %s ..." % ( html_munge( c ), )

else:	

	# Displaying comments or accepting a new POSTed one
	
	p = query['p']
	#s += "user %s, paragraph %s<br>" % (u, p)
	
	vw = comments.select( { 'user': u, 'paragraph': p } )
	if len(vw) == 0:
		# Never heard of that paragraph
		#print "(new para)"
		notes = None
		nComments = 0
	else:
		# Got it - grab the 'notes' view
		#print "(existing para)"
		notes = vw[0].notes
		nComments = len(notes)
	
	if request.command in ('put', 'post'):
	
		# We have a new comment to add
		
		#s += "looks like you're adding a comment:<br>"
		#s += "(data %s)" % (`form`,)
	
		storedEmail = util.MungeHTML( form['email'] )
		storedName = util.MungeHTML( form['name'] )
		storedUrl = util.MungeHTML( form['url'] )
		
		rawCookie = '%s&%s&%s' % (
			base64.encodestring( storedEmail ),
			base64.encodestring( storedName ),
			base64.encodestring( storedUrl ),
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
			'email': storedEmail,
			'name': storedName,
			'url': storedUrl,
			'comment': form['comment'],
			}
		
		nComments += 1
		
		# If we don't have a row in for this user/paragraph, make one
		if notes == None:
			#print "new comment"
			notes = metakit.view()
			
			# Make a row in 'comments' for this paragraph
			comments.append( {
				'user': u,
				'paragraph': p,
				'notes': notes,
				} )
			
			# Pull the row out again
			vw = comments.select( { 'user': u, 'paragraph': p } )
			notes = vw[0].notes
			
			# ... and add this particular comment in
			notes.append( newComment )
			set.Commit()
		else:
			# It's already there - add more comments
			notes.append( newComment )
			set.Commit()
		
	# Start enclosing table (gives black borders)
	s += """
	<table width="100%" cellspacing="1" cellpadding="0">
	<tr><td class="black">
	<table width="100%" cellspacing="1" cellpadding="10">
	"""
	
	# Print all comments
	if nComments == 0:
		s += '<tr><td class="cmt"><strong>No comments yet</strong></td></tr>'
	else:
		#s += '%d comments<br>' % (nComments,)
	
		# Display comment table			
	
		for iCmt in range( len( notes ) ):
			cmt = notes[iCmt]
			#s += 'cmt: %s<br>' % (cmt.comment,)
			s += """
			<tr><td class="cmt">
			%s<br>
			<a href="%s">%s</a> [<a href="mailto:%s">%s</a>]
			</td></tr>
			""" % (
				string.replace(
					cgi.escape( cmt.comment ),
					"\n", "<br />"
				),
				util.MungeHTML( cmt.url ),
				cgi.escape( cmt.name ),
				cmt.email,
				cgi.escape( cmt.email ),
			)
		
	# Print 'add comment' form
	s += """
	<tr><td>
	<form method="post" action="comments.py?u=%s&p=%s">
	<table width="100%%" cellspacing="0" cellpadding="2">
	<tr><td></td><td><strong>Add a new comment:</strong></td></tr>
	<tr><td>Name:</td><td width="99%%"><input type="text" size="50" name="name" value="%s"/></td></tr>
	<tr><td>E-mail:</td><td><input type="text" size="50" name="email" value="%s"/></td></tr>
	<tr><td>Website:</td><td><input type="text" size="50" name="url" value="%s"/></td></tr>
	<tr><td>Comment:</td><td><textarea name="comment" width="100%%"></textarea></tr>
	<tr><td></td><td><input type="submit" value="Save comment" />
		<input type="button" value="Cancel" onclick="javascript:window.close()" /></td>
	</table>
	</form>
	</td></tr>
	""" % (u, p, storedName, storedEmail, storedUrl)
	
	# End enclosing table
	s += """
	</table>
	</td></tr></table>
	"""
	
	s += """
	</body>
	</html>
	"""
	
# Dump it all in the request object and send it off
request['Content-Type'] = 'text/html'
request['Content-Length'] = len(s)
request.push( s )
request.done()
