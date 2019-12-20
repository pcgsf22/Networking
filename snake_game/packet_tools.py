#!/usr/bin/env python
# coding: utf-8
import struct


def pack(message_type, *args):
    """ Pack all messages"""
    if message_type == 7:
        return map_pack(message_type, args[0], args[1], args[2], args[3], args[4])
    elif message_type <= 3:
        return client_pack(message_type, args[0], args[1], args[2])
    elif message_type == 6:
        return server_pack(message_type, args[0], args[1])
    else:
        return struct.pack("!B", message_type)


def client_pack(message_type, ID, name, op_code):
    """ Pack client messages
    """
    format_string = "!BBB{}s{}sH"
    if message_type == 3:
        format_string = "!BBB{}s{}sB"
    return struct.pack(format_string.format(len(ID), len(name)), message_type, len(ID), len(name), ID, name, op_code)


def server_pack(message_type, result, name):
    """ Pack server messages
    """
    return struct.pack("!BBB{}s".format(len(name)), message_type, result, len(name), name)


def set_x(bit_num, x_val):
    """ Set x value of the server
    """
    x_val = 31 - x_val
    bit_num |= (1 << x_val)
    return bit_num


def to_bitmap(pos_list):
    """ Convert position list to bitmap
    """
    bit_list = [0]*32
    for x, y in pos_list:
        bit_list[y] = set_x(bit_list[y], x)
    return bit_list


def map_pack(message_type, seq_num, apple_row, apple_col, pos_list1, pos_list2):
    """ Pack bitmap information
    """
    bitmap1 = to_bitmap(pos_list1)
    bitmap2 = to_bitmap(pos_list2)
    encoded = struct.pack("!BBBB", message_type, seq_num, apple_row, apple_col)
    for num in bitmap1:
        encoded += struct.pack("!I", num)
    for num in bitmap2:
        encoded += struct.pack("!I", num)
    return encoded


def map_unpack(message):
    """ Unpack bitmap information
    """
    bitset_format = "!BBBB" + "I"*64
    unpacked = struct.unpack(bitset_format, message)
    return unpacked[0], unpacked[1], unpacked[2], unpacked[3], unpacked[4:36], unpacked[36:]


def unpack(message):
    format_type, = struct.unpack_from("!B", message)
    if format_type == 7:
        return map_unpack(message)
    if 3 < format_type < 6:
        return struct.unpack("!B", message)
    message = message[1:]
    int_a, len_name = struct.unpack_from("!BB", message)
    message = message[2:]
    if format_type == 6:
        return format_type, int_a, message
    res_format = "!{}s{}sH"
    if format_type == 3:
        res_format = "!{}s{}sB"
    ip, name, number = struct.unpack_from(
        res_format.format(int_a, len_name), message)

    return format_type, ip, name, number
