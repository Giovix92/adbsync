# Copyright (C) 2021/22 Giovix92

import argparse
import os, shutil, re
import subprocess, time
from alive_progress import alive_bar

version = "v1.0"
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
	help="Don't actually run copy/move actions, just simulate 'em.")
parser.add_argument('--directory', type=str, metavar="directory",
	help="Choose a custom origin/destination folder.")
args = parser.parse_args()

# Start ADB
subprocess.check_call(['adb', 'start-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Check connected devices
adb_out = subprocess.check_output(['adb', 'devices']).splitlines()
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

# Check if a custom sn has been specified
if args.device != None:
	if args.device in devices:
		print(f'Using {args.device} as used device.')
		serial = args.device
	else:
		print('Unable to proceed, the specified serial number is not recognized by ADB.')
		exit()
else:
	print(f'Using by default the first recognized device, in this case {devices[0]}.')
	serial = devices[0]

# Check if find command actually exists, calling the help page is sufficient
try:
	cmd = subprocess.check_call(['adb', 'shell', 'find', '--help'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
	print('The find binary is not present in your device, please install busybox/toybox. Exiting.')
	exit()

# Check if a custom directory is specified, otherwise use the s/n
if args.directory:
	if os.path.exists(args.directory):
		directory = args.directory
	elif os.path.exists(os.path.join(os.getcwd(), args.directory)):
		directory = os.path.join(os.getcwd(), args.directory)
	else:
		print("Specified directory cannot be found - falling back to original naming.")
		directory = serial
else:
	print("Using original directory naming.")
	directory = serial
	
if not os.path.exists(directory):
	os.mkdir(directory)

# Fill the list containing device files paths, and decode every single value
device_file_list_args = [
	'adb',
	'-s',
	f'{serial}',
	'shell',
	'find',
	'/sdcard/',
	'-type',
	'f',
	'-name',
	'"*"',
	'!',
	'-iname',
	'".*"',
	'!',
	'-path',
	'"*thumbnails*"',
	'!',
	'-path',
	'"*cache*"'
]
device_file_list_onlyfiles = []
device_file_list = subprocess.check_output(device_file_list_args).splitlines()
for i in range(0, len(device_file_list)):
	device_file_list[i] = device_file_list[i].decode('UTF-8')
	device_file_list_onlyfiles.append(device_file_list[i].replace('/sdcard/', ''))


# Fill the list of files present inside the PC
local_file_list_args = [
	'find',
	f'{directory}',
	'-type',
	'f'
]
local_file_list_onlyfiles = []
local_file_list = subprocess.check_output(local_file_list_args).splitlines()
for i in range(0, len(local_file_list)):
	local_file_list[i] = local_file_list[i].decode('UTF-8')
	local_file_list_onlyfiles.append(local_file_list[i].replace(f'{directory}/', ''))

# Generate lists of diffing files
local_sync = list(set(device_file_list_onlyfiles) - set(local_file_list_onlyfiles))
device_sync = list(set(local_file_list_onlyfiles) - set(device_file_list_onlyfiles))

# Actual sync process
if args.sync == 'device' and len(device_sync) != 0:
	print(f"Transferring {len(device_sync)} files to your device...")
	# Transfer to the device - we don't need to create remote folder, Android does that automatically
	if not args.dry_run:
		with alive_bar(len(device_sync)) as bar:
			for i in range(0, len(device_sync)):
				remote_path = '/sdcard/'+device_sync[i]
				local_path = f'{directory}/'+device_sync[i]
				push_args = [
					'adb',
					'-s',
					f'{serial}',
					'push',
					f'{local_path}',
					f'{remote_path}'
				]
				try:
					subprocess.check_call(push_args, stdout=subprocess.DEVNULL)
				except:
					print('An error has occured while syncing files to the device. Aborting.')
					exit(1)
elif args.sync == 'device' and len(device_sync) == 0:
	print('No files need to be transferred!')

if args.sync == 'local' and len(local_sync) != 0:
	print(f"Pulling {len(local_sync)} files from your device...")
	# Transfer from the device - we need to create local folders aswell (heck)
	if not args.dry_run:
		with alive_bar(len(local_sync)) as bar:
			for i in range(0, len(local_sync)):
				remote_path = '/sdcard/'+local_sync[i]
				local_path = f'{directory}/'+local_sync[i]
				local_path_only = os.path.dirname(local_path)
				os.makedirs(f'{local_path_only}', exist_ok=True)
				pull_args = [
					'adb',
					'-s',
					f'{serial}',
					'pull',
					f'{remote_path}',
					f'{local_path}'
				]
				try:
					subprocess.check_call(pull_args, stdout=subprocess.DEVNULL)
				except:
					print('An error has occured while pulling files from the device. Aborting.')
					exit(1)
				bar()
elif args.sync == 'local' and len(local_sync) == 0:
	print('No files need to be pulled!')

print('Finished!')
exit()
