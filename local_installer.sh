#!/bin/bash

this_local="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
current_path=$(pwd)

function rmdir_if_exists {
	if [ -d "$1" ]; then
		echo -e "Removing dir $1"
		rm -rf $1
	fi
}

function rmv_files {
	# removes previous build dir and files
	rmdir_if_exists "build/"
	rmdir_if_exists "dist/"
	rmdir_if_exists "gcpinfra.egg-info/"
}

function getout {
	cd $current_path
	exit $1
}

cd $this_local  # go to correct dir

rmv_files  # clean it before me

# build the package
python $this_local/setup.py bdist_wheel
rtn=$?
if [ $rtn -ne 0 ]; then
	echo -e "Package build failed"
	getout 1
fi

# executing pip install
file_name=$(ls $this_local/dist/)
pip install $cached dist/$file_name
rtn=$?
if [ $rtn -eq 127 ]; then
	echo -e "\nIt appears that 'pip' is not installed. Please install 'pip'"
	echo -e " and retry installing this package."

	rmv_files
	getout 1
elif [ $rtn -ne 0 ]; then
	echo -e "\nCould not install wheel using pip."

	rmv_files
	getout 1
fi

# everything looks cool
rmv_files
getout 0
