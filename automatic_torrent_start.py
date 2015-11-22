import shlex
import subprocess

# from environment_local import environment
from environment import environment

def run_qbittorrent(torrent_files_list):
    command_string = environment.get('qBittorrent_location') + ' --daemon --webui-port=8081 '
    command_string += " ".join(torrent_files_list)
    print command_string
    return subprocess.Popen(shlex.split(command_string))
