#!/usr/bin/env python3
"""
AE-no-S solver.

The cipher is AES with SubBytes (round S-box) AND SubWord (key-schedule S-box)
both replaced by the identity map. Everything left (AddRoundKey, ShiftRows,
MixColumns, key schedule) is GF(2)-linear in (plaintext, key). For a *fixed*
key the map p -> E(p) is affine over GF(2):

        E(p) = M . p  XOR  c        (c = E(0))

We are given:
  - zero:        c = E(0)
  - basis_pairs: E(e_i) for the 128 unit vectors e_i  =>  column i of M = E(e_i) XOR c
  - flag_ct:     3 ciphertext blocks of pkcs7-padded flag

Recover each flag block:   p = M^{-1} . (block XOR c)

Bit convention: a 128-bit block (16 bytes) -> bit vector indexed
bit_index = byte_index*8 + (7 - bit_in_byte), i.e. MSB-first within each byte,
bytes in natural order. So pt "80000...0" (high bit of byte 0) is unit vector e_0,
matching the order of basis_pairs in output.txt.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "..", "files", "extracted", "dist-AE-no-S", "output.txt")


def bytes_to_bits(b):
    """16 bytes -> list of 128 bits, MSB-first per byte."""
    bits = []
    for byte in b:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits):
    """128 bits (MSB-first per byte) -> bytes."""
    out = bytearray()
    for i in range(0, len(bits), 8):
        v = 0
        for j in range(8):
            v = (v << 1) | bits[i + j]
        out.append(v)
    return bytes(out)


def int_from_bits(bits):
    """Pack 128 bits into an int with bit 0 = bits[0] (LSB of int)."""
    v = 0
    for i, bit in enumerate(bits):
        if bit:
            v |= (1 << i)
    return v


def bits_from_int(v, n=128):
    return [(v >> i) & 1 for i in range(n)]


def main():
    with open(OUTPUT) as f:
        data = json.load(f)

    c = bytes.fromhex(data["zero"]["ct"])
    c_bits = bytes_to_bits(c)

    # Build matrix M as 128 columns; each column is a 128-bit int (bit-packed).
    # column i = E(e_i) XOR c  (as a bit vector).
    columns = []
    assert len(data["basis_pairs"]) == 128
    for i, pair in enumerate(data["basis_pairs"]):
        # sanity: pt must be unit vector e_i
        pt_bits = bytes_to_bits(bytes.fromhex(pair["pt"]))
        assert sum(pt_bits) == 1 and pt_bits[i] == 1, f"basis order mismatch at {i}"
        ct_bits = bytes_to_bits(bytes.fromhex(pair["ct"]))
        col_bits = [a ^ b for a, b in zip(ct_bits, c_bits)]
        columns.append(int_from_bits(col_bits))

    # Represent M as rows for Gaussian elimination over GF(2).
    # row r (an int over 128 bits): row_bit i = M[r][i] = bit r of column i.
    rows = []
    for r in range(128):
        row = 0
        for i in range(128):
            if (columns[i] >> r) & 1:
                row |= (1 << i)
        rows.append(row)

    # Invert M over GF(2) via Gauss-Jordan with augmented identity.
    # Each row holds [M_row (128 bits) | I_row (128 bits)] packed in one int,
    # M part in bits 0..127, identity part in bits 128..255.
    aug = []
    for r in range(128):
        aug.append(rows[r] | (1 << (128 + r)))

    for col in range(128):
        # find pivot
        piv = None
        for r in range(col, 128):
            if (aug[r] >> col) & 1:
                piv = r
                break
        if piv is None:
            raise RuntimeError(f"Matrix singular at column {col}")
        aug[col], aug[piv] = aug[piv], aug[col]
        for r in range(128):
            if r != col and (aug[r] >> col) & 1:
                aug[r] ^= aug[col]

    # Extract inverse: Minv rows are the identity part (bits 128..255).
    minv_rows = [(aug[r] >> 128) & ((1 << 128) - 1) for r in range(128)]

    def apply_minv(vec_bits):
        v = int_from_bits(vec_bits)
        res_bits = []
        for r in range(128):
            # dot product mod 2 of minv_rows[r] with v
            res_bits.append(bin(minv_rows[r] & v).count("1") & 1)
        return res_bits

    flag_ct = bytes.fromhex(data["flag_ct"])
    assert len(flag_ct) % 16 == 0
    plaintext = b""
    for off in range(0, len(flag_ct), 16):
        block = flag_ct[off:off + 16]
        rhs_bits = [a ^ b for a, b in zip(bytes_to_bits(block), c_bits)]
        p_bits = apply_minv(rhs_bits)
        plaintext += bits_to_bytes(p_bits)

    print("raw plaintext bytes:", plaintext)
    print("hex:", plaintext.hex())

    # strip pkcs7
    pad = plaintext[-1]
    if 1 <= pad <= 16 and plaintext[-pad:] == bytes([pad]) * pad:
        flag = plaintext[:-pad]
    else:
        flag = plaintext
    try:
        print("FLAG:", flag.decode())
    except UnicodeDecodeError:
        print("FLAG (bytes):", flag)


if __name__ == "__main__":
    main()
