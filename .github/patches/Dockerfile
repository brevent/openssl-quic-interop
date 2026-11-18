# Keep only what the client runs, and the libraries they need, of the image
# built by OpenSSL's test/quic-openssl-docker.
ARG BUILDER
FROM ${BUILDER} AS builder
RUN bins="/usr/local/bin/* $(command -v curl || true)" && mkdir /out && \
    cp --parents /run_endpoint.sh $bins /out && \
    for f in $bins; do ldd "$f"; done | \
    awk '$3 ~ /^\// { print $3 }' | sort -u | xargs cp -L --parents -t /out

FROM martenseemann/quic-network-simulator-endpoint:latest
ENV LD_LIBRARY_PATH=/usr/lib64:/usr/lib:/usr/lib/x86_64-linux-gnu
COPY --from=builder /out/ /
