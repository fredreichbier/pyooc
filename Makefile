all: repo libtest.so

clean:
	rm -rf rock_tmp repo libtest.so .libs

libtest.so: test.ooc
	rock -nolibcache -o=libtest.so -noclean -g +-shared +-fPIC +-Wl,-export-dynamic +-Wl,-soname,libtest.so test.ooc

repo: libtest.so
	rock -backend=json -outpath=repo test.ooc

.PHONY: all clean
