# comments.html

import urllib

headerString = """<html>
<head>
<title>Comments</title>
<style type="text/css">
<!--
textarea { width: 100% }
.black { background-color: black; }
td { background-color:  lightgrey; }
.cmt { background-color: #eeeeee; }
.commentfooter { font-size: 0.8em; background-color: white; }
.quietlink { font-weight: bold; color: black; }
-->
</style>
</head>
<body>
	<table width="100%" cellspacing="1" cellpadding="0">
	<tr><td class="black">
	<table width="100%" cellspacing="1" cellpadding="10">
"""

footerString = """
	</table>
	</td></tr></table>
</body>
</html>
"""


class formatter:

	def __init__( self, set ):
		self.set = set

	def contentType( self ):
		return 'text/html'

	def header( self ):
		return headerString

	def footer( self ):
	
		s = """
		<tr><td>
		<form method="post" action="comments.py?u=%s&p=%s">
		<table width="100%%" cellspacing="0" cellpadding="2">
		<tr><td></td><td><strong>Add a new comment:</strong></td></tr>
		<tr><td>Name:</td><td width="99%%"><input type="text" size="50" name="name" value="%s"/></td></tr>
		<tr><td>E-mail:</td><td><input type="text" size="50" name="email" value="%s"/></td></tr>
		<tr><td>Website:</td><td><input type="text" size="50" name="url" value="%s"/></td></tr>
		<tr><td>Comment:</td><td><textarea name="comment" width="100%%" rows="10"></textarea></tr>
		<tr><td></td><td><input type="submit" value="Save comment" />
			<input type="button" value="Cancel" onclick="javascript:window.close()" /></td>
		<tr><td></td><td><strong>Note</strong>: 'http://...' will be converted into links.
		HTML other than &lt;a href&gt;, &lt;b&gt;, &lt;i&gt;, &lt;s&gt; and &lt;tt&gt; will be stripped.</td>
		<tr><td></td><td>Subscribe to an RSS feed of this comment thread:
		<a href="http://127.0.0.1:5335/system/pages/subscriptions?url=%s"><img border="0"
		src="http://www.myelin.co.nz/images/tinyCoffeeCup.jpg" width="10" height="10"></a>
		<a href="%s"><img border="0" src="http://www.myelin.co.nz/images/xml.gif" width="36" height="14"></a>
		</td></tr>
		</table>
		</form>
		</td></tr>
		""" % ( self.u, self.p,
			self.storedName, self.storedEmail, self.storedUrl,
			urllib.quote( self.xmlFeedLink ), self.xmlFeedLink
		)

		return s + footerString

	def comment( self, cmt ):

		return """
		<tr><td class="cmt">
		%s<br>
		<span class="commentfooter">&nbsp;&nbsp;posted by %s&nbsp;&nbsp;</span>
		</td></tr>
		""" % (
			cmt.cleanedUpComment,
			cmt.commentFooter,
		)
