#!/bin/bash
# Download new marked.min.js
D=$(dirname $0)
cd $D
echo Before:
./versions.sh
echo
echo cp marked.min.js marked.min.js.bk.$(date +%Y%m%d-%H%M%S) | bash -x
echo
echo curl -LO https://cdn.jsdelivr.net/npm/marked/marked.min.js | bash -x
echo
echo After:
./versions.sh
