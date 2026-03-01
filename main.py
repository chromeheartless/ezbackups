import time
from datetime import datetime
import json
import hashlib
import subprocess
import threading
import os
import sys





class FileTimestamp:
    def __str__(self):
        now = datetime.now().astimezone()
        return now.strftime("%Y-%m-%d_%H-%M-%S") + f".{now.microsecond // 1000:03d}"

class Timestamp:
    def __str__(self):
        now = datetime.now().astimezone()
        ts = now.strftime("[%Y-%m-%d %H:%M:%S")
        ts += f".{int(now.microsecond/1000):03d}"
        ts += f" {now.strftime('%Z%z')}]"
        return ts


timestamp = Timestamp()
file_timestamp = FileTimestamp()

config_file = "config.json"

def backup_files():


    with open(config_file, "r") as f:
        config = json.load(f)

    hostname = config["remote_hostname"]
    ipaddr = config["remote_host"]
    remote_backup_dir = config["remote_backup_dir"]
    
    keep_days = config["keep_days"]
    keep_backups = config["keep_backups"]
    clear_trash = config["clear_trash"]

    paths = config["paths"]
    ignore_filetypes = config["ignore_filetypes"]


    test_conn = subprocess.run(["ssh", f"{hostname}@{ipaddr}", "echo OK"], capture_output=True, text=True)
    if (test_conn.stdout).strip() == "OK":
        print(f"{timestamp} connection to host works!")

    else:
        print(f"{timestamp} could not establish connection to host!")
        return

    remote_path = f"{remote_backup_dir}/{file_timestamp}"
    subprocess.run(["ssh", f"{hostname}@{ipaddr}", f"mkdir -p {remote_path}"])

    result = subprocess.run(
        ["ssh", f"{hostname}@{ipaddr}", f"ls -1 {remote_backup_dir}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"{timestamp} [!] failed to list remote backups.")
        return

    backups = result.stdout.strip().split("\n")
    backups = [b for b in backups if b]

    backups.sort()

    now = datetime.now()

    to_delete = []

    if keep_backups and len(backups) > keep_backups:
        to_delete.extend(backups[:-keep_backups])

    if keep_days:
        for backup in backups:
            try:
                backup_time = datetime.strptime(backup, "%Y-%m-%d_%H-%M-%S.%f")
                age_days = (now - backup_time).days

                if age_days > keep_days:
                    if backup not in to_delete:
                        to_delete.append(backup)

            except ValueError:
                continue

    for backup in to_delete:
        print(f"{timestamp} removing old backup: {backup}")
        subprocess.run(["ssh", f"{hostname}@{ipaddr}", f"rm -rf {remote_backup_dir}/{backup}"])


    total_files = 0
    total_size_bytes = 0

    for path in paths:
        path = os.path.expanduser(path)

        if os.path.isfile(path):
            total_files += 1
            total_size_bytes += os.path.getsize(path)

        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)

                    if os.path.islink(file_path):
                        continue  # skip symlinks

                    total_files += 1
                    total_size_bytes += os.path.getsize(file_path)

    status_data = {
        "timestamp": str(timestamp),
        "total_files": total_files,
        "total_size_bytes": total_size_bytes
    }


    json_data = json.dumps(status_data, indent=4)

    subprocess.run(["ssh", f"{hostname}@{ipaddr}", f"cat > {remote_path}/status_file.json"], input=json_data, text=True)

    exclude_list = []

    for i in ignore_filetypes:
        exclude_list.append("--exclude")
        exclude_list.append(f"{i}")


    for path in paths:
        try:
            path = os.path.expanduser(path)
            subprocess.run([f"rsync", "-av", *exclude_list, "-e", "ssh", f"{path}", f"{hostname}@{ipaddr}:{remote_path}"])
            print(f"{timestamp} [+] succesfully copied {path} to remote host!")

        except Exception as e:
            print(f"{timestamp} [!] error with copying file path: {path} | {e}")
            return


if __name__ == "__main__":
    backup_files()
