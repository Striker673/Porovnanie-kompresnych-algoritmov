import struct

MIN_RUN = 3
MAX_RUN = 255
ESCAPE = 0xFF


def compress(data):
    if not data:
        return b""

    out = bytearray(struct.pack(">I", len(data)))

    i = 0
    n = len(data)
    while i < n:
        current = data[i]
        run = 1
        while i + run < n and data[i + run] == current and run < MAX_RUN:
            run += 1

        if run >= MIN_RUN:
            out.append(ESCAPE)
            out.append(run)
            out.append(current)
        else:
            for _ in range(run):
                if current == ESCAPE:
                    # musíme escapnúť aj samotný escape byte
                    out.append(ESCAPE)
                    out.append(1)
                    out.append(ESCAPE)
                else:
                    out.append(current)

        i += run

    return bytes(out)


def decompress(data):
    if not data:
        return b""

    (original_size,) = struct.unpack_from(">I", data, 0)
    offset = 4

    out = bytearray()
    while offset < len(data):
        b = data[offset]
        offset += 1
        if b == ESCAPE:
            if offset + 1 >= len(data):
                break
            count = data[offset]
            value = data[offset + 1]
            offset += 2
            out.extend(bytes([value]) * count)
        else:
            out.append(b)

    return bytes(out[:original_size])
