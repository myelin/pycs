# Python Community Server
# http://www.pycs.net/
#
#	Makefile: Python Community Server build / installation script
#	Requires GNU make - 'make' on Linux, 'gmake' on FreeBSD
#
# Copyright (c) 2002, Phillip Pearson <pp@myelin.co.nz>
# http://www.myelin.co.nz/
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

# The user PyCS will be running as
USER = www-pycs

# The user who is installing PyCS.
# If you don't have root access, change this to 'ROOT = www-pycs'
# (or the PyCS user, if not www-pycs).
ROOT = root

# The start of all paths.  Subdirectories /usr/lib/pycs,
# /var/lib/pycs, /etc/pycs, /var/log/pycs will be created.
PREFIX = /home/www-pycs

SUBDIRS = www conf modules comments trackbacks

NOTEFILES = README LICENSE
INSTFILES = Makefile mkidx.pl make_readme.pl 
CODEFILES = pycs.py pycsadm.py \
	pycs_settings.py pycs_module_handler.py pycs_xmlrpc_handler.py \
	pycs_translation.py pycs_rewrite_handler.py string_collector.py \
	pycs_auth_handler.py authorizer.py daemonize.py pycs_block_handler.py \
	pycs_tokens.py pycs_http_util.py html_cleaner.py strptime.py \
	xmlStorageSystem.py radioCommunityServer.py weblogUpdates.py \
	pycs_paths.py updatesDb.py pycsAdmin.py changepasswd.py \
	accessRestrictions.py pycs_webauth_handler.py search_engines.py
