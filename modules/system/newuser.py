# Python Community Server
#
#     newuser.py: Create account page (for people not using Radio/PyDS/etc)
#
# Copyright (c) 2004, Phillip Pearson <pp@myelin.co.nz>
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

request['Content-Type'] = 'text/html; charset=%s' % set.DocumentEncoding()

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

page = {
	'title': _('New User (comment hosting)'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="mailto:pp@myelin.co.nz">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

s = ''

fLoggedIn = 0

headers = util.IndexHeaders( request )
cookies = util.IndexCookies( headers )

# Have we been POSTed to?
def get_values(*keys):
	ret = []
	for k in keys:
		v = form.get(k)
		if v:
			ret.append(form[k])
		else:
			return None
	return ret

def show_urls(u):
	global s
	s += """<p>Your usernum is %(usernum)s.</p>
<!--<p>If you want to use this server for comments, the URL is <b>%(commenturl)s</b></p>-->

<p>To get comments and trackbacks to work, you need to edit your weblog template and add the following HTML to the top:</p>

<p>&lt;script src="%(commenturl)s?u=%(usernum)s&amp;amp;c=counts" type="text/javascript"&gt;&lt;/script&gt;<br/>
&lt;script src="%(tburl)s?u=%(usernum)s&amp;amp;c=counts" type="text/javascript"&gt;&lt;/script&gt;
</p>

<p>Now, in your item template, you need to put the following:</p>

<p>Comment [&lt;script type="text/javascript" language="JavaScript"&gt;commentCounter('<i><b>postid</b></i>')&lt;/script&gt;]&lt;/a&gt;<br/>
TrackBack [&lt;script type="text/javascript" language="JavaScript"&gt;trackbackCounter('<i><b>postid</b></i>')&lt;/script&gt;]&lt;/a&gt;
</p>

<p>Replace <b>postid</b> with script to generate the post ID for your blogging tool.  In Radio, it should look like this:</p>

<p>Comment [&lt;script type="text/javascript" language="JavaScript"&gt;commentCounter('&lt;%%itemNum%%&gt;')&lt;/script&gt;]&lt;/a&gt;<br/>
TrackBack [&lt;script type="text/javascript" language="JavaScript"&gt;trackbackCounter('&lt;%%itemNum%%&gt;')&lt;/script&gt;]&lt;/a&gt;</p>

<p><b>NOTE: If you are using Radio, you need to turn off the normal comment system.  Go to <a href="http://127.0.0.1:5335/system/pages/prefs?page=2.12">this configuration page</a> and uncheck the box that says "Check this box to enable comments", then click Submit.</b></p>

""" % {
		'usernum': u.usernum,
		'commenturl': set.ServerUrl() + "/system/comments.py",
		'tburl': set.ServerUrl() + "/system/trackback.py",
		'serverurl': set.ServerUrl(),
		}

stop = Exception()
try:
	x = get_values('name', 'email', 'password', 'password2')
	if x is not None:
		name, email, password, password2 = x
		if password != password2:
			s += "<p>Passwords must match!</p>"
			raise stop
		pwHash = md5.md5( form['password'] ).hexdigest()

		try:
			u = set.FindUserByEmail(form['email'], pwHash)
			show_urls(u)
			raise stop
		except pycs_settings.PasswordIncorrect:
			s += "<p>I'm sorry, another user is already using that e-mail address.</p>"
			raise stop
		except pycs_settings.NoSuchUser:
			s += "<p>Creating your account ..."
			u = set.NewUser(email, pwHash, name)
			s += " done!</p>"
			show_urls(u)
except Exception, e:
	if e is stop:
		s += "<hr>"
	else:
		raise

s += """
	<p>%s</p>
	
	<table align="center" width="100%%" cellspacing="2" cellpadding="2">
	<form method="post" action="newuser.py">
	<table>
		<tr>
			<td>%s</td>
			<td><input type="text" name="name" size="60" /></td>
		</tr>
		<tr>
			<td>%s</td>
			<td><input type="text" name="email" size="60" /></td>
		</tr>
		<tr>
			<td>%s</td>
			<td><input type="password" name="password" size="60" /></td>
		</tr>
		<tr>
			<td>%s</td>
			<td><input type="password" name="password2" size="60" /></td>
		</tr>
		<tr>
			<td></td>
			<td><input type="submit" value="%s" /></td>
		</tr>
	</form>
	</table>
	
	""" % (	_("Enter your name, e-mail address and your password (twice) to create an account.  <b><i>Note: If you are using Radio, PyDS or bzero to host a weblog on this server, DO NOT create an account this way.  Your blogging tool will do it for you.  You should only be creating an account this way if you want to only host comments on this server.</i></b>"),
		_("Name"),
		_("E-mail address"),
		_("Password"),
		_("Repeat password"),
		_("Create account"),
	)



	
# Dump it all out

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()
