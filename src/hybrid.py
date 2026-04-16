import struct
import huffman
import lzw
import rle


def compress_rle_huffman(data):
    if not data:
        return b""
    rle_out = rle.compress(data)
    huff_out = huffman.compress(rle_out)
    return struct.pack(">BI", 0x01, len(rle_out)) + huff_out


def decompress_rle_huffman(data):
    if not data:
        return b""
    # preskočíme 5B hlavičku (marker + rle_size)
    rle_out = huffman.decompress(data[5:])
    return rle.decompress(rle_out)


def compress_lzw_huffman(data):
    if not data:
        return b""
    lzw_out = lzw.compress(data)
    huff_out = huffman.compress(lzw_out)
    return struct.pack(">BI", 0x02, len(lzw_out)) + huff_out


def decompress_lzw_huffman(data):
    if not data:
        return b""
    lzw_out = huffman.decompress(data[5:])
    return lzw.decompress(lzw_out)
