FROM ghcr.io/initc3/gramine:c04bbae

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ENV VENV_PATH=/root/.venvs/sting

RUN apt-get update && apt-get install -y python3-venv \
    npm 

RUN npm install -g npm@7
RUN npm install -g truffle@5.4.29

RUN python3.10 -m venv $VENV_PATH

RUN pip3 install  \
    web3==5.31.4

WORKDIR /
COPY requirements.txt requirements.txt 

RUN $VENV_PATH/bin/pip install -r requirements.txt 

ARG RA_CLIENT_SPID
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ARG DEBUG=1
ENV DEBUG=$DEBUG
ARG SGX=0
ENV SGX=$SGX

COPY ./ /Sting-Flashbots
WORKDIR /Sting-Flashbots

RUN ./chain/compile.sh

# Setup Builder
WORKDIR /Sting-Flashbots/builder/
RUN mkdir -p input_data output_data enclave_data
RUN cp /Sting-Flashbots/chain/build/contracts/Honeypot.json input_data/
RUN cp -r /Sting-Flashbots/chain/keystores/sting/ input_data/sting/
WORKDIR /Sting-Flashbots/relayer/src/
RUN make SGX=$SGX RA_CLIENT_LINKABLE=0 DEBUG=1 RA_TYPE=epid RA_CLIENT_SPID=${RA_CLIENT_SPID}

# Setup Relayer
WORKDIR /Sting-Flashbots/relayer/
RUN mkdir -p input_data output_data enclave_data
RUN cp /Sting-Flashbots/chain/build/contracts/Honeypot.json input_data/
RUN cp -r /Sting-Flashbots/chain/keystores/relayer/ input_data/relayer/
WORKDIR /Sting-Flashbots/relayer/src/
RUN make SGX=$SGX RA_CLIENT_LINKABLE=0 DEBUG=1 RA_TYPE=epid RA_CLIENT_SPID=${RA_CLIENT_SPID}

WORKDIR /Sting-Flashbots