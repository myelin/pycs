#!/usr/bin/python

from sgmllib import SGMLParser
import re
import string

class htmlCleaner( SGMLParser ):

	def __init__( self ):
		SGMLParser.__init__( self )
		self.cleanedHTML = ''
		self.cleanedText = ''
		self.openTags = {}

	def getCleanHtml( self ):
		for tag, count in self.openTags.items():
			self.cleanedHTML += ("</%s>" % tag) * count
		return self.cleanedHTML

	def handle_data( self, data ):
		self.cleanedText += data
		self.cleanedHTML += string.replace(
			re.sub(
				r'(http://[^\r\n \"\<]+)',
				r'<a href="\1" target="_blank">\1</a>',
				data,
			),
			"\n",
			"<br />\n",
		)

	def handle_entityref( self, entity ):
		self.cleanedHTML += '&%s;' % entity

	def handle_starttag( self, tag, method, attrs ):
		self.openTags[tag] = self.openTags.setdefault(tag, 0) + 1
		if not method( attrs ):
			self.cleanedHTML += "<" + tag + ">"
		
	def handle_endtag( self, tag, method ):
		count = self.openTags.setdefault(tag, 0)
		if not count:
			return
		if not method():
			self.cleanedHTML += "</" + tag + ">"
		self.openTags[tag] = count - 1
	
	def start_i( self, attrs ): pass
	def end_i( self ): pass
		
	def start_b( self, attrs ): pass
	def end_b( self ): pass
	
	def start_s( self, attrs ): pass
	def end_s( self ): pass
	
	def start_tt( self, attrs ): pass
	def end_tt( self ): pass
	
	def start_a( self, attrs ):
		f=1
		for key, val in attrs:
			if key == 'href':
				self.cleanedHTML += '<a href="%s" target="_blank">' % ( val, )
				f=0
		if f:
			self.cleanedHTML += '<a>'
		return 1
	def end_a( self ):
		self.cleanedHTML += '</a>'
		return 1

def cleanHtml( text ):
	parser = htmlCleaner()
	parser.feed( text )
	parser.close()
	return parser.getCleanHtml()

if __name__ == '__main__':
	text = [
		"""I'm writing my <b>Radio Klogging Kit for Managers</b> as an <a href="http://radio.weblogs.com/0100827/instantOutliner/klogging.opml">OPML file</a> with <a href="http://www.cadenhead.org/servlet/ViewInstantOutline?opmlFile=http://radio.weblogs.com/0100827/instantOutliner/klogging.opml">a link on my site using your servlet</a>. I have a pointer to the opml in my Instant Outline. Does the polling of my i/o cascade to xref'd outlines? """,
		"""It looks like someone's subscribed to the rendered form of your outline. People should be subscribing to the raw OPML version - http://rcs.myelin.cjb.net/users/0000001/instantOutliner/rogersCadenhead.opml - but actually they're subscribing to the one that calls your servlet. 

Your outline is currently the most popular file on this server, because you plus one or two others are downloading it every 10-60 seconds. I can't imagine the hammering radio.weblogs.com must be getting from all the I/O polling, but it must be pretty shocking.""",
		"""Script should be removed: <script>foo bar</script>""",
		"""Entities &amp; stuff should stay: &lt;b&gt; shouldn't make the text bold!""",
		"""unclosed tags should be <i>closed""",
		"""unopened tags </i> should be ignored""",
	]
	for post in text:

		print "PARSING:"
		print post
		print "--->"
		print cleanHtml( post )
