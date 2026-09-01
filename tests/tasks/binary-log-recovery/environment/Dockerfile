FROM ubuntu:24.04

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        git \
        xxd \
        bsdmainutils \
        coreutils \
        findutils \
        file \
        gcc \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data/logs /output /usr/local/bin

COPY logreader.c /tmp/logreader.c

RUN gcc \
        -O2 \
        -Wall \
        -Wextra \
        -std=c11 \
        /tmp/logreader.c \
        -o /usr/local/bin/logreader \
    && chmod +x /usr/local/bin/logreader \
    && rm /tmp/logreader.c

COPY generate_logs.py /tmp/generate_logs.py

RUN python3 /tmp/generate_logs.py \
    && rm /tmp/generate_logs.py

RUN apt-get purge -y gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN git init /app \
    && git -C /app config user.email "task@askable.local" \
    && git -C /app config user.name "Task Baseline" \
    && git -C /app add -A \
    && git -C /app commit -m "Task baseline" --allow-empty
