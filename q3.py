#!python

import socket
import struct
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
import argparse
import re

def select_every_six_bytes(bytes_array, delimiter):
    # This list will hold the result: an array of arrays of bytes
    result = []

    # Length of the bytes_array
    length = len(bytes_array)

    # Iterate over the bytes_array in steps of 7 (6 bytes + 1 delimiter)
    for i in range(0, length, 7):
        # If there are at least 6 bytes left, add them as a sub-array
        if i + 6 <= length:
            result.append(bytes_array[i:i+6])
            # Verify the 7th byte is the delimiter
            if i + 6 < length and bytes_array[i+6] != delimiter:
                raise ValueError("Expected delimiter not found at position {}".format(i+6))

    return result


def get_server_info(ip, port):
    port = int(port)
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.settimeout(0.1)

    try:
        ss.connect((ip, port))
        ss.send(b'\xFF\xFF\xFF\xFFgetstatus')
        dd = ss.recv(5000)
        i = 0
        status = {}
        for e in dd.replace(b'\n',b'').split(b'\\')[1:]:
            e = e.decode('utf-8')
            if i % 2 == 0:
                k = e
            else:
                status[k] = e
            i += 1

        ss.close()
        return (ip, port, status)

    except socket.error:
        ss.close()
        return (ip, port, {})

def get_ip_port(data):
    addr = []
    server_data_array = select_every_six_bytes(data, 0x5c)

    for server_bytes in server_data_array:
        (ip_byte_0, ip_byte_1, ip_byte_2, ip_byte_3, port_byte_0, port_byte_1) = struct.unpack('BBBBBB', server_bytes)
        port = (port_byte_0 << 8) + port_byte_1
        ip = '%d.%d.%d.%d' % (ip_byte_0, ip_byte_1, ip_byte_2, ip_byte_3)
        addr.append((ip, port))

    return addr

def get_server_list(master_server):
    PORT = 27950
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.25)
    s.connect((master_server, PORT))
    s.send(b'\xFF\xFF\xFF\xFFgetservers 68 empty full')

    servers = []

    try:
        while True:
            packet = s.recv(5000)
            prefix = bytes.fromhex("ffffffff67657473657276657273526573706f6e73655c")
            data = packet[len(prefix):]
            servers = servers + get_ip_port(data)

    except socket.timeout:
        s.close()
        return servers

async def get_server_info_async(ip, port, executor):
    # Asynchronous wrapper for the synchronous get_server_info function
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, get_server_info, ip, port)
    return result

async def get_all_server_infos_async(all_servers):
    # This is the renamed asynchronous function
    with ThreadPoolExecutor() as executor:
        tasks = [get_server_info_async(ip, port, executor) for ip, port in all_servers]
        all_server_infos = await asyncio.gather(*tasks)
    return all_server_infos

def get_all_server_infos(all_servers):
    # This is the synchronous function that wraps the asynchronous logic
    return asyncio.run(get_all_server_infos_async(all_servers))

def print_server_info(ip, port, server_info):
    print(f"{ip}:{port}")
    print("------------------------------")
    for (k,v) in server_info.items():
        print(f"{k} : {v}")
    print()

def validate_ip_port(value):
    # Regular expression to validate the ip:port format
    pattern = re.compile(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)$')
    match = pattern.match(value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid format for IP:Port '{value}'. Expected format is ip:port.")

    ip, port_str = match.groups()
    port = int(port_str)

    return (ip, port)

# Create the argument parser
parser = argparse.ArgumentParser(description="Process an optional IP:Port argument.")

# Add the optional positional argument for IP:Port
parser.add_argument("ipport", help="Specify the target in the format ip:port", type=validate_ip_port, nargs='?', default=None)

# Parse the arguments
args = parser.parse_args()

if args.ipport:
    ip, port = args.ipport
    ip, port, server_info = get_server_info(ip, port)
    print_server_info(ip, port, server_info)
else:
    main_list = get_server_list('master.quake3arena.com')
    print(f"Fetched from master.quake3arena.com, server count: {len(main_list)}")

    io_list = get_server_list('master.ioquake3.org')
    print(f"Fetched from master.ioquake3.org, server count: {len(io_list)}")

    union_set = set(main_list) | set(io_list)
    all_servers = list(union_set)
    print(f"Total unique servers: {len(all_servers)}")

    all_server_infos = get_all_server_infos(all_servers)
    responding_server_infos = [server for server in all_server_infos if server[2]]
    print(f"Responding servers: {len(responding_server_infos)}")

    # responding_cpma_server_infos = [server for server in responding_server_infos if server[2].get("game") == "CPMA"]
    # print(f"Responding CPMA servers: {len(responding_cpma_server_infos)}")

    print()

    for (ip, port, server_info) in responding_server_infos:
        print_server_info(ip, port, server_info)
