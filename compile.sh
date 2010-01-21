#!/bin/sh
ooc test.ooc -noclean
cd ooc_tmp
gcc -D__OOC_USE_GC__ -g -shared -fPIC -o../libtest.so -I. pyooc/test.c sdk/lang/*.c sdk/structs/*.c sdk/text/*.c sdk/io/*.c
cd ..
#rm -rf ooc_tmp
