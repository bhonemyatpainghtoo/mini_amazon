import json  
import os  


class Storage:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def load(self):
        if not os.path.exists(self.filepath):
            return None  
        
        try:
            with open(self.filepath, 'r') as file:
                data = json.load(file) 
                return data
        except:

            return None
    
    def save(self, data):
        try:
            with open(self.filepath, 'w') as file:
                json.dump(data, file, indent=4)
            return True 
        except:
            return False 