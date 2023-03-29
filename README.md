# adbsync - An ADB syncing helper

## What's this?

Everytime I wanted to make a backup of my phone, or restore those files onto it, I had to use everytime the classical `adb pull` (or `adb push`). ADB, though, has a little caveat: even if a file already exists, it'll just _overwrite_ it every single time, making multiple backup times long as hell. That's why I made adbsync.

## Features

- Automatically detects a connected device (and creates its folder using its serial number)
- Automatically detects remote present files and local files, if any.
- Only syncs from/to the device non-present files, speeding up backup/restore times.
- Avoids logs/cache/hidden files, saving extra time and space

## Requirements

- Python 3.9 =>
- alive-progress 2.1 =>
- An UNIX system (macOS, any distro Linux)

## How to use it

Just clone/download the source as zip, and run inside a terminal `python3 adbsync.py`.

## CLI commands available

These are the currently available functions:

- `-h`: Shows every command available.
- `--device sn`: Specifies a custom sn of a particular connected device.
- `--sync local,device`: Syncs file from/to the device.
  - `local` syncs files from the device.
  - `device` syncs files to the device.
- `--dry-run`: Simulate syncing.
- `--directory directory`: Specifies a custom backup/restore LOCAL directory.
