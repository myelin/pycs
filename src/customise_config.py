# Customise config file passed in on STDIN
#
# Syntax:
#
#	python customise_config.py [server_user]

if __name__ == '__main__':
	import sys
	me, user = sys.argv
	print sys.stdin.read().replace(
		'{{USER}}', user
	)
