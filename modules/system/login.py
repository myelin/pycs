# Python Community Server
#
#     login.py: User log in page
#
# Copyright (c) 2002, Phillip Pearson <pp@myelin.co.nz>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to 
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of 
# the Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import md5
import pycs_settings
import cgi
import binascii
import re

request['Content-Type'] = 'text/html'

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('Login'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="mailto:pp@myelin.co.nz">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = ''

fLoggedIn = 0

headers = util.IndexHeaders( request )
cookies = util.IndexCookies( headers )
#if cookies.has_key( 'u' ) and cookies.has_key( 'p' ):
#	s += "got u & p<br>"
#for k in cookies.keys():
#	s += "cookie %s: %s<br>" % ( k, cookies[k] )
if cookies.has_key( 'userInfo' ):
	u, p = re.search( '"(.*?)_(.*?)"', cookies['userInfo'] ).groups()
	u = binascii.unhexlify( u )
	#s += "usernum %s, pass %s<br>" % ( u, p )
	try:
		user = set.FindUser( u, p )
	except set.PasswordIncorrect:
		s += _("(password incorrect)")
		
	s += _("user already logged in: ") + user.usernum
	s += "<br>"

# Have we been POSTed to?
if form.has_key('email') and form.has_key('password'):

	try:
		pwHash = md5.md5( form['password'] ).hexdigest()
		
		user = set.FindUserByEmail(
			form['email'], 
			pwHash,
			)
		
		fLoggedIn = 1
		
		request['Set-Cookie'] = 'userInfo="%s_%s"' % (
			binascii.hexlify( user.usernum ),
			pwHash,
			)
		
		s += _("<p>You are now logged in as user <b>%s</b> (<b>%s</b>)</p>") % ( user.usernum, user.name )
	
	except pycs_settings.NoSuchUser:
		s += _('<p>Sorry, email address <b>%s</b> not found!</p>') % (form['email'],)
	
	except pycs_settings.PasswordIncorrect:
		s += _('<p>Sorry, the passsword was incorrect.  Please try again.</p>')

if not fLoggedIn:
	s += """
	<p>%s</p>
	
	<table align="center" width="100%%" cellspacing="2" cellpadding="2">
	<form method="post" action="login.py">
	<table>
		<tr>
			<td>%s</td>
			<td><input type="text" name="email" size="60" /></td>
		</tr>
		<tr>
			<td>%s</td>
			<td><input type="password" name="password" size="60" /></td>
		</tr>
		<tr>
			<td></td>
			<td><input type="submit" value="%s" /></td>
		</tr>
	</form>
	</table>
	
	""" % (	_("Enter your e-mail address and your password to log in. If you have more than one weblog hosted here, make sure you enter the e-mail address for the right blog."),
		_("E-mail address"),
		_("Password"),
		_("Log in"),
	)
else:
	s += _("""<p>Now you should see 'delete' buttons next to comments for <a href="%s">your weblog</a>.</p>""") % ( set.UserFolder( user.usernum ), )



	
# Dump it all out

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()
