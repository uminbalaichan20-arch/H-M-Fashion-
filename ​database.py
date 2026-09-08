import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "hm_fashion_pos.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT UNIQUE,
        name TEXT NOT NULL,
        category TEXT,
        size TEXT,
        color TEXT,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        discount REAL DEFAULT 0,
        final_amount REAL NOT NULL,
        payment_method TEXT DEFAULT 'Cash'
    );

    CREATE TABLE IF NOT EXISTS sale_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL
    );
    ''')
    conn.commit()
    conn.close()

def get_products(search_term=""):
    conn = get_connection()
    if search_term:
        query = "SELECT * FROM products WHERE barcode LIKE ? OR name LIKE ? OR category LIKE ?"
        df = pd.read_sql_query(query, conn, params=(f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
    else:
        df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    return df

def add_product(barcode, name, category, size, color, price, stock):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (barcode, name, category, size, color, price, stock_quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (barcode, name, category, size, color, price, stock))
    conn.commit()
    conn.close()

def process_checkout(cart, gross_total, discount, final_total, pay_method):
    conn = get_connection()
    cursor = conn.cursor()
    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO sales (sale_date, total_amount, discount, final_amount, payment_method)
        VALUES (?, ?, ?, ?, ?)
    ''', (sale_date, gross_total, discount, final_total, pay_method))
    sale_id = cursor.lastrowid

    for item in cart:
        cursor.execute('''
            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (sale_id, item["id"], item["qty"], item["price"], item["subtotal"]))
        cursor.execute('''
            UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?
        ''', (item["qty"], item["id"]))

    conn.commit()
    conn.close()
    return sale_id

def get_sales_report():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM sales ORDER BY sale_id DESC", conn)
    conn.close()
    return df
