# comments.html

import urllib
import pycs_settings

set = pycs_settings.Settings( quiet=True )

headerString = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=%s" />
<title>Trackbacks</title>
<style type="text/css">
<!--
body { font-family: verdana, sans-serif; }
textarea { width: 100%% }
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
				'<tr><td style="border: solid; border-color: black; border-width: 3px; font-weight: bold;">',
				self.note,
				'</td></tr>'
			]
			
		return ''.join( ret )
		
	
	def endTable( self ):
		ret = []
		
		if self.nComments == 0:
			ret.append( _('<tr><td class="cmt"><strong>No trackbacks yet</strong></td></tr>') )

		ret.append( """
		<tr><td>
		<table width="100%%" cellspacing="0" cellpadding="2">
		<tr><td></td><td>%s
		<a href="http://127.0.0.1:5335/system/pages/subscriptions?url=%s"><img border="0"
		src="%s/images/tinyCoffeeCup.gif" width="10" height="10"
		alt="%s" /></a>
		<a href="%s"><img border="0" src="%s/images/xml.gif" width="36" height="14"
		alt="%s" /></a>
		</td></tr>
		</table>
		</td></tr>
		""" % (
			_("Subscribe to an RSS feed of this trackback thread:"),
			urllib.quote( self.xmlFeedLink ), self.set.ServerUrl(),
			_("Subscribe to this trackback thread in Radio UserLand"),
			self.xmlFeedLink, self.set.ServerUrl(),
			_("Link to the RSS (XML) feed for this trackback thread"),
		) )

		ret.append( endTableString )
		
		return ''.join( ret )

	def footer( self ):
		return footerString

	def comment( self, cmt, level=0 ):
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
				ret += """
				<div><form method="post" action="trackback.py?u=%s&p=%s">
				<input type="hidden" name="delete" value="%s" />
				<input type="submit" value="%s" />
				</form></div>
				""" % ( self.u, self.p, cmt.iCmt,
					_("Delete trackback") )
		
		ret += """</td></tr>
		"""
		
		self.nComments += 1
		
		return ret
