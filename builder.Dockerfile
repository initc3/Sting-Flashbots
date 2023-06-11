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
                jq \
    && rm -rf /var/lib/apt/lists/*


#install golang
RUN wget https://go.dev/dl/go1.20.3.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin
RUN tar -C /usr/local -xzf go1.20.3.linux-amd64.tar.gz

#clone geth-sgx-gramine
RUN git clone https://github.com/flashbots/geth-sgx-gramine.git /geth-sgx/ && \
        cd /geth-sgx/ && git checkout 34d4a040b220f5402d058f046bfd29c3f7dddf81

HEALTHCHECK --interval=5s --start-period=360s \
        CMD curl -s -k -X POST https://localhost:8545 -H "Content-Type: application/json" \
        -d "{\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1,\"jsonrpc\":\"2.0\"}" | \
        jq .result | xargs printf "%d" | xargs test 25 -lt

RUN gramine-sgx-gen-private-key -f

WORKDIR /geth-sgx/
ADD builder/geth/geth.manifest.template /geth-sgx/
ADD builder/geth/Makefile /geth-sgx/
ADD builder/geth/geth_init.cpp /geth-sgx/
ADD builder/geth/txpool.go txpool.go
ADD builder/geth/run.sh ./run.sh

ARG RA_CLIENT_SPID
ENV RA_CLIENT_SPID=$RA_CLIENT_SPID
ARG RA_CLIENT_LINKABLE=0
ENV RA_CLIENT_LINKABLE=$RA_CLIENT_LINKABLE
ARG RA_TYPE=dcap
ENV RA_TYPE=$RA_TYPE
ARG SGX=1
ENV SGX=$SGX

ARG LOCALNET=1
ENV LOCALNET=$LOCALNET
ARG ENCLAVE_SIZE=4G
ENV ENCLAVE_SIZE=$ENCLAVE_SIZE
ARG SEPOLIA=0
ENV SEPOLIA=$SEPOLIA
ARG MAINNET=0
ENV MAINNET=$MAINNET

RUN make TLS=1

WORKDIR /geth-sgx/go-ethereum
RUN go mod download
RUN go run build/ci.go install -static ./cmd/geth
RUN cp /geth-sgx/go-ethereum/build/bin/geth /usr/local/bin/

WORKDIR /geth-sgx/

CMD ./run.sh
# CMD gramine-sgx ./geth
# RUN gramine-sgx-sigstruct-view geth.sig
