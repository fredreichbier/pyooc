#!/bin/sh
ooc test.ooc -noclean
cd ooc_tmp
gcc -shared -fPIC -o../libtest.so -I. test.c lang/*.c
cd ..
#rm -rf ooc_tmp
