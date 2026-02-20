from storage import Storage

class ProductManager:
    def __init__(self):
        self.storage = Storage('products.json')
        self.products = self.storage.load()
        if self.products is None or len(self.products) == 0:
            self.products = self.create_samples()
            self.storage.save(self.products)
    
    def create_samples(self):
        return [
            {"product_id": "P1001", "name": "Wireless Mouse", "price": 19.99, "stock": 50},
            {"product_id": "P1002", "name": "USB-C Cable", "price": 9.99, "stock": 100},
            {"product_id": "P1003", "name": "Mechanical Keyboard", "price": 79.99, "stock": 25},
            {"product_id": "P1004", "name": "HD Webcam", "price": 49.99, "stock": 30},
            {"product_id": "P1005", "name": "Laptop Stand", "price": 29.99, "stock": 40},
            {"product_id": "P1006", "name": "Bluetooth Headphones", "price": 59.99, "stock": 35},
            {"product_id": "P1007", "name": "External SSD 1TB", "price": 89.99, "stock": 20},
            {"product_id": "P1008", "name": "Monitor 24 inch", "price": 199.99, "stock": 15},
            {"product_id": "P1009", "name": "Desk Lamp LED", "price": 24.99, "stock": 45},
            {"product_id": "P1010", "name": "Phone Charger", "price": 14.99, "stock": 75}
        ]
    
    def get_products(self):
        return self.products
    
    def find_product_id(self, product_id):
        for product in self.products:
            if product['product_id'] == product_id:
                return product 
        return None 
    
    def search_products(self, keyword):
        keyword_lower = keyword.lower()
        matching_products = []
        for product in self.products:
            if keyword_lower in product['name'].lower():
                matching_products.append(product)
        return matching_products
    
    def check_stock(self, product_id, quantity):
        product = self.find_product_id(product_id)
        if product is None:
            return False, f"Product '{product_id}' not found"
        if product['stock'] < quantity:
            return False, f"Not enough stock. Only {product['stock']} available"
        return True, "Stock is available"
    
    def update_stock(self, product_id, quantity_change):
        product = self.find_product_id(product_id)
        if product is None:
            return False, f"Product '{product_id}' not found"
        new_stock = product['stock'] + quantity_change
        if new_stock < 0:
            return False, "Cannot reduce stock below zero"
        product['stock'] = new_stock
        self.storage.save(self.products)
        return True, f"Stock updated. New stock: {new_stock}"