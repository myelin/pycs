# comments.html

import urllib
import pycs_settings

set = pycs_settings.Settings( quiet=True )

headerString = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=%s" />
<title>Comments</title>
<style type="text/css">
<!--
body { font-family: verdana, sans-serif; }
.black { background-color: black; }
td { background-color:  lightgrey; }
.cmt { background-color: #eeeeee; }
.commentfooter { font-size: 0.8em; background-color: white; }
.quietlink { font-weight: bold; color: black; }
-->
</style>
</head>
<body>
""" % set.DocumentEncoding()

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

		if hasattr( self, 'link' ):
			if self.link:
				ret += [
					'<tr><td style="border: solid; border-color: black; border-width: 5px; font-weight: bold;">',
					_('You are commenting on the following link:<br><a href="%s" target="_blank">%s</a>') % (self.link, self.link),
					'</td></tr>'
				]
			
		return ''.join( ret )
		
	
	def endTable( self ):
		ret = []
		
		if self.nComments == 0:
			ret.append( _('<tr><td class="cmt"><strong>No comments yet</strong></td></tr>') )

		ret.append( """
		<tr><td>
		<form method="post" action="comments.py?u=%s&p=%s">
		<table width="100%%" cellspacing="0" cellpadding="2">
		<tr><td></td><td><strong>%s</strong></td></tr>
		<tr><td><label for="name">%s</label></td><td width="99%%"><input type="text" size="50" name="name" value="%s"/></td></tr>
		<tr><td><label for="email">%s</label></td><td><input type="text" size="50" name="email" value="%s"/></td></tr>
		<tr><td><label for="url">%s</label></td><td><input type="text" size="50" name="url" value="%s"/></td></tr>
		<tr><td><label for="comment">%s</label></td><td><textarea name="comment" cols="50" rows="10"></textarea></td></tr>
		<tr><td></td><td><input type="submit" value="%s" />
			<input type="button" value="%s" onclick="javascript:window.close()" /></td></tr>
		<tr><td></td><td><strong>%s</strong>: %s</td></tr>
		<tr><td></td><td>%s
		<a href="http://127.0.0.1:5335/system/pages/subscriptions?url=%s"><img border="0"
		src="%s/images/tinyCoffeeCup.gif" width="10" height="10"
		alt="%s" /></a>
		<a href="%s"><img border="0" src="%s/images/xml.gif" width="36" height="14"
		alt="%s" /></a>
		</td></tr>
		</table>
		</form>
		</td></tr>
		""" % ( self.u, self.p,
			_("Add a new comment:"),
			_("Name"),
			self.storedName,
			_("Email"),
			self.storedEmail,
			_("Website"),
			self.storedUrl,
			_("Comment"), _("Save Comment"), _("Cancel"),
			_("Note"),
			_("'http://...' will be converted into links. HTML other than &lt;a href&gt;, &lt;b&gt;, &lt;i&gt;, &lt;s&gt; and &lt;tt&gt; will be stripped."),
			_("Subscribe to an RSS feed of this comment thread:"),
			urllib.quote( self.xmlFeedLink ), self.set.ServerUrl(),
			_("Subscribe to this comment thread in Radio UserLand"),
			self.xmlFeedLink, self.set.ServerUrl(),
			_("Link to the RSS (XML) feed for this comment thread"),
		) )

		ret.append( endTableString )
		
		return ''.join( ret )

	def footer( self ):
		return footerString

	def comment( self, cmt, paragraph=None ):
		ret = """
		<tr><td class="cmt">
			%s<br />
			<span class="commentfooter">&nbsp;&nbsp;%s %s&nbsp;&nbsp;</span>
		""" % (
			cmt.cleanedUpComment,
			_("posted by"),
			cmt.commentFooter,
		)
		
		if self.user:
			u = int( self.u )
			if ( self.set.conf.has_key( 'adminusernum' ) and
				( int( self.set.conf['adminusernum'] ) == int( self.user.usernum ) )
			) or ( u == int( self.user.usernum ) ):
				#ret += "logged in user: %s; this comment user: %s<br />" % ( self.user.usernum, self.u )
				ret += """
				<div><form method="post" action="comments.py?u=%s&p=%s">
				<input type="hidden" name="delete" value="%s" />
				<input type="submit" value="%s" />
				</form></div>
				""" % ( self.u, self.p, cmt.iCmt,
					_("Delete comment") )
		
		ret += """</td></tr>
		"""
		
		self.nComments += 1
		
		return ret
