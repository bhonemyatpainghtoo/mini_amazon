Mini-Amazon E-Commerce System
1. How to Run the Program

    Make sure you have Python 3 installed on your computer.

    Keep all six .py files in the same folder.

    Open your terminal (or Command Prompt/PowerShell).

    Type python main.py and press Enter.

    Follow the menus by typing the number of the action you want to take.

2. Features Implemented

    User Accounts: You can register a new account and log in.

    Security: Passwords are protected using SHA-256 hashing, meaning they are not stored as plain text.

    Product Search: You can see all products or search for specific items by name.

    Smart Cart: You can add/remove items. The system checks if enough stock is available before letting you add an item.

    Checkout: The system calculates the total, updates the inventory, and clears your cart.

    Receipt Export: After buying, you can save your receipt as a .txt file.

3. How Data is Stored

The program saves everything into JSON files so your data is still there when you restart the program.

    users.json: Stores your username and hashed password.

    products.json: Stores the items, prices, and stock levels.

    carts.json: Keeps track of what each user has put in their cart.

    orders.json: A history of every successful purchase with a timestamp.

4. Known Limitations

    Single User: This is a console app designed for one person to use at a time.

    No Admin Menu: Currently, to add new products or change prices, you have to edit the products.json file manually.

    File Storage: It uses simple files instead of a professional database like SQLite.