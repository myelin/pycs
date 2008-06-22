import html_cleaner
import cgi
import time
import strptime
import string
import re
import pycs_http_util

STANDARDDATEFORMAT = '%Y-%m-%d %H:%M:%S'

class comment:

	def __init__( self, tid, usernum, postid, name, url, title, date, excerpt ):

		self.tid = tid
		self.usernum = usernum
		self.postid = postid

		self.tbname = name
		self.tburl = url
		
		if name == '':
			self.name = 'an anonymous blog'
		else:
			self.name = name
		if url in [ '', 'http://' ]:
			self.nameString = '<span class="quietlink">%s</span>' % ( cgi.escape( self.name ), )
		else:
			self.nameString = '<a href="%s" class="quietlink">%s</a>' % ( pycs_http_util.MungeHTML( url ), cgi.escape( self.name ) )
		if title == '':
			self.titleString = 'an untitled blog'
		else:
			self.titleString = title
		if date == '':
			self.dateString = ''
		else:
			self.dateString = date.strftime( _(' at %I:%M:%S %p on %B %d, %Y') )
		
		self.commentFooter = "%s%s" % (
			self.nameString,
			#self.titleString,
			self.dateString,
		)
		
		self.cleanedUpComment = string.replace(
			re.sub(
				r'[^"](http://[^\r\n \"\<]+)[^"]',
				r'<a href="\1">\1</a>',
				cgi.escape( excerpt ),
			),
			"\n", "<br />"
		)
		
		self.cleanedUpComment = html_cleaner.cleanHtml( excerpt )
