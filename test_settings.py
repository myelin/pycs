#!/usr/bin/python

# Python Community Server
#
#     test_settings.py: Quick test of the settings module
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


import pycs_settings
import md5

set = pycs_settings.Settings()

print "--- testing ---"

user1 = set.NewUser( "test@myelin.co.nz", "foo", "Phillip" )
print "user1",user1, user1.__dict__
print

user2 = set.NewUser( "asdf@asdf.com", "asdf", "aSDF" )
print "user2",user2, user2.__dict__
print

u = set.FindUser( 2, 'asdf' )
print "find user2", u, u.email, u.password, u.usernum, u.name

pp = set.FindUserByEmail( "test@myelin.co.nz", "foo" )
print "find pp@myelin", pp.email, pp.password, pp.usernum, u.name

try:
	zz = set.FindUser( 100, "asdf" )
	print "find usernum=100", zz
	raise "this should have failed"
except pycs_settings.NoSuchUser:
	print "good - no such user."

del set