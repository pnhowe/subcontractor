VERSION := $(shell head -n 1 debian/changelog | awk '{match( $$0, /\(.+?\)/); print substr( $$0, RSTART+1, RLENGTH-2 ) }' | cut -d- -f1 )

all:
	./setup.py build

install:
	mkdir -p $(DESTDIR)/usr/bin
	mkdir -p $(DESTDIR)/etc

	install -m 755 bin/* $(DESTDIR)/usr/bin
	install -m 644 subcontractor.conf.sample $(DESTDIR)/etc/

	./setup.py install --root=$(DESTDIR) --install-purelib=/usr/lib/python3/dist-packages/ --prefix=/usr --no-compile -O0

version:
	echo $(VERSION)

clean:
	./setup.py clean || true
	$(RM) -r build
	$(RM) dpkg
	$(RM) -r htmlcov
	dh_clean || true
	find -name *.pyc -delete
	find -name __pycache__ -delete

dist-clean: cleane

.PHONY:: all install version clean dist-clean

test-blueprints:
	echo ubuntu-focal-base

test-requires:
	echo flake8 python3-pytest python3-pytest-cov python3-pytest-django python3-pytest-mock

lint:
	flake8 --ignore=E501,E201,E202,E111,E126,E114,E402 --statistics .

test:
	py.test-3 -x --cov=subcontractor --cov-report html --cov-report term -vv subcontractor

.PHONY:: test-blueprints test-requires test

dpkg-blueprints:
	echo ubuntu-focal-base

dpkg-requires:
	echo dpkg-dev debhelper python3-dev python3-setuptools dh-python

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../subcontractor_*.deb):focal

.PHONY:: dpkg-blueprints dpkg-requires dpkg dpkg-file
