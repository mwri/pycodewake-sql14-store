src_dir=code_wake_sql14_store
pkg_meta_src=$(src_dir)/pkg_meta.py

ifndef tests
tests="test"
endif


all: test lint coverage dist

venv: venv/bin/activate venv/lib/.deps

venv/bin/activate:
	python3 -m venv venv

.PHONY: deps
deps: venv/lib/.deps

venv/lib/.deps: venv/bin/activate $(pkg_meta_src)
	. venv/bin/activate \
		&& pip install $$(python3 $(pkg_meta_src) install_requires)
	touch venv/lib/.deps

.PHONY: dev_deps
dev_deps: venv/lib/.dev_deps

venv/lib/.dev_deps: venv/lib/.deps venv/bin/activate $(pkg_meta_src)
	. venv/bin/activate \
		&& pip install $$(python3 $(pkg_meta_src) extras_require dev)
	touch venv/lib/.dev_deps

.PHONY: test
test: venv venv/lib/.dev_deps
	. venv/bin/activate \
		&& pytest \
		-m "$(mark)" \
		$(pytest_args) \
		$(tests)

.PHONY: coverage
coverage: venv venv/lib/.dev_deps
	. venv/bin/activate \
		&& coverage run \
			--branch \
			--source=$(src_dir) --omit=$(pkg_meta_src) \
			-m pytest \
			-m "not soak" \
			$(pytest_args) \
			$(tests) \
		&& coverage report \
		&& coverage html \
		&& coverage xml

.PHONY: format
format: venv venv/lib/.dev_deps
	. venv/bin/activate \
		&& black \
			--line-length 120 \
			$(src_dir) $(tests) setup.py noxfile.py \
		&& isort \
			--profile black \
			$(src_dir) $(tests)

.PHONY: lint
lint: venv venv/lib/.dev_deps
	. venv/bin/activate \
		&& black --check \
			--line-length 120 \
			$(src_dir) $(tests) setup.py noxfile.py \
		&& isort --check \
			--profile black \
			$(src_dir) $(tests)

.PHONY: mypy
mypy: venv venv/lib/.dev_deps
	. venv/bin/activate \
		&& mypy $(src_dir)

.PHONY: clean
clean:
	rm -rf ./venv ./*.egg-info ./build ./pip_dist ./htmlcov ./coverage.xml ./.coverage ./.nox ./.pytest_cache ./.mypy_cache \
		$$(find $(src_dir) -name __pycache__) $$(find $(src_dir) -name '*.pyc') \
		$$(find $(tests) -name __pycache__) $$(find $(tests) -name '*.pyc')

.PHONY: dist
dist: venv
	. venv/bin/activate \
		&& pip install setuptools wheel \
		&& python3 setup.py sdist bdist_wheel
