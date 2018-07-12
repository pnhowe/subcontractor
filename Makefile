all:
	./setup.py build

install:
	mkdir -p $(DESTDIR)/usr/sbin
	mkdir -p $(DESTDIR)/etc

	install -m 755 sbin/* $(DESTDIR)/usr/sbin
	install -m 644 subcontractor.conf $(DESTDIR)/etc

	./setup.py install --root $(DESTDIR) --install-purelib=/usr/lib/python3/dist-packages/ --prefix=/usr --no-compile -O0

test-requires:
	python3-pytest python3-pytest-cov python3-pytest-django python3-pytest-mock

test:
	py.test-3 -x --cov=subcontractor --cov-report html --cov-report term -vv subcontractor

clean:
	./setup.py clean
	$(RM) -fr build
	$(RM) -f dpkg
	dh_clean

dpkg-distros:
	echo xenial

dpkg-requires:
	echo dpkg-dev debhelper cdbs python3-dev python3-setuptools

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

.PHONY: test dpkg-distros dpkg-requires dpkg
