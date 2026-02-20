from storage import Storage  
import hashlib  

class UserManager:   
    def __init__(self):
        self.storage = Storage('users.json')
        self.users = self.storage.load()
        
        if self.users is None:
            self.users = []
            self.storage.save(self.users) 
    
    def secure_password(self, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return hashed
    
    def check_username(self, username):
        for user in self.users:
            if user['username'] == username.lower().strip():
                return True 
        
        return False 
    
    def register_user(self, username, password):
        
        if not username or username.strip() == "":
            return False, "Username cannot be empty"
        

        if self.check_username(username):
            return False, f"Username '{username}' is already taken"
        

        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        

        new_user = {
            'username': username.lower().strip(),
            'password': self.secure_password(password)  
        }

        self.users.append(new_user)
        self.storage.save(self.users)  
        return True, f"Account created successfully! Welcome, {username}!"
    
    def login_user(self, username, password):

        if not username or not password:
            return False, "Please enter both username and password"
        
        user_found = None
        for user in self.users:
            if user['username'] == username.lower().strip():
                user_found = user
                break 

        if user_found is None:
            return False, "Invalid username or password"

        if user_found['password'] == self.secure_password(password):
            return True, f"Welcome back, {username}!"
        else:
            return False, "Invalid username or password"
