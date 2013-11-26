#!/usr/bin/env python3
#encoding:utf-8

# WARNING: This is a python 3 script (the default on Arch Linux)

import datetime, os, argparse, sys, fileinput, hashlib, subprocess

parser = argparse.ArgumentParser(description='Process an updater-script running some commands on a local Linux box')
parser.add_argument('--logs', action='store',
                   help='The directory for log output')
parser.add_argument('--updater-script', action='store',
                   help='The updater-script to process')
parser.add_argument('--base', action='store',
                   help='The path to the base folder that will be updated -- It should contain system, modem and other partitions mounted as appropriate')
parser.add_argument('--ota', action='store',
                   help='The path to the extracted ota')
parser.add_argument('--applypatch-path', action='store',
                   help='The path to the compiled applypatch binary')

args = parser.parse_args()


# Timestamp for logging
today = datetime.datetime.today()
ts_string = today.isoformat('_')

# Setup / start logging
if not os.path.exists(args.logs):
	os.mkdir(args.logs)

# Logs for this run
log_path = os.path.join(args.logs, ts_string) # Override log_path to be the path for this run's logsf
os.mkdir(log_path)
errorlog = open(os.path.join(log_path, 'error.log'), 'w+')
unknownlog = open(os.path.join(log_path, 'unknown_commands.log'), 'w+')
performedlog = open(os.path.join(log_path, 'performed_commands.log'), 'w+')
ignoredlog = open(os.path.join(log_path, 'ignored_commands.log'), 'w+')

if args.updater_script is None or not os.path.exists(args.updater_script):
	args.updater_script = 'None'
	print('You must specify a valid updater-script file; ' + args.updater_script + ' was invalid')
	print('You must specify a valid updater-script file; ' + args.updater_script + ' was invalid', file=errorlog)
	sys.exit(1)

if args.base is None or not os.path.exists(args.base):
	args.base = 'None'
	print('You must specify the path to the base folder; ' + args.base + ' was invalid')
	print('You must specify the path to the base folder; ' + args.base + ' was invalid', file=errorlog)
	sys.exit(1)

if args.ota is None or not os.path.exists(args.ota):
	args.ota = 'None'
	print('You must specify the path to the ota base folder; ' + args.ota + ' was invalid')
	print('You must specify the path to the ota base folder; ' + args.ota + ' was invalid', file=errorlog)
	sys.exit(1)

if args.applypatch_path is None or not os.path.exists(args.applypatch_path):
	args.applypatch_path = 'None'
	print('You must specify the path to the applypatch binary; ' + args.applypatch_path + ' was invalid')
	print('You must specify the path to the applypatch binary; ' + args.applypatch_path + ' was invalid', file=errorlog)
	sys.exit(1)

# Function for calculating sha1 hash of a given file path
def sha1OfFile(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()

command = ''
clear_command = True
with fileinput.input(files=(args.updater_script)) as f:
	for line in f:
		if clear_command:
			clear_command = False
			command = line.strip()
		else:
			# Combine multi-line commands into single line
			command = command + line.strip()
	
		# Process commands (all commands should end with ;)
		if command.endswith(';'):
			clear_command = True # Tracking to ensure the command is re-set on next pass of loop now that we found a full command string
			if command.startswith('show_progress') or command.startswith('set_progress') or command.startswith('apply_patch_check') or command.startswith('ui_print'):
				print(command, file=ignoredlog)
			else:
				if command.startswith('assert(apply_patch('):
					try:
						patch_command = command[19:-3]
						patch_command = patch_command.replace('"', '')
						arguments = patch_command.split(',')
						original_file = arguments[0]
						if original_file.startswith('/'):
							original_file = original_file[1:]
						original_file_path = os.path.join(args.base, original_file)
						new_file_path = original_file_path
						patched_file_sha1 = arguments[2]
						new_file_size = arguments[3]
						original_file_sha1 = arguments[4]
						patch_file = os.path.join(args.ota, arguments[5].strip()[21:-1]) # This includes stripping off whitespace and "package_extract_file"
						if original_file_sha1 != sha1OfFile(original_file_path):
							print('sha1 mismatch: ' + original_file)
							print('sha1 mismatch: ' + command, file=errorlog)
							continue # Bail and move on with processing
						patch_list = [args.applypatch_path, original_file_path, new_file_path, patched_file_sha1, new_file_size, ':'.join([original_file_sha1, patch_file])]
						subprocess.Popen(patch_list)
						new_file_sha1 = sha1OfFile(new_file_path)
						if patched_file_sha1 != new_file_sha1:
							#print('sha1 mismatch: ' + new_file_path)
							print('sha1 mismatch: ' + new_file_path, file=errorlog)
						print(command, file=performedlog)
					except FileNotFoundError:
						print('file not found: ' + original_file)
						print('file not found: ' + original_file, file=errorlog)
				elif command.startswith('delete_recursive'): # Must preceed delete or else conditions will be wrong
					command = command[17:-2]
					dirs = command.strip().split(',')
					for adir in dirs:
						to_delete = adir.strip().strip('"').strip()[1:]
						try:
							os.removedirs(os.path.join(args.base, to_delete))
						except FileNotFoundError:
							print('warning - directory may or may not have been deleted: ' + to_delete)
							print('warning - directory may or may not have been deleted: ' + to_delete, file=errorlog)
					print(command, file=performedlog)
				elif command.startswith('delete'): # Most follow delete_recursive or else conditions will wrong
					command = command[7:-2]
					files = command.strip().split(',')
					for afile in files:
						to_delete = afile.strip().strip('"').strip()[1:]
						try:
							os.remove(os.path.join(args.base, to_delete))
						except FileNotFoundError:
							print('warning - file may or may not have been deleted: ' + to_delete)
							print('warning - file may or may not have been deleted: ' + to_delete, file=errorlog)
						except IsADirectoryError:
							try:
								 os.removedirs(to_delete)
							except FileNotFoundError:
								print('warning - folder may or may not have been deleted: ' + to_delete)
								print('warning - folder may or may not have been deleted: ' + to_delete, file=errorlog)
					print(command, file=performedlog)
				else:
					print(command, file=unknownlog)
