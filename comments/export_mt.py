# comments.rss

# this file dumps out comments in moveable type import format, just in
# case you want to move a radio/bzero/pyds blog to MT.

import pycs_settings, cgi, defaultFormatter, comments, time

set = pycs_settings.Settings( quiet=True )

def mtesc(s):
	# escape something so it'll fit on a "FOO: bar" line
	s = s.strip()
	pos = len(s)
	for x in "\r\n":
		p = s.find(x)
		if p != -1 and pos > p:
			pos = p
	s = s[:pos]
	return s

def mtmlesc(s):
	# escape something so it'll fit in a multiline field
	return s

class formatter( defaultFormatter.defaultFormatter ):

	def __init__( self, set ):
		self.set = set

	def contentType(self):
		return "text/plain"

	def comment( self, cmt, paragraph, level ):
		author = cmt.cmt.name
		email = cmt.cmt.email
		url = cmt.cmt.url
		ip = ''
		try:
			timetuple = time.strptime(cmt.cmt.date, comments.STANDARDDATEFORMAT)
			date = time.strftime("%m/%d/%Y %H:%M:%S", timetuple) #dateString
		except ValueError:
			date = cmt.cmt.date
		desc = cmt.cleanedUpComment
		src = """DATE: unknown; post = %s
NO ENTRY: 1
-----
COMMENT:
AUTHOR: %s
EMAIL: %s
URL: %s
IP: %s
DATE: %s
%s
-----
--------
""" % ( paragraph.paragraph, mtesc(author), mtesc(email), mtesc(url), mtesc(ip), mtesc(date), mtmlesc(desc) )
		return src

