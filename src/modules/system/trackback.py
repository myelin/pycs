#!/usr/bin/python

# Python Community Server
#
#     trackback.py: trackback pings and lists
#
# Copyright (c) 2003, Georg Bauer <gb@murphy.bofh.ms>
#
# based on comments.py by:
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
import trackbacks
import md5

def escape_8bit(text):
	return re.sub(r'([^\x00-\x7f])',
		      lambda match: '&#%d;' % ord(match.group(1)), text)

def convertEncoding(text, src_enc, dst_enc):
	# convert string encoding
	if src_enc:
		try:
			text = text.decode(src_enc).encode(dst_enc)
		except UnicodeError:
			text = escape_8bit(text)
	else:
		# unkown encoding
		try:
			text = text.decode('ascii').encode('ascii')
		except UnicodeError:
			try:
				text = text.decode('utf-8').encode(dst_enc)
			except UnicodeError:
				try:
					text = text.decode('iso-8859-1').encode(dst_enc)
				except UnicodeError:
					text = escape_8bit(text)
	return text

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

# check wether a full feed is requested and possible (only with rss and not
# with any command except GET)
fullfeed = 0
if query.has_key('full') and format == 'rss' and not( request.command.lower() in ('put', 'post') ):
	try: fullfeed = int(query['full'])
	except: fullfeed = 1

# we start with listing mode
mode = 'listing'
error = 0
errmsg = ''

formatter = None
if format == 'rss':
	if fullfeed:
		import trackbacks.rssfull
		formatter = trackbacks.rssfull.formatter( set )
	else:
		import trackbacks.rss
		formatter = trackbacks.rss.formatter( set )
elif format == 'html':
	import trackbacks.html
	formatter = trackbacks.html.formatter( set, loggedInUser )

request['Content-Type'] = formatter.contentType()

formatter.u = query['u']
usernum = int(formatter.u)
if query.has_key('c'):

	# We are being called to supply the number of trackbacks; have to
	# generate JavaScript to do this.  Don't display any forms etc.

	c = query['c']
	if c == 'counts':
		rows = [row for row in set.pdb.execute("SELECT postid, COUNT(id) FROM pycs_trackbacks WHERE usernum=%d GROUP BY postid", (usernum,))]
		if rows:
			paragraphs, counts = zip(*rows)
		else:
			paragraphs = counts = []
		
		s = "anTbID = [" + string.join(
			['"%s"' % (x,) for x in paragraphs]
			, ", " ) + "]; "
		
		s += "anTbCount = [" + string.join(
			['"%d"' % (x,) for x in counts]
			, ", " ) + "]; "

		s += "nTbPosts = %d;\n" % (len(counts),)
		s += """				
		function trackbackCounter( nID ) {
			for ( idx = 0; idx < nTbPosts; idx ++ ) {
				if ( anTbID[idx] == nID ) {
					document.write( anTbCount[idx] );
					return;
				}
			}
			document.write ( "0" );
			return;
		}
		"""
		
	else:
		s = "unknown 'c' value: %s ..." % ( cgi.escape( c ), )

