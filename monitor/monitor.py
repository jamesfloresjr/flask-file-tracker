import os, sys, hashlib, configparser, stat, time, shutil, getpass, subprocess
from datetime import datetime

# Load configuration
config = configparser.ConfigParser()
config.read('/deploy/monitor/monitor.config')

# Pull in Settings
CHECK_INTERVAL = int(config['settings']['check_interval'])
MAX_ATTEMPTS = int(config['settings']['max_attempts'])

# Load paths
log_directory = config['paths']['log_directory']
SOURCE_FOLDER = config['paths']['source_folder']
DEFAULT_PROCESSING_FOLDER = config['paths']['default_processing_folder']
ERROR_FOLDER = config['paths']['error_folder']
FLASK_APP = config['paths']['flask_app']

# Load destination rules as a dictionary
SUFFIXES_TO_HANDLE = {key: value for key,
                      value in config['suffixes_to_handle'].items()}
PREFIXES_TO_HANDLE = {key: value for key,
                      value in config['prefixes_to_handle'].items()}
					  
##### FLASK: Adding flask_app directory to system
sys.path.append(os.path.abspath(FLASK_APP))

##### FLASK: Importing custom scripts from flask app
from website import *
from website.models import File
from website.utils import *

##### FLASK: Creating app instance
app = create_app()

# Simple Logging
class Log:
    def __init__(self, directory):
        self.directory = directory

    def get_log_file(self):
        current_date = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.directory, f"{current_date}.log")

    def write_log(self, level, message):
        log_file_path = self.get_log_file()
        current_time = datetime.now().strftime("%H:%M:%S")
        user = getpass.getuser()

        with open(log_file_path, 'a') as log_file:
            log_file.write(
                f"{user} - {current_time} - {level.upper()} - {message}\n")

    def info(self, message):
        self.write_log("info", message)

    def warn(self, message):
        self.write_log("warn", message)

    def error(self, message):
        self.write_log("error", message)


# Initialize Logger
log = Log(log_directory)

# Function to create directories if they don't exist
def dir_check(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            log.error(f"Error: {directory} does not exist. Exiting.")
            exit()

dir_check(log_directory)

# Initialize necessary folders
folders_to_check = [SOURCE_FOLDER, DEFAULT_PROCESSING_FOLDER, ERROR_FOLDER, log_directory] + \
    list(SUFFIXES_TO_HANDLE.values()) + list(PREFIXES_TO_HANDLE.values())
for folder in folders_to_check:
    dir_check(folder)

# Check if file has 660 permissions
def has_correct_permissions(file_path):
    file_stat = os.stat(file_path)
    permissions = stat.S_IMODE(file_stat.st_mode)
    return permissions == 0o660

# Function to check if a file is fully copied by verifying that its size is stable
def is_file_ready(file_path):
    initial_size = -1
    while True:
        current_size = os.path.getsize(file_path)
        if current_size == initial_size:
            return True  # File size is stable, assuming it's ready
        initial_size = current_size
        time.sleep(2)    # Wait 2 seconds and check again

# Determine the appropriate destination based on file name
def get_destination_path(file_name):
    # Check suffixes first
    for suffix, path in SUFFIXES_TO_HANDLE.items():
        if file_name.endswith(suffix):
            return os.path.join(path, file_name)

    # Then check prefixes
    for prefix, path in PREFIXES_TO_HANDLE.items():
        if file_name.startswith(prefix):
            return os.path.join(path, file_name)

    # Default to the main destination folder
    return os.path.join(DEFAULT_PROCESSING_FOLDER, file_name)

# Handle file move failure by moving the file to the error folder
def handle_move_failure(file_name, file_path, file_hash, dest_path, move_error, attempts):
    error_path = os.path.join(ERROR_FOLDER, file_name)
    log.error(
        f"Failed to move {file_name} to {dest_path}: {move_error}. Attempting to move to {ERROR_FOLDER}.")
    try:
        shutil.move(file_path, error_path)
        log.info(f"Moved {file_name} to {ERROR_FOLDER} due to an error")
    except Exception as e:
        log.error(f"Failed to move {file_name} to {ERROR_FOLDER} as well: {e}")
    
    attempts.pop(file_name, None)
    
    ##### FLASK: Update file with the error status
    with app.app_context():
        log.info(update_file_location(file_hash, error_path))
        log.info(update_file_status(file_hash, 'failed'))

##### FLASK: Creates a sha256 hash
def hash_file(filename, algorithm="sha256"):
    """
    Calculates the hash of a file using the specified algorithm.
    Defaults to SHA-256.
    """

    h = hashlib.new(algorithm)

    with open(filename, "rb") as file:
        while True:
            chunk = file.read(4096)  # Read file in chunks
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()

# Directory Monitor
def monitor_folder():
    attempts = {}  # Track attempts for each file
    log.info(f"Started monitoring folder: {SOURCE_FOLDER}")

    while True:
        # Monitor files in the source folder
        files = set(os.listdir(SOURCE_FOLDER))

        for file_name in files:
            file_path = os.path.join(SOURCE_FOLDER, file_name)
            file_hash = hash_file(file_path)
            if os.path.isfile(file_path):
                # Initialize attempt count if not present
                if file_name not in attempts:
                    attempts[file_name] = 0

                    ##### FLASK: Create new item for the file tracker
                    with app.app_context():
                        log.info(create_new_file(file_name, file_path, file_hash))

                # Check if the file is ready for processing
                if not is_file_ready(file_path):
                    attempts[file_name] += 1
                    if attempts[file_name] >= MAX_ATTEMPTS:
                        log.warn(
                            f"File {file_name} cannot be opened. Is it still being copied? Waiting...")
                        attempts[file_name] = 0  # Reset counter after logging
                    continue  # Skip this file and check it in the next loop

                # Check permissions and skip if not 660
                if not has_correct_permissions(file_path):
                    attempts[file_name] += 1
                    if attempts[file_name] >= 5:
                        log.warn(
                            f"File {file_name} has incorrect permissions (not 660).")
                        attempts[file_name] = 0  # Reset counter after logging
                    continue  # Skip this file and check it in the next loop

                # Get the appropriate destination path based on the file name
                dest_path = get_destination_path(file_name)
                try:
                    shutil.move(file_path, dest_path)
                    log.info(f"Moved file {file_name} to {dest_path}")
                    # Remove from attempts after successful processing
                    attempts.pop(file_name, None)
                    
                    ##### FLASK: Update item with new location
                    with app.app_context():
                        log.info(update_file_location(file_hash, dest_path))

                except Exception as move_error:
                    handle_move_failure(
                        file_name, file_path, file_hash, dest_path, move_error, attempts)

        # Wait before the next check
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        monitor_folder()
    except Exception as e:
        log.error(f"An error occurred: {str(e)}")
