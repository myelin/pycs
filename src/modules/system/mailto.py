# Python Community Server
#
#     mailto.py: Spam-free mailto page
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
import string
import pycs_settings
import re
import cgi
import smtplib
import socket
from email.Message import Message
from email.Header import Header

# See pycs_module_handler.py for info on how modules work

# We should be able to get at the following globals:

#	request: an http request object
#		try request.split_uri() to get some info about the request


no8bit = re.compile(r'.*[^\x20-\x7f]')
def quoteHeader(txt, fromcset, tocset):
	txt = txt.decode(documentEncoding).encode(mailEncoding)
	if no8bit.match(txt):
		return str(Header(txt, mailEncoding))
	else:
		return txt

[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

request['Content-Type'] = 'text/html; charset=%s' % set.DocumentEncoding()

page = {
	'title': _('Feedback'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="mailto:pp@myelin.co.nz">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

# Actually generate the output

s = ""

usernum = re.compile( "(\d+)" ).search( query['usernum'] )
if usernum == None:
	raise "Can't get usernum"

usernum = usernum.group(0)
	
u = set.User( usernum )

if request.command.lower() == 'post':

	err = None
	
	s += _('<h2>Posting your message</h2>')

	fields = ['fromName', 'fromEmail', 'fromUrl', 'subject', 'msgBody']

	documentEncoding = set.DocumentEncoding()
	mailEncoding = set.MailEncoding()

	fromName = form['fromName']
	fromEmail = re.compile( r'[A-Za-z0-9\-\_\+\@\.]+' ).match( form['fromEmail'] )
	if fromEmail is None:
		fromEmail = ""
	else:
		fromEmail = fromEmail.group( 0 )
	fromUrl = re.compile( r'[A-Za-z0-9\-\_\:\?\&\+\%\/\.]+' ).match( form['fromUrl'] )
	if fromUrl is None:
		fromUrl = ""
	else:
		fromUrl = fromUrl.group( 0 )
	subject = form['subject']

	s += '<table>'

	# Get rid of HTML and display it
	for field in fields:
		s += '<tr><td>%s</td><td><strong>%s</strong></td></tr>' % (
			field,
			string.replace( cgi.escape( form[field] ), "\n", "<br />\n" )
			)

	s += '</table>'

	msgBody = '%s ( %s ) sent you a message through the Python Community Server:\n\n' % (fromName, fromUrl) + form['msgBody']

	# Now build an RFC-2822 message out of it
	msg = Message()
	msg.set_charset(mailEncoding)
	msg.set_payload(msgBody.decode(documentEncoding).encode(mailEncoding))
	msg['X-User-Agent'] = 'Python Community Server'
	msg['From'] = '%s (%s)' % (
		fromEmail,
		quoteHeader(fromName, documentEncoding, mailEncoding)
	)
	msg['To'] = u.email
	msg['Subject'] = quoteHeader(subject, documentEncoding, mailEncoding)

	try:
		sender = smtplib.SMTP( "localhost", 25 )
		sender.sendmail(
			set.ServerMailTo(),
			u.email,
			msg.as_string(),
			)
		
	except socket.error, e:
		err = e

	except smtplib.SMTPRecipientsRefused:
		err = _("The recipient's mail server didn't like it.")
	
	except smtplib.SMTPHeloError:
		err = _("The server didn't reply properly to the \"HELO\" greeting!")
	
	except smtplib.SMTPSenderRefused:
		err = _("The server didn't accept the from address!")
	
	except smtplib.SMTPDataError:
		err = _("The server just didn't like the message for some reason!")
	
	#sender.quit()
	
	if err == None:
		s += _("""
		<h2>Message sent OK; <a href="%s">click here to go back</a>.</h2>
		""") % ( set.UserFolder( usernum ) )
		
	else: # An error occurred
		s = _("""
		<h2>Sorry, the mail didn't send properly!</h2>
		<h2>Error:</h2>
		<h2><center><strong>%s</strong></center></h2>
		""") % (err,)

else:

	s += _('<h2>Sending a message to %s</h2>') % ( u.name, )

	s += """
	<form method="post" action="mailto.py?action=send&usernum=%s">
	<table width="80%%" cellspacing="0" cellpadding="2">
	<tr>	<td>%s</td>
		<td><input type="text" name="fromName" size="60" /></td>
		</tr>
	<tr>	<td>%s</td>
		<td><input type="text" name="fromEmail" size="60" /></td>
		</tr>
	<tr>	<td>%s</td>
		<td><input type="text" name="fromUrl" size="60" value="http://" /></td>
		</tr>
	<tr>	<td>%s</td>
		<td><input type="text" name="subject" size="60" /></td>
		</tr>
	<tr>	<td></td>
		<td><textarea name="msgBody" rows="20" cols="60"></textarea></td>
		</tr>
	<tr>	<td></td>
		<td><input type="submit" value="%s" /></td>
		</tr>
	</table>
	</form>
	""" % ( usernum,
	        _("Your name"),
	        _("Your e-mail address"),
		_("Your URL"),
		_("Subject"),
		_("Send message") )

# Dump it all out

page['body'] = s
s = set.Render( page, usernum = u.usernum )

request['Content-Length'] = len(s)
request.push( s )
request.done()
