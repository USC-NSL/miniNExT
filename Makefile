VERSION = 1.4.0

MININEXT = mininext
EXAMPLEDIR = examples
EXAMPLES = quagga-ixp
PYSRC = $(MININEXT)/*.py $(MININEXT)/services/*.py
PYSRC += $(addprefix $(MININEXT)/$(EXAMPLEDIR)/, $(EXAMPLES)/*.py)

MXEXEC = mxexec
INSTALLBINS = $(MXEXEC)
MANPAGES = mxexec.1

BINDIR = /usr/bin
MANDIR = /usr/share/man/man1

DEPS = help2man python-setuptools python-pip
DEVELDEPS = $(DEPS) pyflakes pylint

AUTOPEPOPTS = --in-place --aggressive --aggressive 
P8IGNORE = 
LINTIGNORE = C0103,R0904

CFLAGS += -Wall -Wextra

all:

clean:
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.*~" -delete
	rm -rf build dist $(MXEXEC) $(MANPAGES) $(DOCDIRS)

codecheck: $(PYSRC)
	@echo "Running code check"
	pyflakes $(PYSRC)
	pep8 --repeat --ignore=$(P8IGNORE) $(PYSRC)
	pylint --disable=$(LINTIGNORE) $(PYSRC)

errcheck: $(PYSRC)
	@echo "Running check for errors only"
	pyflakes $(PYSRC)
	pylint -E $(PYSRC)
	
codeformat: $(PYSRC)
	@echo "Formatting code with autopep8"
	autopep8 $(AUTOPEPOPTS) $(PYSRC)

mxexec: mxexec.c
	cc $(CFLAGS) $(LDFLAGS) -DVERSION=\"$(VERSION)\" $< -o $@

install: $(INSTALLBINS) $(MANPAGES)
	install $(INSTALLBINS) $(BINDIR)
	install $(MANPAGES) $(MANDIR)
	python setup.py install

uninstall:
	rm -f $(addprefix $(BINDIR)/, $(INSTALLBINS))
	rm -f $(addprefix $(MANDIR)/, $(MANPAGES))
	pip uninstall mininext
.PHONY: uninstall

deps:
	@echo $(DEPS)
.PHONY: deps

develdeps:
	@echo $(DEVELDEPS)
.PHONY: develdeps

develop: $(INSTALLBINS) $(MANPAGES)
	install $(INSTALLBINS) $(BINDIR)
	install $(MANPAGES) $(MANDIR)
	python setup.py develop

undevelop:
	rm -f $(addprefix $(BINDIR)/, $(INSTALLBINS))	
	rm -f $(addprefix $(MANDIR)/, $(MANPAGES))
	python setup.py develop --uninstall
.PHONY: undevelop

man: $(MANPAGES)

mxexec.1: mxexec
	help2man -N -n "execution utility for MiniNExT (MiniNet ExTended)." \
	-h "-h" -v "-v" --no-discard-stderr ./$< -o $@ 

.PHONY: doc

doc: man
	doxygen doc/doxygen.cfg
	make -C doc/latex
