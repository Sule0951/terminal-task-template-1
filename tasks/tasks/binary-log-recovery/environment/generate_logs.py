#!/usr/bin/env python3

import os
import struct


def checksum(data: bytes) -> int:
    return sum(data) & 0xFFFFFFFF


def write_record(
    endian: str,
    seq: int,
    ts: int,
    typ: str,
    payload: bytes,
) -> bytes:
    type_bytes = typ.encode("ascii")

    record = struct.pack(endian + "II", seq, ts)
    record += bytes([len(type_bytes)])
    record += type_bytes
    record += struct.pack(endian + "H", len(payload))
    record += payload
    record += struct.pack(endian + "I", checksum(record))

    return record


def write_log(
    path: str,
    version: int,
    records: list[tuple[int, int, str, bytes]],
    *,
    declared_count: int | None = None,
    truncate_bytes: int = 0,
) -> None:
    endian = "<" if version == 1 else ">"

    if declared_count is None:
        declared_count = len(records)

    header = (
        b"EVLG"
        + bytes([version])
        + struct.pack(endian + "I", declared_count)
    )

    body = b"".join(
        write_record(endian, seq, ts, typ, payload)
        for seq, ts, typ, payload in records
    )

    data = header + body

    if truncate_bytes:
        if truncate_bytes >= len(data):
            raise ValueError("truncation removes entire file")
        data = data[:-truncate_bytes]

    with open(path, "wb") as f:
        f.write(data)


def corrupt_checksum(
    record: bytes,
    endian: str,
    value: int,
) -> bytes:
    return record[:-4] + struct.pack(endian + "I", value)


os.makedirs("/data/logs", exist_ok=True)


# ------------------------------------------------------------
# Valid little-endian records.
# ------------------------------------------------------------

write_log(
    "/data/logs/clean_le.log",
    1,
    [
        (1, 1693500000, "LOGIN", bytes.fromhex("deadbeef")),
        (2, 1693500001, "LOGOUT", bytes.fromhex("cafebabe")),
        (3, 1693500002, "DATA", bytes.fromhex("01020304")),
        (4, 1693500003, "PING", bytes.fromhex("ff")),
    ],
)


# ------------------------------------------------------------
# Valid big-endian records.
# ------------------------------------------------------------

write_log(
    "/data/logs/clean_be.log",
    2,
    [
        (10, 1693500100, "LOGIN", bytes.fromhex("aabbccdd")),
        (11, 1693500101, "ERROR", bytes.fromhex("11223344")),
        (12, 1693500102, "PONG", bytes.fromhex("00")),
    ],
)


# ------------------------------------------------------------
# More valid records.
# ------------------------------------------------------------

write_log(
    "/data/logs/secondary_le.log",
    1,
    [
        (50, 1693500500, "START", bytes.fromhex("0a0b0c")),
        (51, 1693500501, "STOP", bytes.fromhex("0d0e0f")),
        (52, 1693500502, "INFO", bytes.fromhex("112233445566")),
    ],
)


write_log(
    "/data/logs/secondary_be.log",
    2,
    [
        (70, 1693500700, "OPEN", bytes.fromhex("a1")),
        (71, 1693500701, "CLOSE", bytes.fromhex("b2")),
    ],
)


# ------------------------------------------------------------
# Records deliberately interleaved by sequence number.
# ------------------------------------------------------------

write_log(
    "/data/logs/interleaved.log",
    1,
    [
        (20, 1693500200, "A", bytes.fromhex("1111")),
        (21, 1693500201, "B", bytes.fromhex("2222")),
    ],
)


# ------------------------------------------------------------
# Wrong checksum, little-endian.
# ------------------------------------------------------------

bad_le = write_record(
    "<",
    30,
    1693500300,
    "BAD",
    bytes.fromhex("ff00ff00"),
)

bad_le = corrupt_checksum(
    bad_le,
    "<",
    0xDEADBEEF,
)

with open("/data/logs/bad_checksum_le.log", "wb") as f:
    f.write(
        b"EVLG"
        + bytes([1])
        + struct.pack("<I", 1)
        + bad_le
    )


# ------------------------------------------------------------
# Wrong checksum, big-endian.
# ------------------------------------------------------------

bad_be = write_record(
    ">",
    31,
    1693500301,
    "BAD2",
    bytes.fromhex("cafed00d"),
)

bad_be = corrupt_checksum(
    bad_be,
    ">",
    0x12345678,
)

with open("/data/logs/bad_checksum_be.log", "wb") as f:
    f.write(
        b"EVLG"
        + bytes([2])
        + struct.pack(">I", 1)
        + bad_be
    )


# ------------------------------------------------------------
# Valid record followed by incomplete record.
# ------------------------------------------------------------

valid_prefix = write_record(
    "<",
    40,
    1693500400,
    "OK",
    bytes.fromhex("00"),
)

partial = write_record(
    "<",
    41,
    1693500401,
    "PARTIAL",
    bytes.fromhex("abcdef"),
)

with open("/data/logs/truncated_tail.log", "wb") as f:
    f.write(
        b"EVLG"
        + bytes([1])
        + struct.pack("<I", 2)
        + valid_prefix
        + partial[:-3]
    )


# ------------------------------------------------------------
# Header claims more records than physically exist.
# ------------------------------------------------------------

only_record = write_record(
    "<",
    60,
    1693500600,
    "ONE",
    bytes.fromhex("aa"),
)

with open("/data/logs/overcount.log", "wb") as f:
    f.write(
        b"EVLG"
        + bytes([1])
        + struct.pack("<I", 5)
        + only_record
    )


# ------------------------------------------------------------
# Valid zero-record log.
# ------------------------------------------------------------

with open("/data/logs/zero_records.log", "wb") as f:
    f.write(
        b"EVLG"
        + bytes([1])
        + struct.pack("<I", 0)
    )


# ------------------------------------------------------------
# Empty file.
# ------------------------------------------------------------

open("/data/logs/empty.log", "wb").close()


# ------------------------------------------------------------
# Invalid magic.
# ------------------------------------------------------------

with open("/data/logs/bad_magic.log", "wb") as f:
    f.write(
        b"XXXX"
        + bytes([1])
        + struct.pack("<I", 1)
    )


# ------------------------------------------------------------
# Unsupported version.
# ------------------------------------------------------------

with open("/data/logs/unknown_version.log", "wb") as f:
    f.write(
        b"EVLG"
        + bytes([99])
        + struct.pack("<I", 1)
    )


print("Generated binary log corpus.")
