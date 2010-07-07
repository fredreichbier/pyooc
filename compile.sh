#!/bin/sh
rm -rf rock_tmp
rock -nolibcache -o=libtest.so -noclean -g +-shared +-fPIC +-Wl,-export-dynamic +-Wl,-soname,libtest.so test.ooc
