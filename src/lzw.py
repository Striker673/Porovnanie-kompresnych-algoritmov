import struct

MAX_DICT_SIZE = 4096


def compress(data):
    if not data:
        return b""

    dictionary = {bytes([i]): i for i in range(256)}
    next_code = 256

    codes = []
    current = bytes([data[0]])

    for i in range(1, len(data)):
        current_plus = current + bytes([data[i]])
        if current_plus in dictionary:
            current = current_plus
        else:
            codes.append(dictionary[current])
            if next_code < MAX_DICT_SIZE:
                dictionary[current_plus] = next_code
                next_code += 1
            current = bytes([data[i]])

    codes.append(dictionary[current])

    out = struct.pack(">I", len(codes))
    for code in codes:
        out += struct.pack(">H", code)
    return out


def decompress(data):
    if not data:
        return b""

    offset = 0
    (num_codes,) = struct.unpack_from(">I", data, offset)
    offset += 4

    codes = []
    for _ in range(num_codes):
        (code,) = struct.unpack_from(">H", data, offset)
        codes.append(code)
        offset += 2

    if not codes:
        return b""

    dictionary = {i: bytes([i]) for i in range(256)}
    next_code = 256

    result = bytearray(dictionary[codes[0]])
    previous = dictionary[codes[0]]

    for i in range(1, len(codes)):
        code = codes[i]
        if code in dictionary:
            entry = dictionary[code]
        elif code == next_code:
            # špeciálny prípad - kód sa referencuje na seba (cScSc vzor)
            entry = previous + bytes([previous[0]])
        else:
            raise ValueError(f"Neplatný LZW kód: {code}")

        result.extend(entry)

        if next_code < MAX_DICT_SIZE:
            dictionary[next_code] = previous + bytes([entry[0]])
            next_code += 1

        previous = entry

    return bytes(result)
