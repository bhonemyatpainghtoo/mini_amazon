from users import UserManager
from products import ProductManager
from cart import CartManager
from orders import OrderManager


class MiniAmazon:

    def __init__(self):

        self.user_manager = UserManager()          
        self.product_manager = ProductManager()    
        self.cart_manager = CartManager()         
        self.order_manager = OrderManager()     

        self.current_user = None
    
    def show_header(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "MINI-AMAZON STORE")
        print("=" * 60)
    
    def welcome_menu(self):
        while True:
            self.show_header()
            print("\nWelcome! What would you like to do?")
            print("\n1. Register (Create new account)")
            print("2. Login (Access your account)")
            print("3. Exit (Quit the program)")
            print("-" * 60)

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                self.register()
            elif choice == "2":
                if self.login():
                    self.store_menu()
            elif choice == "3":
                print("\nThank you for visiting Mini-Amazon! Goodbye!")
                break
            else:
                print("\n❌ Invalid choice! Please enter 1, 2, or 3.")
                input("Press Enter to continue...")
    
    def register(self):
        self.show_header()
        print("\n--- CREATE NEW ACCOUNT ---\n") 
        username = input("Choose a username: ").strip() 
        password = input("Choose a password (min 6 characters): ").strip()  
        success, message = self.user_manager.register_user(username, password)
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")
        
        input("\nPress Enter to continue...")  
    def login(self):
        self.show_header()
        print("\n--- LOGIN ---\n")
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        success, message = self.user_manager.login_user(username, password)
        if success:
            self.current_user = username  
            print(f"\n✅ {message}")
            input("Press Enter to continue...")
            return True
        else:
            print(f"\n❌ {message}")
            input("Press Enter to continue...")
            return False
    def store_menu(self):
        while True:
            self.show_header()
            print(f"\nWelcome, {self.current_user}!")
            print("\n1. Browse Products (See all products)")
            print("2. Search Products (Find specific products)")
            print("3. View Cart (See what's in your cart)")
            print("4. Checkout (Buy your items)")
            print("5. View Order History (See past orders)")
            print("6. Logout (Go back to main menu)")
            print("-" * 60)
            choice = input("\nEnter your choice (1-6): ").strip()
            if choice == "1":
                self.browse_products()
            elif choice == "2":
                self.search_products()
            elif choice == "3":
                self.view_cart()
            elif choice == "4":
                self.checkout()
            elif choice == "5":
                self.view_order_history()
            elif choice == "6":
                print(f"\n👋 Goodbye, {self.current_user}!")
                self.current_user = None
                input("Press Enter to continue...")
                break
            else:
                print("\n❌ Invalid choice! Please enter 1-6.")
                input("Press Enter to continue...")   
    def browse_products(self):
        self.show_header()
        print("\n--- ALL PRODUCTS ---\n")
        products = self.product_manager.get_products()
        print(f"{'ID':<12} {'Name':<30} {'Price':<12} {'Stock':<10}")
        print("-" * 64)
        for product in products:
            print(f"{product['product_id']:<12} ", end="")
            print(f"{product['name']:<30} ", end="")
            print(f"${product['price']:<11.2f} ", end="")
            print(f"{product['stock']:<10}")    
        print("-" * 64)  
        add = input("\nAdd a product to cart? (y/n): ").strip().lower()
        if add == 'y':
            self.add_to_cart()
        else:
            input("Press Enter to continue...")   
    def search_products(self):
        self.show_header()
        print("\n--- SEARCH PRODUCTS ---\n")

        keyword = input("Enter product name to search: ").strip()
        
        if not keyword:
            print("\n❌ Please enter a search term!")
            input("Press Enter to continue...")
            return
        
        results = self.product_manager.search_products(keyword)

        if len(results) == 0:
            print(f"\nNo products found matching '{keyword}'")
        else:
            print(f"\nFound {len(results)} product(s):\n")
            print(f"{'ID':<12} {'Name':<30} {'Price':<12} {'Stock':<10}")
            print("-" * 64)
            
            for product in results:
                print(f"{product['product_id']:<12} ", end="")
                print(f"{product['name']:<30} ", end="")
                print(f"${product['price']:<11.2f} ", end="")
                print(f"{product['stock']:<10}")
            
            print("-" * 64)
            add = input("\nAdd a product to cart? (y/n): ").strip().lower()
            if add == 'y':
                self.add_to_cart()
                return
        
        input("Press Enter to continue...")
    
    def add_to_cart(self):
        product_id = input("\nEnter Product ID: ").strip()
        
        product = self.product_manager.find_product_id(product_id)
        if not product:
            print(f"\n❌ Product '{product_id}' not found!")
            input("Press Enter to continue...")
            return
        
        print(f"\nProduct: {product['name']}")
        print(f"Price: ${product['price']:.2f}")
        print(f"Available Stock: {product['stock']}")

        try:
            quantity = int(input("\nHow many do you want? ").strip())
        except:
            print("\n❌ Please enter a valid number!")
            input("Press Enter to continue...")
            return
        
        success, message = self.cart_manager.add_to_cart(
            self.current_user,
            product_id,
            quantity,
            self.product_manager
        )
        
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")
        
        input("Press Enter to continue...")
    
    def view_cart(self):

        self.show_header()
        print(f"\n--- YOUR CART ({self.current_user}) ---\n")
        

        cart = self.cart_manager.get_cart(self.current_user)
        if len(cart) == 0:
            print("Your cart is empty.")
            input("\nPress Enter to continue...")
            return
        total = 0
        print(f"{'Product ID':<12} {'Name':<25} {'Qty':<8} {'Price':<12} {'Subtotal':<12}")
        print("-" * 69)
        
        for item in cart:
            product = self.product_manager.find_product_id(item['product_id'])
            
            if product:
                subtotal = product['price'] * item['quantity']
                total = total + subtotal
                
                # Print item
                print(f"{item['product_id']:<12} ", end="")
                print(f"{product['name']:<25} ", end="")
                print(f"{item['quantity']:<8} ", end="")
                print(f"${product['price']:<11.2f} ", end="")
                print(f"${subtotal:<11.2f}")
        
        print("-" * 69)
        print(f"{'TOTAL:':<48} ${total:.2f}")
        print("=" * 69)
        
        # Ask what to do
        print("\n1. Remove an item")
        print("2. Update quantity")
        print("3. Go back")
        
        choice = input("\nWhat would you like to do? (1-3): ").strip()
        
        if choice == "1":
            self.remove_from_cart()
        elif choice == "2":
            self.update_cart_quantity()
    
    def remove_from_cart(self):
        product_id = input("\nEnter Product ID to remove: ").strip()
        
        success, message = self.cart_manager.remove_from_cart(
            self.current_user,
            product_id
        )
        
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")
        
        input("Press Enter to continue...")
    
    def update_cart_quantity(self):
        product_id = input("\nEnter Product ID: ").strip()
        
        try:
            quantity = int(input("Enter new quantity (0 to remove): ").strip())
        except:
            print("\n❌ Please enter a valid number!")
            input("Press Enter to continue...")
            return
        
        if quantity == 0:
            success, message = self.cart_manager.remove_from_cart(
                self.current_user,
                product_id
            )
        else:
            success, message = self.cart_manager.update_quantity(
                self.current_user,
                product_id,
                quantity,
                self.product_manager
            )
        
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")
        
        input("Press Enter to continue...")
    
    def checkout(self):
        self.show_header()
        print("\n--- CHECKOUT ---\n")
        cart = self.cart_manager.get_cart(self.current_user)

        if len(cart) == 0:
            print("Your cart is empty. Add some items first!")
            input("\nPress Enter to continue...")
            return
        
        # Show cart summary
        total = 0
        print(f"{'Product ID':<12} {'Name':<25} {'Qty':<8} {'Price':<12} {'Subtotal':<12}")
        print("-" * 69)
        
        for item in cart:
            product = self.product_manager.find_product_id(item['product_id'])
            if product:
                subtotal = product['price'] * item['quantity']
                total = total + subtotal
                
                print(f"{item['product_id']:<12} ", end="")
                print(f"{product['name']:<25} ", end="")
                print(f"{item['quantity']:<8} ", end="")
                print(f"${product['price']:<11.2f} ", end="")
                print(f"${subtotal:<11.2f}")
        
        print("-" * 69)
        print(f"{'TOTAL:':<48} ${total:.2f}")
        print("=" * 69)

        confirm = input("\nPlace this order? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("\n❌ Checkout cancelled.")
            input("Press Enter to continue...")
            return

        success, message, order_id = self.order_manager.create_order(
            self.current_user,
            cart,
            self.product_manager,
            self.cart_manager
        )
        
        if success:
            print(f"\n✅ {message}")
            print(f"\n📋 Order ID: {order_id}")
            print(f"💰 Total: ${total:.2f}")
            print("\nThank you for your purchase!")

            export = input("\nExport receipt to file? (y/n): ").strip().lower()
            if export == 'y':
                success2, msg2 = self.order_manager.export_receipt(order_id)
                print(f"\n{msg2}")
        else:
            print(f"\n❌ {message}")
        
        input("\nPress Enter to continue...")
    
    def view_order_history(self):
        self.show_header()
        print(f"\n--- ORDER HISTORY ({self.current_user}) ---\n")
        

        orders = self.order_manager.get_user_orders(self.current_user)

        if len(orders) == 0:
            print("You have no orders yet.")
            input("\nPress Enter to continue...")
            return

        for order in orders:
            print("=" * 69)
            print(f"Order ID: {order['order_id']}")
            print(f"Date: {order['timestamp']}")
            print(f"Total: ${order['total']:.2f}")
            print("\nItems:")
            print(f"{'Product ID':<15} {'Quantity':<12} {'Unit Price':<12}")
            print("-" * 69)
            
            for item in order['items']:
                print(f"{item['product_id']:<15} ", end="")
                print(f"{item['quantity']:<12} ", end="")
                print(f"${item['unit_price']:<11.2f}")
            
            print("=" * 69 + "\n")
        
        input("Press Enter to continue...")
    
    def run(self):
        self.welcome_menu()


def main():

    print("\nStarting Mini-Amazon...")
    print("Loading data...")

    app = MiniAmazon()
    app.run()
    
    print("\nThank you for using Mini-Amazon!")
if __name__ == "__main__":
    main()
