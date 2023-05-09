# Support setting various labels on the final image
ARG COMMIT=""
ARG VERSION=""
ARG BUILDNUM=""

# Build Geth in a stock Go builder container
FROM golang:1.20-alpine as builder

RUN apk add --no-cache gcc musl-dev linux-headers git


RUN git clone https://github.com/flashbots/builder.git /go-ethereum

WORKDIR /go-ethereum
ARG GETH_COMMIT
RUN git checkout $GETH_COMMIT
ADD go-ethereum-new/miner/worker.go /go-ethereum/miner/worker.go
ADD go-ethereum-new/les/api_backend.go /go-ethereum/les/api_backend.go
ADD go-ethereum-new/internal/ethapi/api.go /go-ethereum/internal/ethapi/api.go
ADD builder/geth/txpool.go /go-ethereum/core/txpool/txpool.go

RUN go mod download
RUN go run build/ci.go install -static ./cmd/geth

# Pull Geth into a second stage deploy alpine container
FROM alpine:latest

RUN apk add --no-cache ca-certificates
COPY --from=builder /go-ethereum/build/bin/geth /usr/local/bin/

EXPOSE 8545 8546 30303 30303/udp
ENTRYPOINT ["geth"]

# Add some metadata labels to help programatic image consumption
ARG COMMIT=""
ARG VERSION=""
ARG BUILDNUM=""

LABEL commit="$COMMIT" version="$VERSION" buildnum="$BUILDNUM"
