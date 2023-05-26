ARCH_LIBDIR ?= /lib/$(shell $(CC) -dumpmachine)

ifeq ($(DEBUG),2)
GRAMINE_LOG_LEVEL = debug
else
GRAMINE_LOG_LEVEL = error
endif

PYTHON ?= python3.10
VENV_PATH ?= ${HOME}/.venvs/sting
VENV_LIB = $(shell ${VENV_PATH}/bin/python -m pip show web3 | grep Location: | cut -d" " -f2)
PY_STLIB = /usr/local/lib/${PYTHON}

RA_TYPE ?= none
RA_CLIENT_SPID ?=
RA_CLIENT_LINKABLE ?= 0

.PHONY: all
all: python.manifest
ifeq ($(SGX),1)
all: python.manifest.sgx python.sig
endif


python.manifest: python.manifest.template
	gramine-manifest \
		-Dlog_level=$(GRAMINE_LOG_LEVEL) \
		-Darch_libdir=$(ARCH_LIBDIR) \
		-Dentrypoint=$(realpath $(shell sh -c "command -v ${VENV_PATH}/bin/${PYTHON}")) \
		-Dra_type=$(RA_TYPE) \
		-Dra_client_spid=$(RA_CLIENT_SPID) \
		-Dra_client_linkable=$(RA_CLIENT_LINKABLE) \
		-Dpython=${PYTHON} \
		-Ddebug=${DEBUG} \
		-Dvenvpath=$(VENV_PATH) \
		$< >$@

# Make on Ubuntu <= 20.04 doesn't support "Rules with Grouped Targets" (`&:`),
# see the helloworld example for details on this workaround.
python.manifest.sgx python.sig: sgx_sign
	@:

.INTERMEDIATE: sgx_sign
sgx_sign: python.manifest
	gramine-sgx-sign \
		--manifest $< \
		--output $<.sgx


.PHONY: clean
clean: reset
	$(RM) *.manifest *.manifest.sgx *.token *.sig OUTPUT* *.PID *.report contract_address
	$(RM) -r /Sting-Flashbots/searcher/src/enclave/__pycache__


.PHONY: reset
reset:
	$(RM) -r /Sting-Flashbots/searcher/enclave_data/* /Sting-Flashbots/searcher/output_data/* /Sting-Flashbots/searcher/input_data/*
