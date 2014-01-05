#!/bin/sh

VER=$1

. ./clean.sh

svn checkout --username=seccanj svn+ssh://seccanj@svn.code.sf.net/p/testman4trac/code/ testman4trac.$VER.SVN
cd testman4trac.$VER.SVN
cp -R ../testman4trac.$VER/* .
svn status
svn add
#svn commit

cd ..

