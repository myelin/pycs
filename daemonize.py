#!/usr/local/bin/python
#
'''\
Python code to turn a unix program into a daemon
mocons.lib.utils.daemonize.py
jjk  06/25/97  001
jjk  04/15/98  002  renamed from MdcBecomeDaemon.py

**works only on unix - NT does not support fork() command

from comp.lang.python postings
	Conrad Minshall <conrad@apple.com> 8/3/96
	Fredrik Lundh <Fredrik_Lundh@ivab.se> 8/5/96
	Monty Zukowski <monty@tbyte.com>	8/6/96

usage
	from mocons.lib.utils import daemonize
	daemonize.become_daemon(daemon_home_directory_name)

To start a test Daemon:
	daemonize.py test

'''


def become_daemon(ourHomeDir='.',outLog=None,errLog=None):
	"""Robustly turn us into a UNIX daemon, running in ourHomeDir.
	XXX on SVR4 some claim you should re-fork after the setsid()
	jjk  06/25/97  001

	Added an option to redirect stdout and stderr to appropriate files.
	The big key here is that the output is unbuffered.  Additionally, it
	should be possible to reshape this code to make it a little simpler, 
	but the task should be pretty obvious to see what is does.
	mch  10/30/2002  002
	"""
	import os
	import sys
	if os.fork() != 0:  # launch child and...
		os._exit(0)     # kill off parent
	os.setsid()
	os.chdir(ourHomeDir)
	os.umask(0)
	sys.stdin.close()
        if errLog and outLog:
            sys.stderr=open (errLog, 'a', 0)
            sys.stdout=open (outLog, 'a', 0)
	elif errLog:
	    sys.stderr=open (errLog, 'a', 0)
	    sys.stdout=NullDevice ()
	elif outLog:
	    sys.stdout=open (outLog, 'a', 0)
	    sys.stderr=NullDevice ()
        else:
	    sys.stdout = NullDevice()
	    sys.stderr = NullDevice()

class NullDevice:
	"""A substitute for stdout and stderr that writes to nowhere
	jjk  06/25/97  001
	"""

	def write(self, s):
		"""accept a write command, but do nothing
		jjk  06/25/97  001
		"""
		pass

def term (signal, param):
	"""Default signal handler behavior
	"""
	#It might be nice to remove a PID file here, if
	#one exists.  Since we do not know its name this
	#is left up to a developer
	print sys.argv[0] , "terminating"
	sys.exit(0)

def install_handlers ():
	import signal
	#install default signal profile
	signal.signal(signal.SIGTTOU, signal.SIG_IGN)
	signal.signal(signal.SIGTTIN, signal.SIG_IGN)
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)
	signal.signal(signal.SIGTSTP, term)
	signal.signal(signal.SIGTERM, term)
	signal.signal(signal.SIGINT, term)

def test():
	"""test become_daemon(). Launch a daemon that writes the time
	to a file every 10 seconds
	jjk  06/25/97  001
	mch  10/30/2002  002
	"""
	#It's important to install the signal handlers early as we
	#don't want the initiating process to have different behavior
	#than what actually ends up as the memory persistent process.
	install_handlers ()

	import os
	import time

	#Define some parameters for the daemon code
	filename = 'daemonize.test.out'
	pidfile = 'daemonize.test.pid'
	out = 'daemonize.test.stdout'
	err = 'daemonize.test.stderr'
	sleepSeconds = 10

	#Dump this information to STDOUT for review by the user
	print
	print 'Starting a test Daemon:'
	print '    every', sleepSeconds, "seconds, the daemon's process id"
	print '    and the the current time will be appended'
	print '    to the file', filename
	print 'You can view the output as it changes with:'
	print '    tail -f', filename
	print 'To stop the daemon, determine its PID from'
	print 'the output file, and use the kill command:'
	print '    kill <processid>'
	
	#Now actually create the daemon process (a.k.a. memory persistent process)
	become_daemon('.',out,err)

	#write the PID to a pid file, note the PID is here because
	#we are now within the execution scope of the daemon. any pids
	#before the call to become_daemon() will record the wronG PID.
	pid = os.getpid()	
	pf=open (pidfile, 'w')
	pf.write ("%d" % pid)
	pf.close ()

	#Show how STDERR works
	sys.stderr.write ("This is a test message to STDERR @ '%s'\n"%str (sys.stderr))

	#Do some work
	f = open(filename, 'a')
	f.write('\n\n*****Starting Test Daemon, PID: %d\n'%pid)
	f.close()
	#MAIN DAEMON BODY

	while(1):
		#Show how STDOUT works
		print "This is a test message to STDOUT @ " + "'" + str (sys.stderr) + "'"
		ctime = time.asctime(time.localtime(time.time()))
		f = open(filename, 'a')
		f.write('PID: %d  Time: %s\n'%(pid, ctime))
		f.close()
		time.sleep(sleepSeconds)

if (__name__ == '__main__'):
	import sys, string
	if (len(sys.argv)>1):
		if (string.lower(sys.argv[1])=='test'):
			test()
	else:
		print
		print 'daemonize.py'
		print 'Python code to turn a unix program into a daemon'
		print 'To start a test Daemon:'
		print '     daemonize.py test'

