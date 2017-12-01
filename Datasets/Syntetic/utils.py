#!/usr/bin/env python3

def generate_identifier(x, y = None):
    a = 97
    z = 123
    chars = [str(chr(i)) for i in range(a, z)]

    xx = 1
    idt = ""
    while xx > 0:
        idt = chars[x % (z - a)] + idt
        xx = int(x / (z - a))
        x = xx

    if y is not None:
        return idt + str(y)
    else:
        return idt
