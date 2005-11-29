# comments.rss

import pycs_settings

set = pycs_settings.Settings( quiet=True )

headerString = """<?xml version="1.0" encoding="%s"?>
<!-- RSS generation by Python Community Server -->
<rss version="0.92">
""" % set.DocumentEncoding()

footerString = """	</channel>
</rss>
"""

import rss

class formatter( rss.formatter ):

	def __init__( self, set ):
		self.set = set

	def header( self ):
		user = self.set.User( self.u )
		s = """	<channel>
		<title>%s %s</title>
		<link>%s</link>
		<description>%s</description>
		<copyright>%s %s</copyright>
		<managingEditor>%s</managingEditor>
		<webMaster>%s</webMaster>
""" % (
		user.weblogTitle,
		_("(trackbacks on weblog)"),
		self.set.UserFolder( user.usernum ),
		_("Trackbacks for a weblog, ordered by date (newest first)"),
		_("Copyright"),
		user.name,
		user.email,
		user.email,
	)

		return headerString + s

	def comment( self, cmt, level ):
		title = _("Comment by")
		if cmt.tbname == '':
			title += _(" an anonymous blog")
		else:
			title += " " + cmt.name
		link = '%s/system/trackback.py?u=%s&amp;p=%s' % ( self.set.ServerUrl(), cmt.usernum, cmt.postid )
		title += _(" for post %s") % cmt.postid
		title += cmt.dateString
		desc = cmt.cleanedUpComment
		if level == 1:
			if len(desc) > 40:
				desc = desc[:40] + ' ...'
		src = """		<item>
			<title>%s</title>
			<link>%s</link>
			<description><![CDATA[%s]]></description>
		</item>
""" % ( title, link, desc )
		return src

