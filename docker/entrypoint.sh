#!/bin/sh
if [ -n "$PROMETHEUS_MULTIPROC_DIR" ]; then
    mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
    rm -rf "${PROMETHEUS_MULTIPROC_DIR:?}"/*
fi

exec "$@"
