from database import get_connection

class ProductManager:
    def get_products(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT product_id, name, price, stock FROM products"
            )

            rows = cursor.fetchall()

            products = []

            for row in rows:
                products.append({
                    "product_id": row[0],
                    "name": row[1],
                    "price": row[2],
                    "stock": row[3]
                })

            return products

        finally:
            conn.close()
    
    def find_product_id(self, product_id):
        product_id = product_id.upper().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT product_id, name, price, stock
                FROM products
                WHERE product_id = ?
                """,
                (product_id,)
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "product_id": row[0],
                "name": row[1],
                "price": row[2],
                "stock": row[3]
            }

        finally:
            conn.close()
    
    def search_products(self, keyword):
        keyword = keyword.strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT product_id, name, price, stock
                FROM products
                WHERE LOWER(name) LIKE LOWER(?)
                """,
                (f"%{keyword}%",)
            )

            rows = cursor.fetchall()

            products = []

            for row in rows:
                products.append({
                    "product_id": row[0],
                    "name": row[1],
                    "price": row[2],
                    "stock": row[3]
                })

            return products

        finally:
            conn.close()
    
    def check_stock(self, product_id, quantity):
        product = self.find_product_id(product_id)
        if product is None:
            return False, f"Product '{product_id}' not found"
        if product['stock'] < quantity:
            return False, f"Not enough stock. Only {product['stock']} available"
        return True, "Stock is available"
    
    def update_stock(self, product_id, quantity_change):
        product_id = product_id.upper().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT stock FROM products WHERE product_id = ?",
                (product_id,)
            )

            row = cursor.fetchone()

            if row is None:
                return False, f"Product '{product_id}' not found"

            current_stock = row[0]
            new_stock = current_stock + quantity_change

            if new_stock < 0:
                return False, "Cannot reduce stock below zero"

            cursor.execute(
                """
                UPDATE products
                SET stock = ?
                WHERE product_id = ?
                """,
                (new_stock, product_id)
            )

            conn.commit()

            return True, f"Stock updated. New stock: {new_stock}"

        finally:
            conn.close()