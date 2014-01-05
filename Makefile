all: repo libtest.so

clean:
	rm -rf rock_tmp repo libtest.so .libs

libtest.so: test.ooc
	rock -v +-fPIC +-shared
	gcc `find .libs/ -name '*.o'` -shared -o libtest.so

repo: libtest.so
	rock --backend=json --outpath=repo test.ooc

.PHONY: all clean
