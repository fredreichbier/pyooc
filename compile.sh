#!/bin/sh
ooc test.ooc -noclean
cd ooc_tmp
gcc -g -shared -fPIC -o../libtest.so -I. pyooc/test.c sdk/lang/*.c sdk/structs/*.c sdk/text/*.c
cd ..
#rm -rf ooc_tmp
