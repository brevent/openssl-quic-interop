# openssl-quic-interop

Tests QUIC interoperability of OpenSSL clients against nginx, with ngtcp2 as a reference. Runs the full [quic-interop-runner](https://github.com/quic-interop/quic-interop-runner) suite.

| Role | Implementation | Image |
|---|---|---|
| client | `openssl-3.5` | OpenSSL's interop container, branch `openssl-3.5` |
| client | `openssl-master` | OpenSSL's interop container, branch `master` |
| client | `ngtcp2` | The runner's, as a reference |
| server | `nginx` | [`ghcr.io/brevent/nginx-quic-qns`](https://github.com/brevent/nginx-quic-qns/pkgs/container/nginx-quic-qns) |

The workflow runs daily, on push to `main`, and on demand. Failed tests are reported as warnings. A client's job fails only when the runner produces no result.

The summary of each run shows a row of results per test, and each name links to the version tested. The [`results`](../../tree/results) branch keeps the summaries of runs on `main` from the last 7 days. The logs of jobs with failed tests or no result are kept as artifacts for 7 days.

## OpenSSL container

Each run resolves the commits of both branches once and builds OpenSSL at those commits. For `openssl-3.5`, curl is pinned to 8.18.0, the last release with OpenSSL QUIC support. Nothing else is changed.

The container does not support some test cases, such as `multiconnect` (used by `handshakeloss` and `handshakecorruption`) and `keyupdate`, which report `unsupported`.

## ngtcp2 and nginx images

Each run resolves the runner's ngtcp2 image and the nginx image to digests once and tests those digests.
