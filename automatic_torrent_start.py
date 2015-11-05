import subprocess

from environment import environment


def run_qbittorrent(torrent_files_list):
    command_string = environment.get('qBittorrent_location') + ' --no-splash '
    command_string += " ".join(torrent_files_list)
    return subprocess.call(command_string)
