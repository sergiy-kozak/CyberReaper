# syntax=docker/dockerfile:1

FROM golang:1.16-alpine as builder
ENV REPO="github.com/codesenberg/bombardier"
WORKDIR /app
RUN go mod init bombardier_tmp
RUN go mod edit -replace ${REPO}=github.com/PXEiYyMH8F/bombardier@78-add-proxy-support
RUN go get ${REPO}
RUN CGO_ENABLED=0 go install -v -ldflags '-extldflags "-static"' ${REPO}
RUN /go/bin/bombardier --help


FROM python:3 as tool
WORKDIR /client
COPY src/MHDDoS/requirements.txt /client/MHDDoS/requirements.txt
RUN pip install --no-cache-dir -r MHDDoS/requirements.txt
COPY --from=builder /go/bin/bombardier /root/go/bin/bombardier
COPY src/ /client

ENTRYPOINT [ "python", "./main.py" ]

RUN curl -o MHDDoS/config.json https://raw.githubusercontent.com/Aruiem234/mhddosproxy/main/proxies_config.json
RUN curl -o MHDDoS/files/proxies/proxylist.txt https://raw.githubusercontent.com/porthole-ascend-cinnamon/proxy_scraper/main/proxies.txt
