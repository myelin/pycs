# comments.rss

import pycs_settings, cgi

set = pycs_settings.Settings( quiet=True )

headerString = """<?xml version="1.0" encoding="%s"?>
<!-- RSS generation by Python Community Server -->
<rss version="0.92">
""" % set.DocumentEncoding()

footerString = """	</channel>
</rss>
"""

import rss

def esc(s):
	return cgi.escape(s, 1)

class formatter( rss.formatter ):

	def __init__( self, set ):
		self.set = set

	def header( self ):
		try:
			user = self.set.User( self.u )
		except pycs_settings.NoSuchUser:
			user = None
		s = """	<channel>
		<title>%s %s</title>
		<link>%s</link>
		<description>%s</description>
		<copyright>%s %s</copyright>
		<managingEditor>%s</managingEditor>
		<webMaster>%s</webMaster>
""" % (
		user and user.weblogTitle or '',
		_("(comments on weblog)"),
		user and self.set.UserFolder( user.usernum ) or '',
		_("Comments for a weblog, ordered by date (newest first)"),
		_("Copyright"),
		user and user.name or '',
		user and user.email or '',
		user and user.email or '',
	)

		return headerString + s

	def comment( self, cmt, paragraph, level ):
		title = _("Comment by")
		if cmt.cmt.name == '':
			title += _(" an anonymous coward")
		else:
			title += " " + cmt.cmt.name
		link = '%s/system/comments.py?u=%s&amp;p=%s' % ( self.set.ServerUrl(), paragraph.user, paragraph.paragraph )
		title += _(" for post %s") % paragraph.paragraph
		title += cmt.dateString
		desc = cmt.cleanedUpComment
		if level == 1:
			if len(desc) > 40:
				desc = desc[:40] + ' ...'
		src = """		<item>
			<title>%s</title>
			<link>%s</link>
			<description>%s</description>
		</item>
""" % ( esc(title), esc(link), esc(desc) )
		return src

