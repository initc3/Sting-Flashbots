FROM ghcr.io/initc3/gramine:c04bbae

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ENV VENV_PATH=/root/.venvs/sting

RUN apt-get update && apt-get install -y python3-venv 

RUN python3.10 -m venv $VENV_PATH

RUN pip3 install  \
    web3==5.31.4 \
    pyopenssl==23.1.1

ARG RA_TYPE=dcap
ENV RA_TYPE=$RA_TYPE
ARG RA_CLIENT_SPID
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ARG DEBUG=1
ENV DEBUG=$DEBUG
ARG SGX=1
ENV SGX=$SGX

WORKDIR /
COPY requirements.txt requirements.txt 
RUN pip install -r requirements.txt 
RUN $VENV_PATH/bin/pip install -r requirements.txt 


COPY ./searcher/src/enclave/lib/ecdsa/account.py /usr/local/lib/python3.10/site-packages/eth_account/account.py
COPY ./searcher/src/enclave/lib/ecdsa/signing.py /usr/local/lib/python3.10/site-packages/eth_account/_utils/signing.py
COPY ./searcher/src/enclave/lib/ecdsa/datatypes.py /usr/local/lib/python3.10/site-packages/eth_keys/datatypes.py
COPY ./searcher/src/enclave/lib/ecdsa/main.py /usr/local/lib/python3.10/site-packages/eth_keys/backends/native/main.py
COPY ./searcher/src/enclave/lib/ecdsa/ecdsa.py /usr/local/lib/python3.10/site-packages/eth_keys/backends/native/ecdsa.py

COPY ./searcher/src/enclave/lib/ecdsa/account.py $VENV_PATH/lib/python3.10/site-packages/eth_account/account.py
COPY ./searcher/src/enclave/lib/ecdsa/signing.py $VENV_PATH/lib/python3.10/site-packages/eth_account/_utils/signing.py
COPY ./searcher/src/enclave/lib/ecdsa/datatypes.py $VENV_PATH/lib/python3.10/site-packages/eth_keys/datatypes.py
COPY ./searcher/src/enclave/lib/ecdsa/main.py $VENV_PATH/lib/python3.10/site-packages/eth_keys/backends/native/main.py
COPY ./searcher/src/enclave/lib/ecdsa/ecdsa.py $VENV_PATH/lib/python3.10/site-packages/eth_keys/backends/native/ecdsa.py

# ADD /Sting-Flashbots/chain/contracts/HoneyPot.json /Sting-Flashbots/searcher/input_data/

ADD ./searcher/ /Sting-Flashbots/searcher

WORKDIR /Sting-Flashbots/searcher
RUN mkdir -p input_data output_data enclave_data

WORKDIR /Sting-Flashbots/searcher/src
RUN make SGX=$SGX RA_CLIENT_LINKABLE=0 DEBUG=1 RA_TYPE=epid RA_CLIENT_SPID=${RA_CLIENT_SPID}