import socket
import struct
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

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

def get_server_infos(all_servers):
    # This is the synchronous function that wraps the asynchronous logic
    return asyncio.run(get_server_infos_async(all_servers))

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
        final_key = None
        for e in dd.split(b'\\')[1:]:
            e = e.decode('utf-8')
            if i % 2 == 0:
                k = e
            else:
                status[k] = e
            final_key = k
            i += 1

        final_value = status[final_key]
        final_lines = final_value.split('\n')
        status[final_key] = final_lines[0]

        if len(final_lines) > 2:
            player_infos = final_lines[1:-1]
            status["_player_info"] = [info.split(" ") for info in player_infos]

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

async def get_server_infos_async(all_servers):
    # This is the renamed asynchronous function
    with ThreadPoolExecutor() as executor:
        tasks = [get_server_info_async(ip, port, executor) for ip, port in all_servers]
        all_server_infos = await asyncio.gather(*tasks)
    return all_server_infos

async def get_server_info_async(ip, port, executor):
    # Asynchronous wrapper for the synchronous get_server_info function
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, get_server_info, ip, port)
    return result

def validate_ip_port(value):
    # Regular expression to validate the ip:port format
    pattern = re.compile(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)$')
    match = pattern.match(value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid format for IP:Port '{value}'. Expected format is ip:port.")

    ip, port_str = match.groups()
    port = int(port_str)

    return (ip, port)

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
