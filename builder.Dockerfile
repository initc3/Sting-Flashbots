ARG GRAMINE_IMG_TAG=dcap-595ba4d
FROM ghcr.io/initc3/gramine:${GRAMINE_IMG_TAG}

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
                libssl-dev \
                gnupg \
                software-properties-common \
                build-essential \
                ca-certificates \
                git \
    && rm -rf /var/lib/apt/lists/*


#install golang
RUN wget https://go.dev/dl/go1.20.3.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin
RUN tar -C /usr/local -xzf go1.20.3.linux-amd64.tar.gz

#clone geth-sgx-gramine
RUN git clone https://github.com/flashbots/geth-sgx-gramine.git /geth-sgx/ && \
        cd /geth-sgx/ && git checkout 34d4a040b220f5402d058f046bfd29c3f7dddf81

# RUN gramine-sgx-gen-private-key -f

WORKDIR /geth-sgx/
ADD builder/geth/geth.manifest.template /geth-sgx/
ADD builder/geth/Makefile /geth-sgx/
ADD builder/geth/geth_init.cpp /geth-sgx/
ADD builder/geth/txpool.go txpool.go

ARG RA_CLIENT_SPID
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ARG RA_CLIENT_LINKABLE
ENV RA_CLIENT_LINKABLE=$RA_CLIENT_LINKABLE
ARG RA_TYPE=epid
ENV RA_TYPE=$RA_TYPE
ARG SGX=1
ENV SGX=$SGX

RUN make SGX=$SGX TLS=1 ENCLAVE_SIZE=4G LOCALNET=1 RA_TYPE=$RA_TYPE

CMD RELAY_SECRET_KEY=0x2e0834786285daccd064ca17f1654f67b4aef298acbb82cef9ec422fb4975622 BUILDER_SECRET_KEY=0x2e0834786285daccd064ca17f1654f67b4aef298acbb82cef9ec422fb4975622 BUILDER_TX_SIGNING_KEY=0x2e0834786285daccd064ca17f1654f67b4aef298acbb82cef9ec422fb4975622 gramine-sgx ./geth
# RUN gramine-sgx-sigstruct-view geth.sig
