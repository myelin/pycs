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

import defaultFormatter

class formatter( defaultFormatter.defaultFormatter ):

	def __init__( self, set ):
		self.set = set

	def contentType( self ):
		return 'text/xml'
		
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
		_("(comments on post %s)") % self.p,
		self.set.UserFolder( user.usernum ),
		_("Comments for a weblog post"),
		_("Copyright"),
		user.name,
		user.email,
		user.email,
	)

		return headerString + s

	def footer( self ):
		return footerString

	def comment( self, cmt, paragraph=None, level=0 ):
		title = _("Comment by")
		if cmt.cmt.name == '':
			title += _(" an anonymous coward")
		else:
			title += " " + cmt.cmt.name
		if cmt.cmt.url in [ '', 'http://' ]:
			link = self.set.ServerUrl()
		else:
			link = cmt.cmt.url
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
