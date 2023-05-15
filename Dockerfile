FROM python:3.9

COPY --from=initc3/geth:97745ba /usr/local/bin/geth /usr/local/bin/geth

RUN apt-get update && apt-get install -y --no-install-recommends \
    npm \
    vim

RUN npm install -g npm@7
RUN npm install -g truffle@5.4.29

RUN pip3 install  \
    web3==5.31.4 \
    ethereum==2.3.2 \
    trie==1.3.8

