import urllib
import string
import re

def SplitQuery( q ):
	d = {}

	if (q == None) or (len( q ) == 0):
		return d
	
	# Skip the first char if it's a '?'
	if q[0] == '?':
		q = q[1:]
	
	# Split it up ('blah=pokwer&foo=blah' -> ['blah=pokwer', 'foo=blah'])
	args = re.split( '\&', q )
	
	#print 'split args:', args
	sep = re.compile( '^(.*?)\=(.*)$' )
	
	for arg in args:
		m = sep.search( arg )
		if m:
			key, val = m.groups()
			d[key] = urllib.unquote_plus( val )
			#print 'key',key,' val',val
	
	# Return whole hash
	return d


def MungeHTML( txt ):
	return string.replace(
		string.replace(
		string.replace( txt, '"', '&quot;' ),
		'<', '_' ),
		'>', '_' )
	
def IndexHeaders( request ):

	"Make a dictionary out of all the HTTP headers in 'request'"

	headers = {}
	
	headerRE = re.compile(
		r'^(.*?)\: (.*)$'
		)
	for h in request.header:
		m = headerRE.search( h )
		if m:
			key, val = m.groups()
			headers[key] = val
			#s += "header '%s': '%s'<br>" % ( key, val )
		
	return headers

def IndexCookies( headers ):

	"Make a dictionary out of all the cookies in 'headers'"
	
	cookies = {}
	
	if headers.has_key( 'Cookie' ):
		import re
		for line in re.split( '; ', headers['Cookie'] ):
			key, val = re.match( '(.*?)=(.*)', line ).groups()
			cookies[key] = val
		#cookies = SplitQuery( headers['Cookie'] )
		
	return cookies

