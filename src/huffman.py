import heapq
import struct
from collections import Counter


class HuffmanNode:
    def __init__(self, byte=None, freq=0, left=None, right=None):
        self.byte = byte
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq

    def is_leaf(self):
        return self.left is None and self.right is None


def build_tree(freq):
    if not freq:
        return None

    if len(freq) == 1:
        byte, count = next(iter(freq.items()))
        # edge case - single symbol, tree musí mať aspoň 1 hranu
        return HuffmanNode(left=HuffmanNode(byte=byte, freq=count))

    heap = [HuffmanNode(byte=b, freq=f) for b, f in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        heapq.heappush(heap, HuffmanNode(freq=left.freq + right.freq, left=left, right=right))

    return heap[0]


def build_codes(node, prefix="", codes=None):
    if codes is None:
        codes = {}
    if node is None:
        return codes
    if node.is_leaf():
        codes[node.byte] = prefix if prefix else "0"
        return codes
    build_codes(node.left, prefix + "0", codes)
    build_codes(node.right, prefix + "1", codes)
    return codes


def compress(data):
    if not data:
        return b""

    freq = Counter(data)
    tree = build_tree(freq)
    codes = build_codes(tree)

    out = struct.pack(">I", len(freq))
    for byte_val, count in freq.items():
        out += struct.pack(">BI", byte_val, count)

    bit_string = "".join(codes[b] for b in data)
    padding = (8 - len(bit_string) % 8) % 8
    bit_string += "0" * padding
    out += struct.pack(">B", padding)

    for i in range(0, len(bit_string), 8):
        out += bytes([int(bit_string[i:i + 8], 2)])

    return out


def decompress(data):
    if not data:
        return b""

    offset = 0
    (num_symbols,) = struct.unpack_from(">I", data, offset)
    offset += 4

    freq = {}
    for _ in range(num_symbols):
        byte_val, count = struct.unpack_from(">BI", data, offset)
        freq[byte_val] = count
        offset += 5

    total = sum(freq.values())
    tree = build_tree(freq)
    if tree is None:
        return b""

    (padding,) = struct.unpack_from(">B", data, offset)
    offset += 1

    bit_string = "".join(format(data[i], "08b") for i in range(offset, len(data)))
    if padding > 0:
        bit_string = bit_string[:-padding]

    result = bytearray()
    node = tree
    for bit in bit_string:
        node = node.left if bit == "0" else node.right
        if node.is_leaf():
            result.append(node.byte)
            node = tree
            if len(result) == total:
                break

    return bytes(result)
