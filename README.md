
# ezbackups

![top logo](cover-image.png)

Simple backup utility I wrote for my Pi within like a day.


## Git looked too hard to setup, so I wrote my own.

I have a Raspberry Pi 5, and I wanted to use it as a backup machine. More specifically, I wanted to back up my `~/code` folder and my `~/.config` folder with a simple command. I realized I didn’t need any version control or fancy Git features, just a simple way to quickly back up all my files while keeping everything organized and easy to look through.

Yes, I could just `scp -r` two folders, but why spend 4 seconds doing something when you can spend 2 hours automating it?

(Also, I could’ve made this in bash, but Python is easier for me.)

## How to use it (why would you even use this...)

The program is configured through one config file (I didn’t want to use args or other methods of specifying paths every single time).

Edit the `config.json` file and select which files/directories you want it to back up, along with the information of the device you’ll be sending your files to.

Example config.json:

``` json
{
    "remote_hostname": "pi",
    "remote_host": "192.168.1.42",
    "remote_backup_dir": "~/backups",

    "keep_days": 3,
    "keep_backups": 10,
    "clear_trash": true,

    "paths": [
        "~/Documents/code",
        "~/.config"
    ],

    "ignore_filetypes": [
        "__pycache__",
        ".log"
    ]
}
```


- `remote_hostname` is the hostname of your machine (by default it’s `raspberrypi` on a Pi).
- `remote_host` is the IP address of that machine on your network.
- `remote_backup_dir` is the directory where the machine will store your backup folders.
- `keep_days` is the number of days you want to keep backups for. The script looks at timestamps and removes anything older than this.
- `keep_backups` is the maximum total number of backups allowed in the backup folder. I recommend keeping at least two.
- `clear_trash` is mostly decorative, since we’re doing rm -rf {dir} anyway, but it fits nicely.
- `paths` is a list of paths you want to back up from your machine.
- `ignore_filetypes` works like a `.gitignore`, it ignores folders and file types listed here (within the specified paths).

This demo config will run something like:

``` bash
ssh pi@192.168.1.42 echo OK                                                                                         (test connection)

ssh pi@192.168.1.42 ls -1 ~/backups                                                                                 (get existing backup folders)

(runs a check to see if keep_days or keep_backups limits are exceeded, and removes if needed)

ssh pi@192.168.1.42 mkdir ~/backups/timestamp                                                                       (create timestamped directory)
ssh pi@192.168.1.42 cat > ~/backups/timestamp/status_file.json                                                      (create + write a simple status file)
rsync -av --exclude '__pycache__' --exclude '.log' -e ssh -r ~/Documents/code pi@192.168.1.45:~/backups/timestamp   (copy first folder)
rsync -av --exclude '__pycache__' --exclude '.log' -e ssh ~/.config pi@192.168.1.45:~/backups/timestamp             (copy second folder)
```

`os.path.expanduser()` expands `"~"` to an absolute path, so feel free to use paths relative to `"~"` (on your machine).

Also, `remote_backup_dir` (`~/backups` in this case) doesn’t have to exist, rsync can create it, but the `mkdir` call is necessary because it can create one folder, not two nested ones at the same time. If the remote backup directory doesn’t exist, it needs to create both the backups folder and the timestamp child folder.


## SSH setup

For this to work smoothly, you need a passwordless way to copy files over SSH. The simplest way is to generate a new ed25519 keypair yourself (doing it via subprocess wouldn’t work since you need to enter your password once).

1. Generate a key on your machine:

```
ssh-keygen -t ed25519
```

You can just press Enter on all promts.

2. Copy the key to the backup machine (Raspberry Pi in this case):

```
ssh-copy-id <hostname>@<ip address>
```
This will ask for the Pi’s password once. After that, the script can connect without a password.

You can test it with:

```
ssh <hostname>@<ip address>
```

If it connects without asking for a password, then you’re good.

After that, make sure your config is set up how you want it, and run main.py.

## Recommended things

I recommend `yazi` as a terminal file manager, since the timestamp strings are annoying to type manually. On the Pi, `yazi` has to be built from source, so I’m currently just using `Neovim` to browse the files.

You can also make the script an executable, since it reads from the same config file every time, no need to recompile anything. You could even move the config file into your `dotfiles` or `.config` folder and change the `config_file` path in the script to make it more sturdy.

Setting up some RAID configuration can also be useful. In my case, everything is stored on the Pi’s SD card, but if you have multiple drives, some redundancy wouldn’t hurt.

## Extra rant

Why not progressive backups? (only copy new files)

That would add another layer of over-engineering for this tiny terminal tool. I might add it later, but the whole point of this tool is to capture snapshots of the folders at that exact moment in time (kind of like NixOS does when you rebuild the system).

Is it efficient? No.
Does it handle bandwidth well? Not really.
Do I care? Absolutely not.

I’m backing up kilobytes of data. For a quick late night backup, this does the job.

---

Feel free to fork this, change this, I don't really care. 
Licenced under GNU GPL v3.0
