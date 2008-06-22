#!/bin/bash

case "$1" in
	1)
		cp settings_broken.dat rescued/settings.dat;
		python rescue_data.py || die "couldn't rescue data";
	;;
	
	2)
		if [ ! -f rescued/settings.txt ]; then
			mv rescued/settings_old.txt rescued/settings.txt;
		fi;
		rm rescued/settings.dat;
		python rescue_return_data.py || die "couldn't return data";
		mv rescued/settings.txt rescued/settings_old.txt;
		python rescue_data.py || die "couldn't read rescued data";
		mv rescued/settings.txt rescued/settings_new.txt;
		diff rescued/settings_old.txt rescued/settings_new.txt;
	;;
esac
