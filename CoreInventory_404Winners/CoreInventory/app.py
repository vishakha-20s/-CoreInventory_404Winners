from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
from functools import wraps
import urllib.request
import json
import os

app = Flask(__name__)
app.secret_key = 'coreinventory404winners'

def get_db():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'rain@forever123'),
        database=os.environ.get('DB_NAME', 'coreinventory')
    )

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data     = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        db = get_db()
        c  = db.cursor(dictionary=True)
        c.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = c.fetchone()
        db.close()
        if user:
            session['user'] = username
            if request.is_json:
                return jsonify({'success': True})
            return redirect('/dashboard')
        else:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Invalid username or password!'
                })
            return render_template('login.html',
                error='Invalid username or password!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data     = request.get_json()
            fullname = data.get('fullname')
            username = data.get('username')
            email    = data.get('email')
            password = data.get('password')
        else:
            fullname = request.form.get('fullname')
            username = request.form.get('username')
            email    = request.form.get('email')
            password = request.form.get('password')
        db = get_db()
        c  = db.cursor(dictionary=True)
        c.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )
        existing = c.fetchone()
        if existing:
            db.close()
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Username already taken!'
                })
            return render_template('register.html',
                error='Username already taken!')
        c.execute(
            "INSERT INTO users (fullname, username, email, password) VALUES (%s,%s,%s,%s)",
            (fullname, username, email, password)
        )
        db.commit()
        db.close()
        if request.is_json:
            return jsonify({'success': True})
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    c  = db.cursor(dictionary=True)
    c.execute("SELECT COUNT(*) as total FROM products")
    total_products = c.fetchone()['total']
    c.execute(
        "SELECT COUNT(*) as low FROM products WHERE quantity <= min_stock"
    )
    low_stock = c.fetchone()['low']
    c.execute(
        "SELECT COUNT(*) as pending FROM movements WHERE type='receipt' AND date >= CURDATE()"
    )
    pending_receipts = c.fetchone()['pending']
    c.execute(
        "SELECT COUNT(*) as pending FROM movements WHERE type='delivery' AND date >= CURDATE()"
    )
    pending_deliveries = c.fetchone()['pending']
    c.execute(
        "SELECT * FROM products ORDER BY quantity ASC LIMIT 5"
    )
    low_items = c.fetchall()
    db.close()
    return render_template('dashboard.html',
        total_products=total_products,
        low_stock=low_stock,
        pending_receipts=pending_receipts,
        pending_deliveries=pending_deliveries,
        low_items=low_items
    )

@app.route('/products')
@login_required
def products():
    db = get_db()
    c  = db.cursor(dictionary=True)
    c.execute("SELECT * FROM products")
    all_products = c.fetchall()
    db.close()
    return render_template('products.html',
        products=all_products)

@app.route('/products/add', methods=['POST'])
@login_required
def add_product():
    name      = request.form['name']
    sku       = request.form['sku']
    category  = request.form['category']
    quantity  = request.form['quantity']
    unit      = request.form['unit']
    min_stock = request.form['min_stock']
    db = get_db()
    c  = db.cursor()
    c.execute(
        "INSERT INTO products (name, sku, category, quantity, unit, min_stock) VALUES (%s,%s,%s,%s,%s,%s)",
        (name, sku, category, quantity, unit, min_stock)
    )
    db.commit()
    db.close()
    return redirect('/products')

@app.route('/receipts', methods=['GET', 'POST'])
@login_required
def receipts():
    db = get_db()
    c  = db.cursor(dictionary=True)
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity   = int(request.form['quantity'])
        note       = request.form['note']
        c.execute(
            "UPDATE products SET quantity = quantity + %s WHERE id = %s",
            (quantity, product_id)
        )
        c.execute(
            "INSERT INTO movements (product_id, type, quantity, note) VALUES (%s, 'receipt', %s, %s)",
            (product_id, quantity, note)
        )
        db.commit()
        return redirect('/receipts')
    c.execute("SELECT * FROM products")
    all_products = c.fetchall()
    c.execute("""
        SELECT m.*, p.name as product_name
        FROM movements m
        JOIN products p ON m.product_id = p.id
        WHERE m.type='receipt'
        ORDER BY m.date DESC
    """)
    movements = c.fetchall()
    db.close()
    return render_template('receipts.html',
        products=all_products, movements=movements)

