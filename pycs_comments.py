#!/usr/bin/python

# Python Community Server
#
#     pycs_comments.py: Comment handler
#	OBSOLETE: don't use this any more; it's the old way of doing things.
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

def split_query( q ):
	d = {}

	if (q == None) or (len( q ) == 0):
		return d
	
	# Skip the first char if it's a '?'
	if q[0] == '?':
		q = q[1:]
	
	# Split it up ('blah=pokwer&foo=blah' -> ['blah=pokwer', 'foo=blah'])
	args = re.split( '\&', q )
	
	#print 'split args:', args
	sep = re.compile( '^(.*?)\=(.*)$' )
	
	for arg in args:
		m = sep.search( arg )
		if m:
			key, val = m.groups()
			d[key] = urllib.unquote_plus( val )
			#print 'key',key,' val',val
	
	# Return whole hash
	return d



def munge_html( txt ):
	return string.replace(
		string.replace(
		string.replace( txt, '"', '_' ),
		'<', '_' ),
		'>', '_' )
	





class collector:

	def __init__ (self, handler, length, request):
		self.handler = handler
		self.request = request
		self.request.collector = self
		self.request.channel.set_terminator (length)
		self.buffer = StringIO.StringIO()

	def collect_incoming_data (self, data):
		self.buffer.write (data)

	def found_terminator (self):
		self.buffer.seek(0)
		self.request.collector = None
		self.request.channel.set_terminator ('\r\n\r\n')
		self.handler.continue_request (
			self.request,
			self.buffer
			)


	

class comment_handler:

	match_regex = re.compile(
		r'^/comments$'
		)

	def __init__( self ):
		print "[comment handler]"
		self.db = metakit.storage( 'conf/comments.dat', 1 )
		
		# order by user & paragraph
		self.comments = self.db.getas(
			'comments[user:S,paragraph:S,notes[name:S,email:S,url:S,comment:S]]'
			).ordered( 2 )
	
	def match( self, request ):
		[path, params, query, fragment] = request.split_uri()
		#print "attempt to match '%s'" % (path,)
		m = self.match_regex.match( path )
		return( m != None )
	
	def handle_request( self, request ):
		if request.command in ('put', 'post'):
			# look for a Content-Length header.
			cl = request.get_header ('content-length')
			length = int(cl)
			if not cl:
				request.error (411)
			else:
				collector (self, length, request)
		else:
			self.continue_request (request, StringIO.StringIO())

	def continue_request( self, request, input_data ):
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
		#print "path",path
		#print "params",params
		#print "query",query
		#print "fragment",fragment
		
		# Decode information in query string and form		
		query = split_query( query )
		form = split_query( input_data.read() )
		
		#s += "Path %s<br>params %s<br>query %s<br>fragment %s<br>" % (path, params, query, fragment)

		u = query['u']
		if query.has_key('c'):
			c = query['c']
			if c == 'counts':
				paragraphs = []
				counts = []

				posts = self.comments.select( { 'user': u } )
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
				request.push( s )
				
			else:
				request.push( "unknown 'c' value: %s ..." % (html_munge( c ),) )
			request.done()
			return
			
		p = query['p']
		#s += "user %s, paragraph %s<br>" % (u, p)

		vw = self.comments.select( { 'user': u, 'paragraph': p } )
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
			#s += "looks like you're adding a comment:<br>"
			#s += "(data %s)" % (`form`,)

			newComment = {
				'email': munge_html( form['email'] ),
				'name': munge_html( form['name'] ),
				'url': munge_html( form['url'] ),
				'comment': munge_html( form['comment'] ),
				}
			
			nComments += 1
			
			# If we don't have a row in for this user/paragraph, make one
			if notes == None:
				#print "new comment"
				notes = metakit.view()
				
				# Make a row in 'comments' for this paragraph
				self.comments.append( {
					'user': u,
					'paragraph': p,
					'notes': notes,
					} )
				
				# Pull the row out again
				vw = self.comments.select( { 'user': u, 'paragraph': p } )
				notes = vw[0].notes
				
				# ... and add this particular comment in
				notes.append( newComment )
				self.db.commit()
			else:
				# It's already there - add more comments
				notes.append( newComment )
				self.db.commit()
			
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

			for cmt in notes:
				#s += 'cmt: %s<br>' % (cmt.comment,)
				s += """
				<tr><td class="cmt">
				%s<br>
				<a href="%s">%s</a> [<a href="mailto:%s">%s</a>]
				</td></tr>
				""" % ( cmt.comment, cmt.url, cmt.name, cmt.email, munge_html( cmt.email ), )
			
		# Print 'add comment' form
		s += """
		<tr><td>
		<form method="post" action="/comments?u=%s&p=%s">
		<table width="100%%" cellspacing="0" cellpadding="2">
		<tr><td></td><td><strong>Add a new comment:</strong></td></tr>
		<tr><td>Name:</td><td width="99%%"><input type="text" size="50" name="name"></td></tr>
		<tr><td>E-mail:</td><td><input type="text" size="50" name="email"></td></tr>
		<tr><td>Website:</td><td><input type="text" size="50" name="url"></td></tr>
		<tr><td>Comment:</td><td><textarea name="comment" width="100%%"></textarea></tr>
		<tr><td></td><td><input type="submit" value="Save comment" />
			<input type="button" value="Cancel" onclick="javascript:window.close()" /></td>
		</table>
		</form>
		</td></tr>
		""" % (u, p)

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
	
	#def continue_request( self, request ):
	#	pass
