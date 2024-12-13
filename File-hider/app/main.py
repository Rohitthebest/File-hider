import os
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
from sqlalchemy.orm import Session

# Import local modules
from config import Config
from auth import AuthManager, User
from email_verification import EmailVerificationService
from file_operations import FileHider, HiddenFile

# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup database engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Rich Console for enhanced CLI output
console = Console()

class FileHiderApp:
    def __init__(self):
        self.db = SessionLocal()
        self.current_user = None

    def _clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _pause(self):
        """Pause and wait for user to press enter"""
        input("\nPress Enter to continue...")

    def _main_menu(self):
        """Display main menu"""
        while True:
            self._clear_screen()
            console.print("[bold cyan]File Hider Application[/bold cyan]")
            console.print("\nMain Menu:")
            console.print("1. Login")
            console.print("2. Signup")
            console.print("3. Exit")
            
            choice = Prompt.ask("Enter your choice", choices=['1', '2', '3'])
            
            if choice == '1':
                self._login_menu()
            elif choice == '2':
                self._signup_menu()
            elif choice == '3':
                console.print("[yellow]Goodbye![/yellow]")
                break

    def _login_menu(self):
        """Login menu and authentication process"""
        self._clear_screen()
        console.print("[bold green]Login[/bold green]")
        
        username = Prompt.ask("Enter username")
        password = Prompt.ask("Enter password", password=True)
        
        try:
            # Authentication logic
            user = self.db.query(User).filter_by(username=username).first()
            
            if not user or not AuthManager.verify_password(password, user.password_hash):
                console.print("[red]Invalid username or password[/red]")
                self._pause()
                return
            
            # Check email verification
            if not user.is_verified:
                console.print("[yellow]Email not verified[/yellow]")
                verify_choice = Confirm.ask("Do you want to verify your email?")
                if verify_choice:
                    self._verify_email_menu(user.email)
                return
            
            # Successful login
            self.current_user = user
            self._user_dashboard()
        
        except Exception as e:
            console.print(f"[red]Login error: {e}[/red]")
            self._pause()

    def _signup_menu(self):
        """Signup menu"""
        self._clear_screen()
        console.print("[bold green]Signup[/bold green]")
        
        username = Prompt.ask("Enter username")
        email = Prompt.ask("Enter email")
        password = Prompt.ask("Enter password", password=True)
        confirm_password = Prompt.ask("Confirm password", password=True)
        
        if password != confirm_password:
            console.print("[red]Passwords do not match[/red]")
            self._pause()
            return
        
        try:
            # Validate email
            if not EmailVerificationService.is_valid_email(email):
                console.print("[red]Invalid email format[/red]")
                self._pause()
                return
            
            # Check if username exists
            existing_user = self.db.query(User).filter_by(username=username).first()
            if existing_user:
                console.print("[red]Username already exists[/red]")
                self._pause()
                return
            
            # Hash password
            hashed_password = AuthManager.hash_password(password)
            
            # Create new user
            new_user = User(
                username=username, 
                email=email, 
                password_hash=hashed_password
            )
            
            self.db.add(new_user)
            self.db.commit()
            
            # Initiate email verification
            verification_result = EmailVerificationService.initiate_verification(
                self.db, 
                new_user
            )
            
            if verification_result['status'] == 'success':
                console.print("[green]Account created! Please check your email to verify.[/green]")
                self._verify_email_menu(email)
            else:
                console.print(f"[yellow]{verification_result['message']}[/yellow]")
            
            self._pause()
        
        except Exception as e:
            self.db.rollback()
            console.print(f"[red]Signup error: {e}[/red]")
            self._pause()

    def _verify_email_menu(self, email=None):
        """Email verification menu"""
        self._clear_screen()
        console.print("[bold green]Email Verification[/bold green]")
        
        if not email:
            email = Prompt.ask("Enter your email")
        
        while True:
            console.print("\nEmail Verification Options:")
            console.print("1. Enter Verification Code")
            console.print("2. Resend Verification Code")
            console.print("3. Back to Main Menu")
            
            choice = Prompt.ask("Enter your choice", choices=['1', '2', '3'])
            
            if choice == '1':
                verification_code = Prompt.ask("Enter verification code")
                
                result = EmailVerificationService.verify_email(
                    self.db, 
                    email, 
                    verification_code
                )
                
                if result['status'] == 'success':
                    console.print("[green]Email verified successfully![/green]")
                    self._pause()
                    break
                else:
                    console.print(f"[red]{result['message']}[/red]")
                    self._pause()
            
            elif choice == '2':
                resend_result = EmailVerificationService.resend_verification_code(
                    self.db, 
                    email
                )
                console.print(f"[yellow]{resend_result['message']}[/yellow]")
                self._pause()
            
            elif choice == '3':
                break

    def _user_dashboard(self):
        """User dashboard after login"""
        while self.current_user:
            self._clear_screen()
            console.print(f"[bold green]Welcome, {self.current_user.username}![/bold green]")
            console.print("\nUser Dashboard:")
            console.print("1. Hide File")
            console.print("2. Unhide File")
            console.print("3. List Hidden Files")
            console.print("4. Verify Email")
            console.print("5. Logout")
            
            choice = Prompt.ask("Enter your choice", choices=['1', '2', '3', '4', '5'])
            
            if choice == '1':
                self._hide_file_menu()
            elif choice == '2':
                self._unhide_file_menu()
            elif choice == '3':
                self._list_hidden_files_menu()
            elif choice == '4':
                self._verify_email_menu(self.current_user.email)
            elif choice == '5':
                console.print("[yellow]Logging out...[/yellow]")
                self.current_user = None
                break

    def _hide_file_menu(self):
        """Hide file menu"""
        self._clear_screen()
        console.print("[bold green]Hide File[/bold green]")
        
        file_path = Prompt.ask("Enter the full path of the file to hide")
        
        if not os.path.exists(file_path):
            console.print("[red]File not found[/red]")
            self._pause()
            return
        
        try:
            file_hider = FileHider(
                user_id=self.current_user.id,
                upload_folder=Config.UPLOAD_FOLDER,
                hidden_folder=Config.HIDDEN_FOLDER
            )
            
            hidden_filename = file_hider.hide_file(file_path, self.db)
            console.print(f"[green]File hidden successfully. Hidden filename: {hidden_filename}[/green]")
            self._pause()
        
        except Exception as e:
            console.print(f"[red]File hiding error: {e}[/red]")
            self._pause()

    def _unhide_file_menu(self):
        """Unhide file menu"""
        self._clear_screen()
        console.print("[bold green]Unhide File[/bold green]")
        
        hidden_file_id = Prompt.ask("Enter the hidden file id")
        
        try:
            file_hider = FileHider(
                user_id=self.current_user.id,
                upload_folder=Config.UPLOAD_FOLDER,
                hidden_folder=Config.HIDDEN_FOLDER
            )
            console.print(f"[yellow]Unhiding file... {hidden_file_id, file_hider.user_id}[/yellow]")
            
            restored_path = file_hider.unhide_file(hidden_file_id, self.db)
            console.print(f"[green]File unhidden successfully. Restored to: {restored_path}[/green]")
            self._pause()
        
        except Exception as e:
            console.print(f"[red]File unhiding error: {e}[/red]")
            self._pause()

    def _list_hidden_files_menu(self):
        """List hidden files menu"""
        self._clear_screen()
        console.print("[bold green]Hidden Files[/bold green]")
        
        try:
            hidden_files = self.db.query(HiddenFile).filter_by(
                user_id=self.current_user.id
            ).all()
            
            if not hidden_files:
                console.print("[yellow]No hidden files found[/yellow]")
                self._pause()
                return
            
            console.print("\nHidden Files:")
            for idx, file in enumerate(hidden_files, 1):
                console.print(f"{file.id}. Original: {file.original_filename}")
                console.print(f"   Hidden: {file.hidden_filename}")
                console.print(f"   Hidden At: {file.hidden_at}\n")
            
            self._pause()
        
        except Exception as e:
            console.print(f"[red]Error listing hidden files: {e}[/red]")
            self._pause()

    def run(self):
        """Main application run method"""
        try:
            self._main_menu()
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
        finally:
            self.db.close()

def main():
    app = FileHiderApp()
    app.run()

if __name__ == '__main__':
    main()