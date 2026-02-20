from storage import Storage

class CartManager:   
    def __init__(self):
        self.storage = Storage('carts.json')
        self.carts = self.storage.load()

        if self.carts is None:
            self.carts = {}
            self.storage.save(self.carts)
    
    def get_cart(self, username):
        if username not in self.carts:
            self.carts[username] = []
            self.storage.save(self.carts)
        
        return self.carts[username]
    
    def add_to_cart(self, username, product_id, quantity, product_manager):
        if quantity <= 0:
            return False, "Quantity must be greater than zero"

        available, message = product_manager.check_stock(product_id, quantity)
        if not available:
            return False, message

        cart = self.get_cart(username)

        item_found = None
        for item in cart:
            if item['product_id'] == product_id:
                item_found = item
                break

        if item_found is not None:
            new_quantity = item_found['quantity'] + quantity
            
            available, message = product_manager.check_stock(product_id, new_quantity)
            if not available:
                return False, f"Cannot add {quantity} more. {message}"
            
            item_found['quantity'] = new_quantity

        else:
            cart.append({
                'product_id': product_id,
                'quantity': quantity
            })

        self.carts[username] = cart
        self.storage.save(self.carts)

        product = product_manager.find_product_id(product_id)
        
        return True, f"Added {quantity} x {product['name']} to cart"
    
    def remove_from_cart(self, username, product_id):
        cart = self.get_cart(username)
        original_count = len(cart)

        new_cart = []
        for item in cart:
            if item['product_id'] != product_id:
                new_cart.append(item)

        if len(new_cart) < original_count:
            self.carts[username] = new_cart
            self.storage.save(self.carts)
            return True, f"Removed {product_id} from cart"
        else:
            return False, f"{product_id} not found in cart"
    
    def update_quantity(self, username, product_id, new_quantity, product_manager):
        if new_quantity <= 0:
            return False, "Quantity must be greater than zero"

        cart = self.get_cart(username)
        
        item_found = None
        for item in cart:
            if item['product_id'] == product_id:
                item_found = item
                break

        if item_found is None:
            return False, f"{product_id} not found in cart"

        available, message = product_manager.check_stock(product_id, new_quantity)
        if not available:
            return False, message
        
        item_found['quantity'] = new_quantity
        self.storage.save(self.carts)
        
        return True, f"Updated {product_id} quantity to {new_quantity}"
    
    def clear_cart(self, username):
        self.carts[username] = []
        self.storage.save(self.carts)
        
        return True, "Cart cleared"
    
    def calculate_total(self, username, product_manager):
        cart = self.get_cart(username)
        total = 0
        
        for item in cart:
            product = product_manager.find_product_id(item['product_id'])
            if product:
                item_cost = product['price'] * item['quantity']
                total = total + item_cost
        
        return total