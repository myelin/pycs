# Python Community Server
#
#     Makefile: build script for GNU make
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


U = www-radio
D = /home/$(U)

F = *.py *.pyc *.sh *.pl *.conf
FILES = $(addprefix $(D)/, $(F))
SUBDIRS = www conf modules
DIRS = $(addprefix $(D)/, $(SUBDIRS))
PYCSFILES = README LICENSE Makefile mkidx.pl \
	pycs.py \
	pycs_settings.py pycs_comments.py pycs_module_handler.py pycs_xmlrpc_handler.py \
	xmlStorageSystem.py radioCommunityServer.py \
	startserver.sh update.sh startserver.bat \
	test_server.py test_settings.py \
	analyse_logs.py \
	pycs.conf 
PYCSMODFILES = updates.py mailto.py users.py comments.py
SPECIFICS = $(PYCSFILES) medusa/*.py metakit.py Mk4py.so
VER = 0.01
DISTFN = pycs-$(VER)-src

.PHONY: check install all

all: check install
	#@echo "Try 'make check' or 'make install'"

check:
	export PYTHONPATH=medusa && pychecker pycs.py

install: scripts
	cp -f $(SPECIFICS) $(D)/
	#chmod -R 644 $(D)/*
	chmod 755 $(FILES)
	mkdir -p $(DIRS)
	chown $(U).$(U) $(DIRS)
	chmod 744 $(DIRS)

scripts:
	cp -a modules $(D)/
	chown root.root $(D)/modules -R
	chmod 755 $(D)/modules -R
	cp www/index.html $(D)/www/
	chown root.root $(D)/www/index.html
	chmod 644 $(D)/www/index.html

dist:
	rm -rf $(DISTFN)/
	rm -f $(DISTFN).tar.gz
	mkdir -p $(DISTFN)
	cp $(PYCSFILES) $(DISTFN)/
	mkdir -p $(DISTFN)/modules/system
	cp $(addprefix modules/system/, $(PYCSMODFILES)) $(DISTFN)/modules/system/
	mkdir -p $(DISTFN)/www
	cp www/dist_index.html $(DISTFN)/www/index.html
	tar -czf $(DISTFN).tar.gz $(DISTFN)/*
	rm -rf $(DISTFN)/
	cp $(DISTFN).tar.gz $(D)/www/
	chmod 644 $(D)/www/$(DISTFN).tar.gz
