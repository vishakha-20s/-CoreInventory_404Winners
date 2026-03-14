import mysql.connector

def init_db():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='rain@forever123'
    )
    c = conn.cursor()
    c.execute("DROP DATABASE IF EXISTS coreinventory")
    c.execute("CREATE DATABASE IF NOT EXISTS coreinventory")
    conn.close()
    print("✅ Database created!")

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='rain@forever123',
        database='coreinventory'
    )
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id       INT AUTO_INCREMENT PRIMARY KEY,
        fullname VARCHAR(200),
        username VARCHAR(100) UNIQUE NOT NULL,
        email    VARCHAR(200),
        password VARCHAR(100) NOT NULL
    )''')
    print("✅ Users table created!")

    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id        INT AUTO_INCREMENT PRIMARY KEY,
        name      VARCHAR(200) NOT NULL,
        sku       VARCHAR(100) UNIQUE NOT NULL,
        category  VARCHAR(100),
        quantity  INT DEFAULT 0,
        unit      VARCHAR(50),
        min_stock INT DEFAULT 10
    )''')
    print("✅ Products table created!")

    c.execute('''CREATE TABLE IF NOT EXISTS movements (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT,
        type       VARCHAR(50),
        quantity   INT,
        note       TEXT,
        date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    print("✅ Movements table created!")

    try:
        c.execute(
            "INSERT INTO products (name, sku, category, quantity, unit, min_stock) VALUES (%s,%s,%s,%s,%s,%s)",
            ('Steel Rods', 'SKU001', 'Metal', 8, 'kg', 50)
        )
        c.execute(
            "INSERT INTO products (name, sku, category, quantity, unit, min_stock) VALUES (%s,%s,%s,%s,%s,%s)",
            ('Plastic Chairs', 'SKU002', 'Plastic', 3, 'pcs', 20)
        )
        c.execute(
            "INSERT INTO products (name, sku, category, quantity, unit, min_stock) VALUES (%s,%s,%s,%s,%s,%s)",
            ('Wooden Planks', 'SKU003', 'Wood', 75, 'pcs', 30)
        )
        c.execute(
            "INSERT INTO products (name, sku, category, quantity, unit, min_stock) VALUES (%s,%s,%s,%s,%s,%s)",
            ('Iron Sheets', 'SKU004', 'Metal', 12, 'pcs', 40)
        )
        c.execute(
            "INSERT INTO products (name, sku, category, quantity, unit, min_stock) VALUES (%s,%s,%s,%s,%s,%s)",
            ('Cement Bags', 'SKU005', 'Chemical', 120, 'bags', 50)
        )
        print("✅ Sample products added!")
    except:
        print("⚠️ Products already exist!")

    try:
        c.execute(
            "INSERT INTO users (fullname, username, email, password) VALUES (%s,%s,%s,%s)",
            ('Admin User', 'admin', 'admin@coreinventory.com', 'admin123')
        )
        print("✅ Admin user created!")
    except:
        print("⚠️ Admin already exists!")

    conn.commit()
    conn.close()
    print("")
    print("🎉 All done!")
    print("========================")
    print("Login with:")
    print("Username: admin")
    print("Password: admin123")
    print("========================")

if __name__ == '__main__':
    init_db()

