#!python
import subprocess
import time

import q3

def new_players(previous, current):
    previous_set = set(previous)
    current_set = set(current)
    new_players_set = current_set - previous_set
    return list(new_players_set)

def notify(title, text):
    script = f'display notification "{text}" with title "{title}" sound name "Submarine"'
    subprocess.run(["osascript", "-e", script])

server_db = {}

while True:
    print(f"Checking servers")
    main_list = q3.get_server_list('master.quake3arena.com')
    io_list = q3.get_server_list('master.ioquake3.org')
    union_set = set(main_list) | set(io_list)
    all_servers = list(union_set)
    all_server_infos = q3.get_server_infos(all_servers)
    responding_server_infos = [server for server in all_server_infos if server[2]]
    responding_cpma_server_infos = [server for server in responding_server_infos if server[2].get("game") == "CPMA"]

    print(f"Responding CPMA servers: {len(responding_cpma_server_infos)}")

    for (ip, port, server_info) in responding_cpma_server_infos:
        previous_info = server_db.get((ip, port))

        if previous_info:
            previous_players = q3.human_player_list(previous_info)
            current_players = q3.human_player_list(server_info)
            new_players_list = new_players(previous_players, current_players)
            if len(new_players_list) > 0:
                notify(
                    "New player detected",
                    f"{ip}:{port}\n{q3.remove_color_declarations(server_info.get('sv_hostname'))}\n{', '.join(new_players_list)}"
                )
                print(f"New players detected on {ip}:{port} {q3.remove_color_declarations(server_info.get('sv_hostname'))}")
                print(new_players_list)
        else:
            human_players = q3.human_player_list(server_info)
            if len(human_players) > 0:
                notify(
                    "Scanned cpma server with humans",
                    f"{ip}:{port}\n{q3.remove_color_declarations(server_info.get('sv_hostname'))}\n{', '.join(human_players)}"
                )
                print(f"Scanned cpma server with humans {ip}:{port} {q3.remove_color_declarations(server_info.get('sv_hostname'))}")
                print(human_players)

        server_db[(ip, port)] = server_info

    print("Waiting 30 seconds to rescan...")
    time.sleep(30)