@app.route('/delivery', methods=['GET', 'POST'])
@login_required
def delivery():
    db = get_db()
    c  = db.cursor(dictionary=True)
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity   = int(request.form['quantity'])
        note       = request.form['note']
        c.execute(
            "SELECT quantity FROM products WHERE id = %s",
            (product_id,)
        )
        product = c.fetchone()
        if product['quantity'] < quantity:
            c.execute("SELECT * FROM products")
            all_products = c.fetchall()
            return render_template('delivery.html',
                error='Not enough stock!',
                products=all_products)
        c.execute(
            "UPDATE products SET quantity = quantity - %s WHERE id = %s",
            (quantity, product_id)
        )
        c.execute(
            "INSERT INTO movements (product_id, type, quantity, note) VALUES (%s, 'delivery', %s, %s)",
            (product_id, quantity, note)
        )
        db.commit()
        return redirect('/delivery')
    c.execute("SELECT * FROM products")
    all_products = c.fetchall()
    c.execute("""
        SELECT m.*, p.name as product_name
        FROM movements m
        JOIN products p ON m.product_id = p.id
        WHERE m.type='delivery'
        ORDER BY m.date DESC
    """)
    movements = c.fetchall()
    db.close()
    return render_template('delivery.html',
        products=all_products, movements=movements)

@app.route('/adjustment', methods=['GET', 'POST'])
@login_required
def adjustment():
    db = get_db()
    c  = db.cursor(dictionary=True)
    if request.method == 'POST':
        product_id   = request.form['product_id']
        new_quantity = int(request.form['new_quantity'])
        note         = request.form['note']
        c.execute(
            "SELECT quantity FROM products WHERE id=%s",
            (product_id,)
        )
        old  = c.fetchone()
        diff = new_quantity - old['quantity']
        c.execute(
            "UPDATE products SET quantity=%s WHERE id=%s",
            (new_quantity, product_id)
        )
        c.execute(
            "INSERT INTO movements (product_id, type, quantity, note) VALUES (%s,'adjustment',%s,%s)",
            (product_id, diff, note)
        )
        db.commit()
        db.close()
        return redirect('/adjustment')
    c.execute("SELECT * FROM products")
    all_products = c.fetchall()
    c.execute("""
        SELECT m.*, p.name as product_name
        FROM movements m
        JOIN products p ON m.product_id = p.id
        WHERE m.type='adjustment'
        ORDER BY m.date DESC
    """)
    movements = c.fetchall()
    db.close()
    return render_template('adjustment.html',
        products=all_products, movements=movements)

@app.route('/stock')
@login_required
def stock():
    db = get_db()
    c  = db.cursor(dictionary=True)
    c.execute("SELECT * FROM products ORDER BY quantity ASC")
    all_products = c.fetchall()
    db.close()
    return render_template('stock.html',
        products=all_products)

@app.route('/move_history')
@login_required
def move_history():
    db = get_db()
    c  = db.cursor(dictionary=True)
    c.execute("""
        SELECT m.*, p.name as product_name
        FROM movements m
        JOIN products p ON m.product_id = p.id
        ORDER BY m.date DESC
    """)
    movements = c.fetchall()
    db.close()
    return render_template('move_history.html',
        movements=movements)

@app.route('/transfer')
@login_required
def transfer():
    return render_template('transfer.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    user_message = request.json.get('message')
    db = get_db()
    c  = db.cursor(dictionary=True)
    c.execute(
        "SELECT * FROM products WHERE quantity <= min_stock"
    )
    low_items = c.fetchall()
    c.execute("SELECT COUNT(*) as total FROM products")
    total = c.fetchone()['total']
    db.close()

    inventory_context = f"""
    You are an AI Inventory Assistant for CoreInventory system.
    Current inventory data:
    - Total products: {total}
    - Low stock items: {[item['name'] + ' (qty: ' + str(item['quantity']) + ')' for item in low_items]}
    Answer the user's question about inventory in a helpful, concise way.
    Use emojis to make responses friendly.
    """

    api_key = os.environ.get('ANTHROPIC_API_KEY', 'YOUR_API_KEY_HERE')

    data = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": 300,
        "system": inventory_context,
        "messages": [{"role": "user", "content": user_message}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            reply  = result['content'][0]['text']
    except Exception as e:
        reply = "🤖 AI assistant is currently unavailable. Please check your API key!"

    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)