import pymysql

def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='HintalDiez()25',
            database='floralsoul_data',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Connected to MySQL database")
        return connection

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return None

def fetch_products():
    connection = create_connection()
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()
        connection.close()
        return products

if __name__ == '__main__':
    products = fetch_products() or []
    for product in products:
        print(f"ID: {product['id']}, Name: {product['name']}, Price: ${product['price']}, "
              f"Category: {product['category']}, Size: {product['size']}, "
              f"Added: {product['created_at']}")

