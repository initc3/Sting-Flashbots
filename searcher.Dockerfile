FROM ghcr.io/initc3/gramine:c04bbae

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED 1
ENV VENV_PATH=/root/.venvs/sting

RUN apt-get update && apt-get install -y python3-venv 

RUN python3.10 -m venv $VENV_PATH

RUN pip3 install  \
    web3==5.31.4

ARG RA_CLIENT_SPID
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ARG DEBUG=1
ENV DEBUG=$DEBUG
ARG SGX=1
ENV SGX=$SGX

WORKDIR /
COPY requirements.txt requirements.txt 
RUN $VENV_PATH/bin/pip install -r requirements.txt 

COPY ./searcher /Sting-Flashbots

WORKDIR /Sting-Flashbots
CMD python send_bundle.py 