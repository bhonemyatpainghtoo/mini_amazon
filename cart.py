from database import get_connection

class CartManager:   
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
    
    def get_cart(self, username):
        user_id = self.get_user_id(username)

        if user_id is None:
            return []

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT product_id, quantity
                FROM cart_items
                WHERE user_id = ?
                """,
                (user_id,)
            )

            rows = cursor.fetchall()

            cart = []

            for row in rows:
                cart.append({
                    "product_id": row[0],
                    "quantity": row[1]
                })

            return cart

        finally:
            conn.close()
    
    def add_to_cart(self, username, product_id, quantity, product_manager):
        if quantity <= 0:
            return False, "Quantity must be greater than zero"

        product_id = product_id.upper().strip()

        user_id = self.get_user_id(username)

        if user_id is None:
            return False, "User not found"

        product = product_manager.find_product_id(product_id)

        if product is None:
            return False, f"Product '{product_id}' not found"

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT quantity
                FROM cart_items
                WHERE user_id = ? AND product_id = ?
                """,
                (user_id, product_id)
            )

            row = cursor.fetchone()

            if row is None:
                new_quantity = quantity
            else:
                current_quantity = row[0]
                new_quantity = current_quantity + quantity

            available, message = product_manager.check_stock(
                product_id,
                new_quantity
            )

            if not available:
                return False, message

            if row is None:
                cursor.execute(
                    """
                    INSERT INTO cart_items
                    (user_id, product_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, product_id, new_quantity)
                )

            else:
                cursor.execute(
                    """
                    UPDATE cart_items
                    SET quantity = ?
                    WHERE user_id = ? AND product_id = ?
                    """,
                    (new_quantity, user_id, product_id)
                )

            conn.commit()

            return True, f"Added {quantity} x {product['name']} to cart"

        finally:
            conn.close()
    
    def remove_from_cart(self, username, product_id):
        product_id = product_id.upper().strip()

        user_id = self.get_user_id(username)

        if user_id is None:
            return False, "User not found"

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM cart_items
                WHERE user_id = ? AND product_id = ?
                """,
                (user_id, product_id)
            )

            if cursor.rowcount == 0:
                return False, f"{product_id} not found in cart"

            conn.commit()

            return True, f"Removed {product_id} from cart"

        finally:
            conn.close()
    
    def update_quantity(self, username, product_id, new_quantity, product_manager):
        if new_quantity <= 0:
            return False, "Quantity must be greater than zero"

        product_id = product_id.upper().strip()

        user_id = self.get_user_id(username)

        if user_id is None:
            return False, "User not found"

        available, message = product_manager.check_stock(
            product_id,
            new_quantity
        )

        if not available:
            return False, message

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE cart_items
                SET quantity = ?
                WHERE user_id = ? AND product_id = ?
                """,
                (new_quantity, user_id, product_id)
            )

            if cursor.rowcount == 0:
                return False, f"{product_id} not found in cart"

            conn.commit()

            return True, f"Updated {product_id} quantity to {new_quantity}"

        finally:
            conn.close()
    
    def clear_cart(self, username):
        user_id = self.get_user_id(username)

        if user_id is None:
            return False, "User not found"

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM cart_items
                WHERE user_id = ?
                """,
                (user_id,)
            )

            conn.commit()

            return True, "Cart cleared"

        finally:
            conn.close()
    
    def calculate_total(self, username, product_manager):
        cart = self.get_cart(username)
        total = 0
        
        for item in cart:
            product = product_manager.find_product_id(item['product_id'])
            if product:
                item_cost = product['price'] * item['quantity']
                total = total + item_cost
        
        return total