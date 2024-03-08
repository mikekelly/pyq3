#!python

import argparse

import q3

def print_server_info(ip, port, server_info):
    print(f"{ip}:{port}")
    print("------------------------------")
    for (k,v) in server_info.items():
        print(f"{k} : {v}")
    print()

# Create the argument parser
parser = argparse.ArgumentParser(description="Process an optional IP:Port argument.")

# Add the optional positional argument for IP:Port
parser.add_argument("ipport", help="Specify the target in the format ip:port", type=q3.validate_ip_port, nargs='?', default=None)

# Parse the arguments
args = parser.parse_args()

if args.ipport:
    ip, port = args.ipport
    ip, port, server_info = q3.get_server_info(ip, port)
    print_server_info(ip, port, server_info)
else:
    main_list = q3.get_server_list('master.quake3arena.com')
    print(f"Fetched from master.quake3arena.com, server count: {len(main_list)}")

    io_list = q3.get_server_list('master.ioquake3.org')
    print(f"Fetched from master.ioquake3.org, server count: {len(io_list)}")

    union_set = set(main_list) | set(io_list)
    all_servers = list(union_set)
    print(f"Total unique servers: {len(all_servers)}")

    all_server_infos = q3.get_server_infos(all_servers)
    responding_server_infos = [server for server in all_server_infos if server[2]]
    print(f"Responding servers: {len(responding_server_infos)}")

    # responding_cpma_server_infos = [server for server in responding_server_infos if server[2].get("game") == "CPMA"]
    # print(f"Responding CPMA servers: {len(responding_cpma_server_infos)}")

    print()

    for (ip, port, server_info) in responding_server_infos:
        print_server_info(ip, port, server_info)
