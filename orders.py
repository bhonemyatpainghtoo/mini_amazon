from storage import Storage
from datetime import datetime

class OrderManager:
    def __init__(self):
        self.storage = Storage('orders.json')
        self.orders = self.storage.load()
        
        if self.orders is None:
            self.orders = []
            self.storage.save(self.orders)
    
    def generate_order_id(self):
        if len(self.orders) == 0:
            return "O0001"
        
        last_order_id = self.orders[-1]['order_id']
        last_number = int(last_order_id[1:])
        new_number = last_number + 1
        new_order_id = f"O{new_number:04d}"
        
        return new_order_id
    
    def create_order(self, username, cart_items, product_manager, cart_manager):
        if len(cart_items) == 0:
            return False, "Your cart is empty", None
 
        for item in cart_items:
            available, message = product_manager.check_stock(
                item['product_id'],
                item['quantity']
            )
            if not available:
                return False, f"Stock check failed: {message}", None
                
        order_items = []
        total_cost = 0
        
        for item in cart_items:
            product = product_manager.find_product_id(item['product_id'])
            
            if product is None:
                return False, f"Product {item['product_id']} not found", None

            item_cost = product['price'] * item['quantity']
            total_cost = total_cost + item_cost

            order_items.append({
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_price': product['price']
            })

            success, msg = product_manager.update_stock(
                item['product_id'],
                -item['quantity'] 
            )
            
            if not success:
                return False, f"Failed to update stock: {msg}", None

        order_id = self.generate_order_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_order = {
            'order_id': order_id,
            'username': username,
            'items': order_items,
            'total': total_cost,
            'timestamp': timestamp
        }

        self.orders.append(new_order)
        self.storage.save(self.orders)
        cart_manager.clear_cart(username)

        return True, "Order placed successfully!", order_id
    
    def get_user_orders(self, username):
        user_orders = []
        for order in self.orders:
            if order['username'] == username:
                user_orders.append(order)

        user_orders.reverse()
        return user_orders
    
    def find_order_by_id(self, order_id):
        for order in self.orders:
            if order['order_id'] == order_id:
                return order
        return None
    
    def export_receipt(self, order_id):
        order = self.find_order_by_id(order_id)
        
        if order is None:
            return False, f"Order {order_id} not found"

        filename = f"receipt_{order_id}.txt"
        
        try:
            with open(filename, 'w') as file:
                file.write("=" * 60 + "\n")
                file.write(" " * 20 + "MINI-AMAZON RECEIPT\n")
                file.write("=" * 60 + "\n\n")

                file.write(f"Order ID: {order['order_id']}\n")
                file.write(f"Customer: {order['username']}\n")
                file.write(f"Date: {order['timestamp']}\n\n")

                file.write("-" * 60 + "\n")
                file.write(f"{'Product ID':<15} {'Qty':<8} {'Price':<12} {'Subtotal':<12}\n")
                file.write("-" * 60 + "\n")
                
                for item in order['items']:
                    subtotal = item['unit_price'] * item['quantity']
                    file.write(f"{item['product_id']:<15} ")
                    file.write(f"{item['quantity']:<8} ")
                    file.write(f"${item['unit_price']:<11.2f} ")
                    file.write(f"${subtotal:<11.2f}\n")
                
                file.write("-" * 60 + "\n")
                file.write(f"{'TOTAL:':<38} ${order['total']:.2f}\n")
                file.write("=" * 60 + "\n")
                file.write("\nThank you for shopping with Mini-Amazon!\n")
            
            return True, f"Receipt saved to {filename}"
        
        except Exception as error:
            return False, f"Failed to save receipt: {str(error)}"