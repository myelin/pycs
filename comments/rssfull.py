# comments.rss

headerString = """<?xml version="1.0"?>
<!-- RSS generation by Python Community Server -->
<rss version="0.92">
"""

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
		_("(comments on weblog)"),
		self.set.UserFolder( user.usernum ),
		_("Comments for a weblog, ordered by date (newest first)"),
		_("Copyright"),
		user.name,
		user.email,
		user.email,
	)

		return headerString + s

	def comment( self, cmt, paragraph ):
		title = _("Comment by")
		if cmt.cmt.name == '':
			title += _(" an anonymous coward")
		else:
			title += " " + cmt.cmt.name
		link = '%s/system/comments.py?u=%s&#38;p=%s' % ( self.set.ServerUrl(), paragraph.user, paragraph.paragraph )
		title += _(" for post %s") % paragraph.paragraph
		title += cmt.dateString
		return """		<item>
			<title>%s</title>
			<link>%s</link>
			<description><![CDATA[%s]]></description>
		</item>
""" % (
					title,
					link,
					cmt.cleanedUpComment,
				)
