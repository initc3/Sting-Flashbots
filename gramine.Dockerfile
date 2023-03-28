FROM ghcr.io/initc3/gramine:c04bbae

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ARG RA_CLIENT_SPID
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ENV VENV_PATH=/root/.venvs/sting

RUN apt-get update && apt-get install -y python3-venv

RUN python3.10 -m venv $VENV_PATH

COPY ./ /Sting-Flashbots
WORKDIR /Sting-Flashbots
# RUN mkdir -p /Sting-Flashbots/keys
# RUN dd if=/dev/urandom of= /Sting-Flashbots/keys/wrap_key bs=16 count=1

RUN $VENV_PATH/bin/pip install -r requirements.txt 
WORKDIR /Sting-Flashbots/src/builder/sting/

# RUN make SGX=1 RA_CLIENT_LINKABLE=0 DEBUG=1 RA_TYPE=epid RA_CLIENT_SPID=${RA_CLIENT_SPID}
# CMD [ "gramine-sgx ./python enclave/enclave.py" ]