TESTFILES = test_server.py test_settings.py
CONFFILES = pycs.conf rewrite.conf
MISCFILES = startserver.sh update.sh startserver.bat analyse_logs.py
MEDUSAFILES = medusa/*.py
MSGSFILES = pycs-*.msgs

# Directories

# Read-only stuff
NOTEDIR = $(PREFIX)/usr/share/doc/pycs
BASEDIR = $(PREFIX)/usr/lib/pycs
CODEDIR = $(BASEDIR)/bin
MEDUSADIR = $(CODEDIR)/medusa
COMMENTDIR = $(CODEDIR)/comments
TRACKBACKDIR = $(CODEDIR)/trackbacks

# Config
CONFDIR = $(PREFIX)/etc/pycs

# Runtime data
VARDIR = $(PREFIX)/var/lib/pycs
RUNDIR = $(PREFIX)/var/run/pycs
DATADIR = $(VARDIR)/data
WEBDIR = $(VARDIR)/www
WEBIMGDIR = $(WEBDIR)/images
RESDIR = $(WEBDIR)/initialResources
MODDIR = $(VARDIR)/modules
MSGSDIR = $(BASEDIR)/messages

# Logging
LOGDIR = $(PREFIX)/var/log/pycs

# All files (well, most files), for 'make dist'
PYCSFILES = $(NOTEFILES) $(INSTFILES) $(CODEFILES) \
	$(MISCFILES) \
	$(TESTFILES) \
	$(addsuffix .default, $(CONFFILES))

COMMENTFILES = __init__.py rss.py rssfull.py export_mt.py html.py defaultFormatter.py
TRACKBACKFILES = __init__.py rss.py rssfull.py html.py defaultFormatter.py
PYCSMODFILES = updates.py mailto.py users.py comments.py login.py count.py referers.py searches.py rankings.py zeitgeist.py trackback.py search.py
WEBFILES = index.html history.html readme.html pycs.css
WEBIMGFILES = xml.gif mailto.gif tinyCoffeeCup.gif
RESFILES = defaultFeeds.opml defaultCategories.opml
SPECIFICS = $(PYCSFILES) medusa/*.py metakit.py Mk4py.so
VER = 0.12pre2
DEBVER = $(VER)-`cat DebianVersion`
DISTFN = pycs-$(VER)-src
DEBFN = pycs_$(DEBVER)_all.deb
LATESTFN = pycs-latest-src

INSTALL = /usr/bin/install -c

INSTALL_USER = $(INSTALL) -g $(USER) -o $(USER)
INSTALL_ROOT = $(INSTALL) -g $(ROOT) -o $(ROOT)

# Logs and config files - visible only to root
INSTALL_MKDIR_PRIV = $(INSTALL_ROOT) -d -m 700
INSTALL_PRIV = $(INSTALL_ROOT) -m 600

# Code and invariant stuff - visible to all, writeable only by root
INSTALL_MKDIR_RW = $(INSTALL_USER) -m 700
INSTALL_RW = $(INSTALL_USER) -m 400

# Data files - visible & writeable to server user (but nobody else)
INSTALL_MKDIR_RO = $(INSTALL_ROOT) -d -m 755
INSTALL_RO = $(INSTALL_ROOT) -m 644

.PHONY: check install all

all: check install
	#@echo "Try 'make check' or 'make install'"

check:
	export PYTHONPATH=medusa && pychecker pycs.py

install: user scripts
	# Config files go in /etc/pycs
	$(INSTALL_MKDIR_PRIV) $(CONFDIR)
	for f in $(CONFFILES); do \
		if [ ! -f $(CONFDIR)/$$f ]; then \
			python customise_config.py "$(USER)" < $$f.default > $$f; \
			$(INSTALL_PRIV) $$f $(CONFDIR)/$$f; \
		fi; \
	done

	# Variant stuff (see below for details - data, web, etc)
	$(INSTALL_MKDIR_RW) -d $(VARDIR)
	$(INSTALL_MKDIR_RW) -d $(RUNDIR)

	# Data files go in /var/lib/pycs/data
	$(INSTALL_MKDIR_RW) -d $(DATADIR)

	# Web files go in /var/lib/pycs/www
	$(INSTALL_MKDIR_RW) -d $(WEBDIR)

	# Notes go in /usr/share/doc/pycs
	$(INSTALL_MKDIR_RO) -d $(NOTEDIR)
	$(INSTALL_RO) $(NOTEFILES) $(NOTEDIR)/
	mv $(NOTEDIR)/LICENSE $(NOTEDIR)/copyright

	# Executables go in /usr/lib/pycs/bin
	$(INSTALL_MKDIR_RO) -d $(CODEDIR)
	$(INSTALL_RO) $(CODEFILES) $(CODEDIR)/
	python pycs_paths.py "$(PREFIX)" > $(CODEDIR)/pycs_paths.py

	# Message catalogs go into /usr/lib/pycs/messages
	$(INSTALL_MKDIR_RO) -d $(MSGSDIR)
	$(INSTALL_RO) $(MSGSFILES) $(MSGSDIR)/

	# Medusa goes in /usr/lib/pycs/bin/medusa
	$(INSTALL_MKDIR_RO) -d $(MEDUSADIR)
	$(INSTALL_RO) $(MEDUSAFILES) $(MEDUSADIR)/

	# Log files go in /var/log
	$(INSTALL_MKDIR_RW) -d $(LOGDIR)

	$(INSTALL_ROOT) -m 755 startserver.sh $(BASEDIR)/startserver.sh

scripts:
	$(INSTALL_MKDIR_RO) -d $(MODDIR)
	$(INSTALL_MKDIR_RO) -d $(MODDIR)/system
	for f in `cd modules && find * | grep -E "\.py$$" && cd ..`; do $(INSTALL_RO) modules/$$f $(MODDIR)/$$f; done

	$(INSTALL_MKDIR_RO) -d $(COMMENTDIR)
	$(INSTALL_RO) $(addprefix comments/, $(COMMENTFILES)) $(COMMENTDIR)/

	$(INSTALL_MKDIR_RO) -d $(TRACKBACKDIR)
	$(INSTALL_RO) $(addprefix trackbacks/, $(TRACKBACKFILES)) $(TRACKBACKDIR)/

	# Install the default web files (index, history, readme) in www/;
	# you can safely edit the files in $(PREFIX)/var/lib/pycs/www/ once
	# this is done as they will not be overwritten by a future install.
	perl -w make_readme.pl < README > www/readme.html
	$(INSTALL_MKDIR_RO) -d $(WEBDIR)
	for f in $(WEBFILES); do \
		if [ ! -f $(WEBDIR)/$$f ]; then \
			$(INSTALL_RO) www/$$f $(WEBDIR)/; \
		fi; \
	done

	$(INSTALL_MKDIR_RO) -d $(WEBIMGDIR)
	for f in $(WEBIMGFILES); do \
		if [ ! -f $(WEBIMGDIR)/$$f ]; then \
			$(INSTALL_RO) www/images/$$f $(WEBIMGDIR)/; \
		fi; \
	done

	# Install the default OPML files in www/initialResources
	$(INSTALL_MKDIR_RO) -d $(RESDIR)
	for f in $(RESFILES); do \
		if [ ! -f $(RESDIR)/$$f ]; then \
			$(INSTALL_RO) www/initialResources/$$f $(RESDIR)/; \
		fi; \
	done

dist:
	rm -rf $(DISTFN)/
	rm -f $(DISTFN).tar.gz
	mkdir -p $(DISTFN)
	cp $(PYCSFILES) $(MSGSFILES) $(DISTFN)/

	mkdir -p $(DISTFN)/modules/system
	cp $(addprefix modules/system/, $(PYCSMODFILES)) $(DISTFN)/modules/system/

	mkdir -p $(DISTFN)/www
	cp $(addprefix www/, $(WEBFILES)) $(DISTFN)/www/

	mkdir -p $(DISTFN)/www/images
	cp $(addprefix www/images/, $(WEBIMGFILES)) $(DISTFN)/www/images/

	mkdir -p $(DISTFN)/www/initialResources
	cp $(addprefix www/initialResources/, $(RESFILES)) $(DISTFN)/www/initialResources/

	mkdir -p $(DISTFN)/comments
	cp $(addprefix comments/, $(COMMENTFILES)) $(DISTFN)/comments/

	mkdir -p $(DISTFN)/trackbacks
	cp $(addprefix trackbacks/, $(TRACKBACKFILES)) $(DISTFN)/trackbacks/

	tar -czf $(DISTFN).tar.gz $(DISTFN)/*
	rm -rf $(DISTFN)/
	cp $(DISTFN).tar.gz $(WEBDIR)/
	chmod 644 $(WEBDIR)/$(DISTFN).tar.gz
	rm -f $(WEBDIR)/$(LATESTFN).tar.gz
	ln -s $(WEBDIR)/$(DISTFN).tar.gz $(WEBDIR)/$(LATESTFN).tar.gz

user:
	# Set up the www-pycs user, if it doesn't already exist
	-groupadd $(USER)
	-useradd -d $(VARDIR) -g $(USER) $(USER)

dpkg:
	rm -rf Debian
	mkdir -p Debian/DEBIAN
	env VERSION=$(DEBVER) python replace_vars.py < Debian.src/DEBIAN/control > Debian/DEBIAN/control
	make install PREFIX=./Debian
	find ./Debian -type d | xargs chmod 755
	mkdir -p debian_out
	dpkg-deb -b Debian debian_out
