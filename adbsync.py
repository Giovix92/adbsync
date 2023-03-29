# Copyright (C) 2021/22 Giovix92

import argparse
import os
import subprocess
from alive_progress import alive_bar

version = "v1.1"
serial = None
sync_method = None
directory = None
device_file_list = []
local_file_list = []
diff_file_list = []

parser = argparse.ArgumentParser(description=f'ADB helper to sync only newer files from/to device.', prog='adbsync.py')
group = parser.add_mutually_exclusive_group()
parser.add_argument('--device', type=str, metavar="sn",
	help='Serial number of a specific device.')
group.add_argument('--sync', choices=['device', 'local'],
	help="Sync files either from the selected device or locally.")
parser.add_argument('--dry-run', action='store_true',
	help="Don't actually run copy/move actions.")
parser.add_argument('--directory', type=str, metavar="directory",
	help="Choose a custom origin/destination folder.")
args = parser.parse_args()

print(f"[i] Giovix92's adbsync, version {version}")

# Start ADB and check connected devices
subprocess.check_call(r'adb start-server', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
adb_out = subprocess.check_output(r'adb devices', shell=True).splitlines()
devices = []
for line in adb_out[1:]:
	if not line.strip():
		continue
	if '\tdevice' in line.decode('UTF-8'):
		devices.append(line.decode('UTF-8').replace('\tdevice', ''))
	if '\trecovery' in line.decode('UTF-8'):
		devices.append(line.decode('UTF-8').replace('\trecovery', ''))
	if '\toffline' in line.decode('UTF-8'):
		bad_sn = line.decode('UTF-8').replace('\toffline', '')
		print(f"Found an offline device with sn {bad_sn}, ignoring.")
		continue

# Check if a custom serial number has been specified
if args.device != None:
	if args.device in devices:
		print(f'[i] Using {args.device} as used device.')
		serial = args.device
	else:
		print('[!] Unable to proceed, the specified serial number is not recognized by ADB.')
		exit()
else:
	print(f'[i] Using by default the first recognized device, in this case {devices[0]}.')
	serial = devices[0]

# Check if find command actually exists, calling the help page is sufficient
try:
	cmd = subprocess.check_call(rf'adb -s {serial} shell find --help', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
except:
	print('[!] The find binary is not present in your device, please install busybox/toybox. Exiting.')
	exit()

# Check if a custom directory is specified, otherwise use the s/n
if args.directory:
	directory = args.directory
	print(f'[i] Using {directory} as principal directory.')
else:
	print(f"[i] Using original directory naming: {serial}.")
	directory = serial
if not os.path.exists(directory):
	os.mkdir(directory)

# Fill the list containing device files paths, and decode every single value
print("[i] Pulling file list from both the remote device and from the local folder...")
device_file_list_onlyfiles = []
device_file_list = subprocess.check_output(rf'adb -s {serial} shell find /sdcard/ -type f 2>/dev/null | egrep -iv "(logs|cache|/\.|MIUI|Notifications|Xiaomi|thumb|/-|\.sh)"', shell=True).splitlines()
for i in range(0, len(device_file_list)):
	device_file_list[i] = device_file_list[i].decode('UTF-8')
	device_file_list_onlyfiles.append(device_file_list[i].replace('/sdcard/', ''))

# Fill the list of files present inside the PC
local_file_list_onlyfiles = []
local_file_list = subprocess.check_output(rf'find {directory} -type f', shell=True).splitlines()
for i in range(0, len(local_file_list)):
	local_file_list[i] = local_file_list[i].decode('UTF-8')
	local_file_list_onlyfiles.append(local_file_list[i].replace(f'{directory}/', ''))

# Generate lists of diffing files
print("[i] Diffing the two file lists...")
local_sync = list(set(device_file_list_onlyfiles) - set(local_file_list_onlyfiles))
device_sync = list(set(local_file_list_onlyfiles) - set(device_file_list_onlyfiles))

# Actual sync process
print("[i] Syncing!")
if args.sync == 'device':
	if len(device_sync) != 0:
		print(f"Transferring {len(device_sync)} files to your device...")
		# Transfer to the device - we don't need to create remote folders, Android does that automatically
		if not args.dry_run:
			with alive_bar(len(device_sync)) as bar:
				for i in range(0, len(device_sync)):
					remote_path = '/sdcard/'+device_sync[i]
					local_path = f'{directory}/'+device_sync[i]
					try:
						subprocess.check_call(rf'adb -s {serial} push "{local_path}" "{remote_path}"', stdout=subprocess.DEVNULL, shell=True)
						bar()
					except:
						print(f'[!] An error has occured while pushing this file to the device: {local_path}')
						print('[!] Aborting.')
						exit(1)
	else:
		print('No files need to be pushed!')

elif args.sync == 'local':
	if len(local_sync) != 0:
		print(f"Pulling {len(local_sync)} files from your device...")
		# Transfer from the device - we need to create local folders aswell (heck)
		if not args.dry_run:
			with alive_bar(len(local_sync)) as bar:
				for i in range(0, len(local_sync)):
					remote_path = '/sdcard/'+local_sync[i]
					local_path = f'{directory}/'+local_sync[i]
					local_path_only = os.path.dirname(local_path)
					os.makedirs(f'{local_path_only}', exist_ok=True)
					try:
						subprocess.check_call(rf'adb -s {serial} pull "{remote_path}" "{local_path}"', stdout=subprocess.DEVNULL, shell=True)
						bar()
					except:
						print(f'[!] An error has occured while pulling this file from the device: {remote_path} to {local_path}')
						print('[!] Aborting.')
						exit(1)
	else:
		print('[i] No files need to be pulled!')

print('[i] Finished!')
exit()