else:	

	# Displaying trackbacks or accepting a new POSTed one. The list of
	# notes is a direct view (when only notes for one paragraph are
	# requested) or a list of tuples of notes and paragraphs, if a
	# fullfeed is requested. This is a bit hacky but prevents duplicate
	# implementation

	if not(fullfeed):
		formatter.p = query['p']

		formatter.xmlFeedLink = "%s%s?u=%s&p=%s&format=rss" % ( set.ServerUrl(), path, formatter.u, formatter.p )
		formatter.trackbackLink = "%s%s?u=%s&p=%s" % ( set.ServerUrl(), path, formatter.u, formatter.p )
		formatter.note = _('The trackback URL for this posting is:<br><br><span style="font-size: 10px">%s</span>') % (
			'<a href="%s">%s</a>' % (
				formatter.trackbackLink,
				formatter.trackbackLink
			)
		)

	s = formatter.header()

	# some trackback client (e.g. MovableType) send ping using GET method
	if request.command.lower() in ('put', 'post') or (
		request.command.lower() == 'get' and  query.has_key( 'url' )):
		# We have a new trackback to add
		mode = 'add'
		
		if form.has_key( 'delete' ) and request.command.lower() in ( 'put', 'post' ):
			# it's a DELETE command

			mode = 'delete'
			
			u = int( formatter.u )
			if ( ( not set.conf.has_key( 'adminusernum' ) ) or
				( int( loggedInUser.usernum ) != int( set.conf['adminusernum'] ) )
			) and ( u != int( loggedInUser.usernum ) ):
				raise "Unauthorised attempt to delete trackback"
				
			delIdx = form['delete']
			formatter.note = _("Comment deleted.") #"delete trackback u=%s, p=%s, cmt=%s" % ( formatter.u, formatter.p, delIdx )
			notes.delete( int( delIdx ) )
			set.Commit()
			
		else:
			# it's an ADD command

			srcEncoding = ''
			for header in request.header:
				# search encoding in request header
				m = re.match(r'[Cc]ontent-[Tt]ype:.*charset=(.+)$', header)
				if m:
					srcEncoding = m.group(1).strip()
					break

			dstEncoding = set.DocumentEncoding()

			if request.command.lower() == 'get':
				title = query.get('title', _('an untitled posting'))
				blog_name = query.get('blog_name', _('an anonymous blog'))
				url = query['url']
				excerpt = query.get('excerpt', '')
			else:
				title = form.get('title', _('an untitled posting'))
				blog_name = form.get('blog_name', _('an anonymous blog'))
				url = form['url']
				excerpt = form.get('excerpt', '')
				
			formatter.storedTitle = convertEncoding(
				util.MungeHTML(title), srcEncoding, dstEncoding)
			formatter.storedName = convertEncoding(
				util.MungeHTML(blog_name), srcEncoding, dstEncoding)
			formatter.storedUrl = util.MungeHTML(url)
			
			newTrackback = {
				'title': formatter.storedTitle,
				'name': formatter.storedName,
				'url': formatter.storedUrl,
				'excerpt': convertEncoding(excerpt, srcEncoding, dstEncoding),
				'date': time.strftime( trackbacks.STANDARDDATEFORMAT ),
				}

			nComments += 1
			
			# If we don't have a row in for this user/paragraph, make one
			if notes == None:
				notes = metakit.view()
				
				# Make a row in 'trackbacks' for this paragraph
				trackbackTable.append( {
					'user': formatter.u,
					'paragraph': formatter.p,
					'notes': notes,
					} )
				
				# Pull the row out again
				vw = trackbackTable.select( { 'user': formatter.u, 'paragraph': formatter.p } )
				notes = vw[0].notes
				
				# ... and add this particular trackback in
				notes.append( newTrackback )
				set.Commit()
			else:
				# It's already there - add more trackbacks
				notes.append( newTrackback )
				set.Commit()
			
			formatter.note = _("New trackback added - thanks for participating!")
	
	s += formatter.startTable()
	
	# Display trackback table			

	# a full feed lists all trackbacks, a paragraph feed only trackbacks to
	# one paragraph
	sql = 'SELECT id,postid,tbname,tburl,tbtitle,tbdate,tbexcerpt FROM pycs_trackbacks WHERE usernum=%d'
	args = [usernum]
	if fullfeed:
		if fullfeed < 3:
			# only show last 2 weeks of trackbacks
			sql += " AND (tbdate > CURRENT_TIMESTAMP - INTERVAL '14 DAYS')"
		# fullfeeds are sorted by date in reverse (newest
		# note first)
		sql += " ORDER BY tbdate DESC"
	else:
		sql += " AND postid=%s ORDER BY tbdate"
		args.append(formatter.p)

	for tid,tpostid,tname,turl,ttitle,tdate,texcerpt in set.pdb.execute(sql, tuple(args)):
		# a fullfeed has to pass in the paragraph to the
		# formatter, while a paragraph related feed does
		# not
		cmtObj = trackbacks.comment(tid, usernum, tpostid, tname, turl, ttitle, tdate, texcerpt)
		s += formatter.comment( cmtObj, level=fullfeed )

	s += formatter.endTable()
	
	s += formatter.footer()

	# if we got an add, we just return an XML status (trackbacks are
	# only added by scripts
	if mode == 'add':
		request['Content-Type'] = 'text/xml'
		if error:
			s = '<?xml version="1.0" encoding="iso-8859-1"?>\n'
			s += "<response>\n"
			s += "<error>1</error>\n"
			s += "<message>%s</message>\n" % errmsg
			s += "</response>\n"
		else:
			s = '<?xml version="1.0" encoding="iso-8859-1"?>\n'
			s += "<response>\n"
			s += "<error>0</error>\n"
			s += "</response>\n"
	
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

