import html_cleaner
import cgi
import time
import strptime
import string
import re
import pycs_http_util

STANDARDDATEFORMAT = '%Y-%m-%d %H:%M:%S'

class comment:

	def __init__( self, cmt, iCmt ):
		
		self.cmt = cmt
		
		# index into the 'notes' subtable for this comment (used when deleting)
		self.iCmt = iCmt
		
		if cmt.name == '':
			self.name = 'an anonymous blog'
		else:
			self.name = cmt.name
		if cmt.url in [ '', 'http://' ]:
			self.nameString = '<span class="quietlink">%s</span>' % ( cgi.escape( self.name ), )
		else:
			self.nameString = '<a href="%s" class="quietlink">%s</a>' % ( pycs_http_util.MungeHTML( cmt.url ), cgi.escape( self.name ) )
		if cmt.title == '':
			self.titleString = 'an untitled blog'
		else:
			self.titleString = cmt.title
		if cmt.date == '':
			self.dateString = ''
		else:
			self.dateString = time.strftime( _(' at %I:%M:%S %p on %B %d, %Y'), strptime.strptime( cmt.date, STANDARDDATEFORMAT ) )
		
		self.commentFooter = "%s%s" % (
			self.nameString,
			#self.titleString,
			self.dateString,
		)
		
		self.cleanedUpComment = string.replace(
			re.sub(
				r'[^"](http://[^\r\n \"\<]+)[^"]',
				r'<a href="\1">\1</a>',
				cgi.escape( cmt.excerpt ),
			),
			"\n", "<br />"
		)
		
		self.cleanedUpComment = html_cleaner.cleanHtml( cmt.excerpt )
