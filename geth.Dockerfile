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
ADD builder/geth/txpool.go /go-ethereum/core/txpool/txpool.go

RUN go mod download
RUN go run build/ci.go install -static ./cmd/geth

# Pull Geth into a second stage deploy alpine container
FROM alpine:latest

RUN apk add --no-cache ca-certificates jq curl
COPY --from=builder /go-ethereum/build/bin/geth /usr/local/bin/

HEALTHCHECK --interval=5s --start-period=360s \
        CMD curl -s -X POST http://localhost:8545 -H "Content-Type: application/json" \
        -d "{\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1,\"jsonrpc\":\"2.0\"}" | \
        jq .result | xargs printf "%d" | xargs test 25 -lt

EXPOSE 8545 8546 30303 30303/udp
ENTRYPOINT ["geth"]

# Add some metadata labels to help programatic image consumption
ARG COMMIT=""
ARG VERSION=""
ARG BUILDNUM=""

LABEL commit="$COMMIT" version="$VERSION" buildnum="$BUILDNUM"
