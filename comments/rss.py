# comments.rss

headerString = """<?xml version="1.0"?>
<!-- RSS generation by Python Community Server -->
<rss version="0.92">
"""

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
		<title>%s (comments on post %s)</title>
		<link>%s</link>
		<description>Comments for a weblog post</description>
		<copyright>Copyright %s</copyright>
		<managingEditor>%s</managingEditor>
		<webMaster>%s</webMaster>
""" % (
		user.weblogTitle,
		self.p,
		self.set.UserFolder( user.usernum ),
		user.name,
		user.email,
		user.email,
	)

		return headerString + s

	def footer( self ):
		return footerString

	def comment( self, cmt ):
		title = "Comment by"
		if cmt.cmt.name == '':
			title += " an anonymous coward"
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
