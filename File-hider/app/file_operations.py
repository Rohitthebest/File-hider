import os
import uuid
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from db import HiddenFile,User
from config import Config
from rich.console import Console
console = Console()

class FileHider:
    def __init__(self, user_id, upload_folder, hidden_folder):
        self.user_id = user_id
        self.upload_folder = upload_folder
        self.hidden_folder = hidden_folder
        self.encryption_key = Config.SECRET_KEY
        self.cipher_suite = Fernet(self.encryption_key)
    
    def hide_file(self, file_path, db: Session):
        # Generate unique hidden filename
        hidden_filename = str(uuid.uuid4())
        
        # Read original file
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        # Encrypt file
        encrypted_data = self.cipher_suite.encrypt(file_data)
        
        # Save encrypted file in hidden folder
        hidden_path = os.path.join(self.hidden_folder, hidden_filename)
        with open(hidden_path, 'wb') as hidden_file:
            hidden_file.write(encrypted_data)
        
        # Store file metadata in database
        hidden_file_record = HiddenFile(
            user_id=self.user_id,
            original_filename=os.path.basename(file_path),
            hidden_filename=hidden_filename,
            file_path=hidden_path
        )
        db.add(hidden_file_record)
        db.commit()
        
        # Optional: Remove original file
        os.remove(file_path)
        
        return hidden_filename
    
    def unhide_file(self, file_id, db: Session):
        # Retrieve file metadata from database

        hidden_file = db.query(HiddenFile).filter(
            HiddenFile.id == file_id,
            HiddenFile.user_id == self.user_id
        ).first()
        
        if not hidden_file:
            raise ValueError("File not found or unauthorized")
        
        # Read encrypted file
        with open(hidden_file.file_path, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        
        
        
        # Decrypt file
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            console.print(decrypted_data)
        
        # Save decrypted file in upload folder
            restored_path = os.path.join(
            self.upload_folder, 
            hidden_file.original_filename
            )
        except Exception as e:
            console.print(f"[red]Error decrypting file: {e}[/red]")
            return None
       

        with open(restored_path, 'wb') as restored_file:
            restored_file.write(decrypted_data)
        

        
        # Remove hidden file
        os.remove(hidden_file.file_path)
        db.delete(hidden_file)
        db.commit()
        
        return restored_path

