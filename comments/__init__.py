import html_cleaner
import cgi
import time
import strptime
import string
import re
import pycs_http_util

STANDARDDATEFORMAT = '%Y-%m-%d %H:%M:%S'

class comment:

	def __init__( self, cmt ):
		
		self.cmt = cmt
		
		if cmt.name == '':
			self.name = 'an anonymous coward'
		else:
			self.name = cmt.name
		if cmt.url in [ '', 'http://' ]:
			self.nameString = '<span class="quietlink">%s</span>' % ( cgi.escape( self.name ), )
		else:
			self.nameString = '<a href="%s" class="quietlink">%s</a>' % ( pycs_http_util.MungeHTML( cmt.url ), cgi.escape( self.name ) )
		if cmt.email == '':
			self.emailString = ''
		else:
			self.emailString = ' [<a href="mailto:%s" class="quietlink">%s</a>]' % ( cmt.email, cgi.escape( cmt.email ), )
		if cmt.date == '':
			self.dateString = ''
		else:
			self.dateString = time.strftime( ' at %I:%M:%S %p on %B %d, %Y', strptime.strptime( cmt.date, STANDARDDATEFORMAT ) )
		
		self.commentFooter = "%s%s%s" % (
			self.nameString,
			self.emailString,
			self.dateString,
		)
		
		self.cleanedUpComment = string.replace(
			re.sub(
				r'(http://[^\r\n \"\<]+)',
				r'<a href="\1">\1</a>',
				cgi.escape( cmt.comment ),
			),
			"\n", "<br />"
		)
		
		self.cleanedUpComment = html_cleaner.cleanHtml( cmt.comment )
