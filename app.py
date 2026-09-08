
import streamlit as st
import pandas as pd
import database as db

st.set_page_config(page_title="H&M Fashion POS", page_icon="👗", layout="wide")

# Database စတင်ဆောက်ရွက်ခြင်း
db.init_db()

if "cart" not in st.session_state:
    st.session_state.cart = []

st.markdown("<h1 style='text-align: center; color: #E50914;'>👗 H&M FASHION POS</h1>", unsafe_allow_html=True)
st.divider()

tab_pos, tab_inventory, tab_reports = st.tabs(["🛒 Sales (Checkout)", "📦 Inventory", "📊 Sales Reports"])

# --- TAB 1: POS CHECKOUT ---
with tab_pos:
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("H&M Products Catalogue")
        search_q = st.text_input("🔍 Search Product or Scan Barcode", key="pos_search")
        products_df = db.get_products(search_q)

        for idx, row in products_df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.write(f"**{row['name']}** ({row['size']}/{row['color']})")
                c2.write(f"{row['price']:,.0f} MMK")
                c3.write(f"Stock: {row['stock_quantity']}")
                
                if row['stock_quantity'] > 0:
                    if c4.button("Add 🛒", key=f"add_{row['product_id']}"):
                        found = False
                        for item in st.session_state.cart:
                            if item["id"] == row["product_id"]:
                                if item["qty"] + 1 <= row["stock_quantity"]:
                                    item["qty"] += 1
                                    item["subtotal"] = item["qty"] * item["price"]
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                "id": row["product_id"], "name": row["name"],
                                "price": row["price"], "qty": 1, "subtotal": row["price"]
                            })
                        st.rerun()
                else:
                    c4.warning("Out")
                st.divider()

    with col_right:
        st.subheader("📋 Receipt (H&M Fashion)")
        if not st.session_state.cart:
            st.info("Cart ထဲတွင် ပစ္စည်းမရှိသေးပါ။")
        else:
            cart_df = pd.DataFrame(st.session_state.cart)
            st.dataframe(cart_df[["name", "qty", "price", "subtotal"]], use_container_width=True)

            gross_total = sum(i["subtotal"] for i in st.session_state.cart)
            discount = st.number_input("Discount (MMK)", min_value=0, value=0, step=1000)
            pay_method = st.selectbox("Payment Method", ["Cash", "KPay", "WavePay", "Card"])

            final_total = max(0, gross_total - discount)
            st.metric("Total Amount", f"{final_total:,.0f} MMK")

            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("✅ Checkout", type="primary", use_container_width=True):
                sale_id = db.process_checkout(st.session_state.cart, gross_total, discount, final_total, pay_method)
                st.session_state.cart = []
                st.balloons()
                st.success(f"ဘေလ်ဖြတ်ပြီးပါပြီ။ Sale ID: #{sale_id}")
                st.rerun()

            if c_btn2.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

# --- TAB 2: INVENTORY MANAGEMENT ---
with tab_inventory:
    st.subheader("➕ Add New Product")
    with st.form("add_product_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        p_barcode = f1.text_input("Barcode / Code")
        p_name = f2.text_input("Product Name")
        p_cat = f3.text_input("Category", value="Clothing")
        
        f4, f5, f6, f7 = st.columns(4)
        p_size = f4.text_input("Size (S/M/L/XL)", value="M")
        p_color = f5.text_input("Color", value="Black")
        p_price = f6.number_input("Price (MMK)", min_value=0.0, step=1000.0)
        p_stock = f7.number_input("Initial Stock Qty", min_value=0, step=1)
        
        submit_btn = st.form_submit_button("Save Product 📦")
        if submit_btn:
            if p_barcode and p_name and p_price > 0:
                try:
                    db.add_product(p_barcode, p_name, p_cat, p_size, p_color, p_price, p_stock)
                    st.success(f"'{p_name}' စတော့ခ်ထဲ သို့ အောင်မြင်စွာ ထည့်ပြီးပါပြီ။")
                except Exception as e:
                    st.error(f"Error: Barcode တူညီနေပါသည် သို့မဟုတ် {e}")
            else:
                st.warning("Barcode၊ အမည်နှင့် ဈေးနှုန်း မှန်ကန်စွာ ဖြည့်စွက်ပါ။")

    st.divider()
    st.subheader("📦 Product Stock List")
    st.dataframe(db.get_products(), use_container_width=True)

# --- TAB 3: SALES REPORT ---
with tab_reports:
    st.subheader("📊 Sales History")
    st.dataframe(db.get_sales_report(), use_container_width=True)
  
