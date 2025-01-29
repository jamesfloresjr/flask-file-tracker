from .models import File
from . import db

# Create new item in database
def create_new_file(filename, location, file_hash, status='in_progress'):
    # Query the database for a file matching the provided hash
    file = File.query.filter_by(hash=file_hash).first()
 
    if file:
        return f'File already exists: {filename}'

    # Create a new instance of the File model
    new_file = File(filename=filename, location=location, hash=file_hash, status=status)
    
    # Add the new item to the session
    db.session.add(new_file)
    
    # Commit the transaction to save the new file
    db.session.commit()
    
    return f'Added new file: {filename}'

def update_file_location(file_hash, new_location):
    # Query the database for a file matching the provided hash
    file = File.query.filter_by(hash=file_hash).first()

    if file:
        # Change the file location
        file.location = new_location

        # Commit changes
        db.session.commit()
        
        return f"Updated file location: {file.filename}"
    else:
        return f"File with hash {file_hash} not found."

def update_file_status(file_hash, new_status):
    # Query the database for a file matching the provided hash
    file = File.query.filter_by(hash=file_hash).first()

    if file:
        # Change the file location
        file.status = new_status

        # Commit changes
        db.session.commit()
        
        return f"Updated file status: {file.filename}"
    else:
        return f"File with hash {file_hash} not found."

def hello_world(name):
    print("Hello, world! Your name is " + name)
