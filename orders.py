from database import get_connection
from datetime import datetime

class OrderManager:    
    def get_user_id(self, username):
        username = username.lower().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return row[0]

        finally:
            conn.close()

    def generate_order_id(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT order_id
                FROM orders
                ORDER BY order_id DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

            if row is None:
                return "O0001"

            last_order_id = row[0]
            number = int(last_order_id[1:])
            next_number = number + 1

            return f"O{next_number:04d}"

        finally:
            conn.close()
    
    def create_order(self, username, cart_items, product_manager, cart_manager):
        username = username.lower().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Start checkout as one database transaction
            conn.execute("BEGIN IMMEDIATE")

            # Find the user's SQLite ID
            cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )

            user_row = cursor.fetchone()

            if user_row is None:
                conn.rollback()
                return False, "User not found", None

            user_id = user_row[0]

            # Get the user's current cart directly from SQLite
            cursor.execute(
                """
                SELECT
                    cart_items.product_id,
                    cart_items.quantity,
                    products.price,
                    products.stock
                FROM cart_items
                JOIN products
                    ON cart_items.product_id = products.product_id
                WHERE cart_items.user_id = ?
                """,
                (user_id,)
            )

            rows = cursor.fetchall()

            if len(rows) == 0:
                conn.rollback()
                return False, "Your cart is empty", None

            total_cost = 0
            order_items = []

            # Check stock and calculate total
            for row in rows:
                product_id = row[0]
                quantity = row[1]
                unit_price = row[2]
                stock = row[3]

                if stock < quantity:
                    conn.rollback()
                    return (
                        False,
                        f"Not enough stock for {product_id}. "
                        f"Only {stock} available",
                        None
                    )

                total_cost += unit_price * quantity

                order_items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price
                })

            # Generate next order ID
            cursor.execute("""
                SELECT COALESCE(
                    MAX(CAST(SUBSTR(order_id, 2) AS INTEGER)),
                    0
                )
                FROM orders
            """)

            last_number = cursor.fetchone()[0]
            order_id = f"O{last_number + 1:04d}"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create the order
            cursor.execute(
                """
                INSERT INTO orders
                (order_id, user_id, total, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    user_id,
                    total_cost,
                    timestamp
                )
            )

            # Save each item and reduce inventory
            for item in order_items:
                cursor.execute(
                    """
                    INSERT INTO order_items
                    (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"]
                    )
                )

                cursor.execute(
                    """
                    UPDATE products
                    SET stock = stock - ?
                    WHERE product_id = ?
                    """,
                    (
                        item["quantity"],
                        item["product_id"]
                    )
                )

            # Clear the cart
            cursor.execute(
                """
                DELETE FROM cart_items
                WHERE user_id = ?
                """,
                (user_id,)
            )

            # Everything succeeded
            conn.commit()

            return True, "Order placed successfully!", order_id

        except Exception as error:
            conn.rollback()
            return False, f"Order failed: {error}", None

        finally:
            conn.close()
    
    def get_user_orders(self, username):
        username = username.lower().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    orders.order_id,
                    users.username,
                    orders.total,
                    orders.timestamp
                FROM orders
                JOIN users
                    ON orders.user_id = users.id
                WHERE users.username = ?
                ORDER BY orders.timestamp DESC
                """,
                (username,)
            )

            order_rows = cursor.fetchall()

            user_orders = []

            for order_row in order_rows:
                order_id = order_row[0]

                cursor.execute(
                    """
                    SELECT
                        product_id,
                        quantity,
                        unit_price
                    FROM order_items
                    WHERE order_id = ?
                    """,
                    (order_id,)
                )

                item_rows = cursor.fetchall()

                items = []

                for item_row in item_rows:
                    items.append({
                        "product_id": item_row[0],
                        "quantity": item_row[1],
                        "unit_price": item_row[2]
                    })

                user_orders.append({
                    "order_id": order_row[0],
                    "username": order_row[1],
                    "total": order_row[2],
                    "timestamp": order_row[3],
                    "items": items
                })

            return user_orders

        finally:
            conn.close()
    
    def find_order_by_id(self, order_id):
        order_id = order_id.upper().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    orders.order_id,
                    users.username,
                    orders.total,
                    orders.timestamp
                FROM orders
                JOIN users
                    ON orders.user_id = users.id
                WHERE orders.order_id = ?
                """,
                (order_id,)
            )

            order_row = cursor.fetchone()

            if order_row is None:
                return None

            cursor.execute(
                """
                SELECT
                    product_id,
                    quantity,
                    unit_price
                FROM order_items
                WHERE order_id = ?
                """,
                (order_id,)
            )

            item_rows = cursor.fetchall()

            items = []

            for item_row in item_rows:
                items.append({
                    "product_id": item_row[0],
                    "quantity": item_row[1],
                    "unit_price": item_row[2]
                })

            return {
                "order_id": order_row[0],
                "username": order_row[1],
                "total": order_row[2],
                "timestamp": order_row[3],
                "items": items
            }

        finally:
            conn.close()
    
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