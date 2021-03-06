#!/bin/sh

VER=$1

PY_VERSION=`./get_python_version.sh`

echo $PY_VERSION

. ./clean.sh

. ./build.sh
zip -r testman4trac.$VER-Py_$PY_VERSION-Trac_1.4.zip bin docs
tar cvzf testmanager.$VER-Py_$PY_VERSION-Trac_1.4.tar.gz bin docs

. ./clean.sh

mkdir testman4trac.$VER

cp *.sh testman4trac.$VER
cp *.txt testman4trac.$VER
cp *.cmd testman4trac.$VER
cp *.py testman4trac.$VER
cp -R sqlexecutor testman4trac.$VER
cp -R testman4trac testman4trac.$VER
cp -R tracgenericclass testman4trac.$VER
cp -R tracgenericworkflow testman4trac.$VER

cd testman4trac.$VER

. ./clean.sh
find . -type d -name .svn -print -exec rm -rf {} \;
find . -type d -name .hg -print -exec rm -rf {} \;
find . -type d -name .git -print -exec rm -rf {} \;
find . -type f -name "*.bak" -print -exec rm -f {} \;

cd ..

zip -r testman4trac.$VER-Trac_1.4.src.zip testman4trac.$VER
tar cvzf testmanager.$VER-Trac_1.4.src.tar.gz testman4trac.$VER

#rm -rf testman4trac.$VER testman4trac.$VER.SVN testman4trac.$VER.GIT
