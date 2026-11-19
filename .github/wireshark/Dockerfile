FROM ubuntu:26.04 AS build

ARG WIRESHARK_VERSION

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils patch

RUN curl -fsSL "https://www.wireshark.org/download/src/all-versions/wireshark-$WIRESHARK_VERSION.tar.xz" | tar xJ

WORKDIR /wireshark-$WIRESHARK_VERSION

COPY *.patch /patches/

RUN for p in /patches/*.patch; do patch -p1 < "$p"; done

RUN ln -s packaging/debian && \
    DEBIAN_FRONTEND=noninteractive apt-get build-dep -y --no-install-recommends ./

RUN DEB_BUILD_OPTIONS="nocheck parallel=$(nproc)" dpkg-buildpackage -b -us -uc

RUN mkdir /debs && mv /*.deb /debs/ && \
    cd /debs && dpkg-scanpackages . /dev/null > Packages

FROM ubuntu:26.04 AS deps

COPY --from=build /debs /opt/debs

RUN echo "deb [trusted=yes] file:/opt/debs ./" > /etc/apt/sources.list.d/wireshark.list && \
    mkdir -p /deps/partial && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --download-only --no-install-recommends \
        -o Dir::Cache::Archives=/deps tshark

FROM build AS repo

COPY --from=deps /deps/*.deb /debs/

RUN cd /debs && dpkg-scanpackages . /dev/null > Packages

FROM scratch

COPY --from=repo /debs /debs
