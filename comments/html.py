# comments.html

import urllib

headerString = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<title>Comments</title>
<style type="text/css">
<!--
body { font-family: verdana, sans-serif; }
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
"""

startTableString = """
	<table width="100%" cellspacing="1" cellpadding="0">
	<tr><td class="black">
	<table width="100%" cellspacing="1" cellpadding="10">
"""

endTableString = """
	</table>
	</td></tr></table>
"""

footerString = """
</body>
</html>
"""

import defaultFormatter

class formatter( defaultFormatter.defaultFormatter ):

	def __init__( self, set, user ):
		self.set = set
		self.user = user
		self.nComments = 0

	def contentType( self ):
		return 'text/html'

	def header( self ):
		return headerString
		
	def startTable( self ):
		ret = [ startTableString ]
		
		if hasattr( self, 'note' ):
			ret += [
				'<tr><td style="border: solid; border-color: black; border-width: 5px; font-weight: bold;">',
				self.note,
				'</td></tr>'
			]
			
		return ''.join( ret )
		
	
	def endTable( self ):
		ret = []
		
		if self.nComments == 0:
			ret.append( '<tr><td class="cmt"><strong>No comments yet</strong></td></tr>' )

		ret.append( """
		<tr><td>
		<form method="post" action="comments.py?u=%s&p=%s">
		<table width="100%%" cellspacing="0" cellpadding="2">
		<tr><td></td><td><strong>Add a new comment:</strong></td></tr>
		<tr><td><label for="name">Name</label></td><td width="99%%"><input type="text" size="50" name="name" value="%s"/></td></tr>
		<tr><td><label for="email">Email</label></td><td><input type="text" size="50" name="email" value="%s"/></td></tr>
		<tr><td><label for="url">Website</label></td><td><input type="text" size="50" name="url" value="%s"/></td></tr>
		<tr><td><label for="comment">Comment</label></td><td><textarea name="comment" width="100%%" rows="10"></textarea></td></tr>
		<tr><td></td><td><input type="submit" value="Save comment" />
			<input type="button" value="Cancel" onclick="javascript:window.close()" /></td></tr>
		<tr><td></td><td><strong>Note</strong>: 'http://...' will be converted into links.
		HTML other than &lt;a href&gt;, &lt;b&gt;, &lt;i&gt;, &lt;s&gt; and &lt;tt&gt; will be stripped.</td></tr>
		<tr><td></td><td>Subscribe to an RSS feed of this comment thread:
		<a href="http://127.0.0.1:5335/system/pages/subscriptions?url=%s"><img border="0"
		src="http://myelin.pycs.net/images/tinyCoffeeCup.gif" width="10" height="10"
		alt="Subscribe to this comment thread in Radio UserLand" /></a>
		<a href="%s"><img border="0" src="http://myelin.pycs.net/images/xml.gif" width="36" height="14"
		alt="Link to the RSS (XML) feed for this comment thread" /></a>
		</td></tr>
		</table>
		</form>
		</td></tr>
		""" % ( self.u, self.p,
			self.storedName, self.storedEmail, self.storedUrl,
			urllib.quote( self.xmlFeedLink ), self.xmlFeedLink
		) )

		ret.append( endTableString )
		
		return ''.join( ret )

	def footer( self ):
		return footerString

	def comment( self, cmt ):
		ret = """
		<tr><td class="cmt">
			%s<br />
			<span class="commentfooter">&nbsp;&nbsp;posted by %s&nbsp;&nbsp;</span>
		""" % (
			cmt.cleanedUpComment,
			cmt.commentFooter,
		)
		
		if self.user:
			if int( self.user.usernum ) == int( self.u ):
				#ret += "logged in user: %s; this comment user: %s<br />" % ( self.user.usernum, self.u )
				ret += """
				<div><form method="post" action="comments.py?u=%s&p=%s">
				<input type="hidden" name="delete" value="%s" />
				<input type="submit" value="Delete comment" />
				</form></div>
				""" % ( self.u, self.p, cmt.iCmt )
		
		ret += """</td></tr>
		"""
		
		self.nComments += 1
		
		return ret
