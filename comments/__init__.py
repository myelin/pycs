import html_cleaner
import cgi
import time
import strptime
import string
import re
import pycs_http_util

STANDARDDATEFORMAT = '%Y-%m-%d %H:%M:%S'

class comment:

	def __init__( self, cid, usernum, postid, name, url, email, date, cmttext ):

		self.cid = cid
		self.usernum = usernum
		self.postid = postid
		
		if name == '':
			self.name = 'an anonymous coward'
		else:
			self.name = name
		self.url = url
		if url in [ '', 'http://' ]:
			self.nameString = '<span class="quietlink">%s</span>' % ( cgi.escape( self.name ), )
		else:
			self.nameString = '<a href="%s" class="quietlink">%s</a>' % ( pycs_http_util.MungeHTML( url ), cgi.escape( self.name ) )
		if email == '':
			self.emailString = ''
		else:
			self.emailString = ' [<a href="mailto:%s" class="quietlink">%s</a>]' % ( email, cgi.escape( email ), )
		if not date:
			self.dateString = ''
		else:
			self.dateString = " at %s" % date #time.strftime( _(' at %I:%M:%S %p on %B %d, %Y'), strptime.strptime( date, STANDARDDATEFORMAT ) )
		
		self.commentFooter = "%s%s" % (
			self.nameString,
			#self.emailString,
			self.dateString,
		)
		
		self.cleanedUpComment = string.replace(
			re.sub(
				r'(http://[^\r\n \"\<]+)',
				r'<a href="\1">\1</a>',
				cgi.escape( cmttext ),
			),
			"\n", "<br />"
		)
		
		self.cleanedUpComment = html_cleaner.cleanHtml( cmttext )
