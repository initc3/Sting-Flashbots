ARG GRAMINE_IMG_TAG=dcap-595ba4d
FROM ghcr.io/initc3/gramine:${GRAMINE_IMG_TAG}

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ENV VENV_PATH=/root/.venvs/sting

RUN apt-get update && apt-get install -y python3-venv 

RUN python3.10 -m venv $VENV_PATH

WORKDIR /
COPY requirements.txt requirements.txt 
RUN pip install -r requirements.txt 
RUN $VENV_PATH/bin/pip install -r requirements.txt 

RUN pip install git+https://github.com/initc3/auditee.git
RUN $VENV_PATH/bin/pip install git+https://github.com/initc3/auditee.git

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


ARG RA_TYPE=dcap
ENV RA_TYPE=$RA_TYPE
ARG RA_CLIENT_SPID
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ARG RA_CLIENT_LINKABLE=0
ENV RA_CLIENT_LINKABLE=$RA_CLIENT_LINKABLE

ARG DEBUG=1
ENV DEBUG=$DEBUG
ARG SGX=0
ENV SGX=$SGX

ADD ./searcher/ /Sting-Flashbots/searcher

WORKDIR /Sting-Flashbots/searcher
RUN mkdir -p input_data output_data enclave_data

WORKDIR /Sting-Flashbots/searcher/src
RUN make SGX=$SGX RA_CLIENT_LINKABLE=$RA_CLIENT_LINKABLE DEBUG=$DEBUG RA_TYPE=$RA_TYPE RA_CLIENT_SPID=$RA_CLIENT_SPID

CMD [ "./run.sh" ]