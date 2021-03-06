# comments.html

import urllib
import cgi
import pycs_settings

set = pycs_settings.Settings( quiet=True )

def getHeaderString(usernum):
	csslink = None
	if usernum:
		try:
			csslink = set.getUserStylesheet(usernum)
		except pycs_settings.NoSuchUser:
			print "no such user: %s" % `usernum`
			pass
	css = """<style type="text/css">
<!--
body { font-family: verdana, sans-serif; }
.black { background-color: black; }
.cmt { background-color: #eeeeee; padding: 1em; border: solid 1px black; margin-bottom: 1em; }
.commentfooter { font-size: 0.8em; background-color: white; }
.quietlink { font-weight: bold; color: black; }
-->
</style>"""
	if csslink:
		css += """\n<link rel="stylesheet" type="text/css" href="%s" />""" % cgi.escape(csslink, 1)
	
	headerString = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=%s" />
<title>Comments</title>
%s
</head>
<body>
""" % (set.DocumentEncoding(), css)
	return headerString

startTableString = """
<ol>
"""

endTableString = """
</ol>
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
		return getHeaderString(self.u)
		
	def startTable( self ):
		ret = []

		def notediv(msg):
			return [
				'<div style="border: solid; border-color: black; border-width: 5px; padding: 1em; font-weight: bold; margin-bottom: 1em;">',
				msg,
				'</div>'
				]
		
		if hasattr( self, 'note' ):
			ret += notediv(self.note)

		if hasattr( self, 'link' ):
			if self.link:
				ret += notediv(_('You are commenting on the following link:<br /><a href="%s" target="_blank">%s</a>') % (self.link, self.link))

		ret.append(startTableString)
		return ''.join( ret )
	
	def endTable( self ):
		ret = []
		
		if self.nComments == 0:
			ret.append( _('<div class="cmt"><strong>No comments yet</strong></li>') )

		ret.append( endTableString )
		ret.append( """<div style="border: solid 1px black; padding: 1em; background-color: lightgrey;">""")
		if self.comments_disabled:
			ret.append(_("Comments are disabled for this user."))
		else:
			ret.append("""<form method="post" action="comments.py?u=%s&amp;p=%s">""" % ( self.u, self.p ) )
			if hasattr(self, 'link') and self.link:
				ret.append( '<input type="hidden" name="link" value="%s" />' % self.link )
			ret.append( """
		<table width="100%%" cellspacing="0" cellpadding="2">
		<tr><td></td><td><strong>%s</strong></td></tr>
		<tr><td><label for="name">%s</label></td><td width="99%%"><input type="text" size="50" name="name" id="name" value="%s"/></td></tr>
		<tr><td><label for="email">%s</label></td><td><input type="text" size="50" name="email" id="email" value="%s"/></td></tr>
		<tr><td><label for="url">%s</label></td><td><input type="text" size="50" name="url" id="url" value="%s"/></td></tr>
		<tr><td><label for="comment">%s</label></td><td><textarea name="comment" id="comment" cols="50" rows="10"></textarea></td></tr>
		<tr><td></td><td><input type="submit" value="%s" />
			<input type="button" value="%s" onclick="javascript:window.close()" /></td></tr>
		<tr><td></td><td><strong>%s</strong>: %s</td></tr>
		<tr><td></td><td>%s
		<a href="http://127.0.0.1:5335/system/pages/subscriptions?url=%s"><img border="0"
		src="%s/images/tinyCoffeeCup.gif" width="10" height="10"
		alt="%s" /></a>
		<a href="%s"><img border="0" src="%s/images/xml.gif" width="36" height="14"
		alt="%s" /></a><br/>
		<a href="/system/login.py">Log in</a> to delete comments.
		</td></tr>
		</table>
		</form>
		</div>
		""" % ( _("Add a new comment:"),
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
			urllib.quote( cgi.escape(self.xmlFeedLink, 1) ), self.set.ServerUrl(),
			_("Subscribe to this comment thread in Radio UserLand"),
			cgi.escape(self.xmlFeedLink, 1), self.set.ServerUrl(),
			_("Link to the RSS (XML) feed for this comment thread"),
			) )
		
		return ''.join( ret )

	def footer( self ):
		return footerString

	def comment( self, cmt, paragraph=None ):
		ret = """
		<li class="cmt">
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
				<div><form method="post" action="comments.py?u=%s&amp;p=%s">
				<input type="hidden" name="delete" value="%s" />
				<input type="submit" value="%s" />
				</form></div>
				""" % ( self.u, self.p, cmt.cid,
					_("Delete comment") )
		
		ret += """</li>
		"""
		
		self.nComments += 1
		
		return ret
