import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Diwali Snacks Orders",
    page_icon="🪔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile experience
st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        height: 50px;
        font-size: 18px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('diwali_orders.db')
    c = conn.cursor()
    
    # Create items table
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  rate REAL NOT NULL,
                  stock REAL DEFAULT 0)''')
    
    # Create orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer_name TEXT NOT NULL,
                  customer_phone TEXT,
                  customer_address TEXT,
                  delivery_date TEXT NOT NULL,
                  status TEXT DEFAULT 'Active',
                  payment_status TEXT DEFAULT 'Pending',
                  order_date TEXT NOT NULL,
                  notes TEXT)''')
    
    # Create order items table
    c.execute('''CREATE TABLE IF NOT EXISTS order_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  order_id INTEGER,
                  item_name TEXT NOT NULL,
                  quantity REAL NOT NULL,
                  rate REAL NOT NULL,
                  FOREIGN KEY (order_id) REFERENCES orders(id))''')
    
    # Insert default items if not exists
    default_items = [
        ('Besan Laddu', 580),
        ('Chakli',400),
        ('Salty Shankarpade', 380),
        ('Sweet Shankarpade', 380),
        ('Chivda', 290),
        ('Shev (Masala)', 380),
        ('Shev (Simple)', 380),
        ('Karanji', 540),
        ('Anarse', 760)
    ]
    
    for item_name, rate in default_items:
        c.execute('INSERT OR IGNORE INTO items (name, rate, stock) VALUES (?, ?, ?)',
                  (item_name, rate, 0))
    
    conn.commit()
    conn.close()

# Database functions
def get_all_items():
    conn = sqlite3.connect('diwali_orders.db')
    df = pd.read_sql_query("SELECT * FROM items ORDER BY name", conn)
    conn.close()
    return df

def get_all_orders(status=None):
    conn = sqlite3.connect('diwali_orders.db')
    if status:
        df = pd.read_sql_query("SELECT * FROM orders WHERE status=? ORDER BY delivery_date", 
                               conn, params=(status,))
    else:
        df = pd.read_sql_query("SELECT * FROM orders ORDER BY delivery_date", conn)
    conn.close()
    return df

def get_order_items(order_id):
    conn = sqlite3.connect('diwali_orders.db')
    df = pd.read_sql_query("SELECT * FROM order_items WHERE order_id=?", 
                           conn, params=(order_id,))
    conn.close()
    return df

def add_order(customer_name, phone, address, delivery_date, items_data, payment_status, notes):
    conn = sqlite3.connect('diwali_orders.db')
    c = conn.cursor()
    
    order_date = datetime.now().strftime('%Y-%m-%d')
    
    c.execute('''INSERT INTO orders 
                 (customer_name, customer_phone, customer_address, delivery_date, 
                  order_date, payment_status, notes, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')''',
              (customer_name, phone, address, delivery_date, order_date, payment_status, notes))
    
    order_id = c.lastrowid
    
    for item in items_data:
        c.execute('''INSERT INTO order_items (order_id, item_name, quantity, rate)
                     VALUES (?, ?, ?, ?)''',
                  (order_id, item['name'], item['quantity'], item['rate']))
    
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, new_status):
    conn = sqlite3.connect('diwali_orders.db')
    c = conn.cursor()
    c.execute('UPDATE orders SET status=? WHERE id=?', (new_status, order_id))
    conn.commit()
    conn.close()

def update_stock(item_name, quantity):
    conn = sqlite3.connect('diwali_orders.db')
    c = conn.cursor()
    c.execute('UPDATE items SET stock=? WHERE name=?', (quantity, item_name))
    conn.commit()
    conn.close()

def delete_order(order_id):
    conn = sqlite3.connect('diwali_orders.db')
    c = conn.cursor()
    c.execute('DELETE FROM order_items WHERE order_id=?', (order_id,))
    c.execute('DELETE FROM orders WHERE id=?', (order_id,))
    conn.commit()
    conn.close()

def get_stock_vs_orders():
    conn = sqlite3.connect('diwali_orders.db')
    
    # Get current stock
    stock_df = pd.read_sql_query("SELECT name, stock FROM items", conn)
    
    # Get required quantities from active orders
    required_df = pd.read_sql_query("""
        SELECT oi.item_name, SUM(oi.quantity) as required
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'Active'
        GROUP BY oi.item_name
    """, conn)
    
    conn.close()
    
    # Merge the dataframes
    result = stock_df.merge(required_df, left_on='name', right_on='item_name', how='left')
    result['required'] = result['required'].fillna(0)
    result['difference'] = result['stock'] - result['required']
    
    return result[['name', 'stock', 'required', 'difference']]

# Initialize database
init_db()

# Sidebar navigation
st.sidebar.title("🪔 Diwali Orders")
page = st.sidebar.radio("Navigation", 
                        ["📊 Dashboard", "📝 New Order", "📋 All Orders", 
                         "📦 Inventory", "📈 Stock Analysis"])

# Dashboard Page
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    # Get statistics
    all_orders = get_all_orders()
    active_orders = get_all_orders('Active')
    completed_orders = get_all_orders('Completed')
    
    today = date.today().strftime('%Y-%m-%d')
    todays_deliveries = active_orders[active_orders['delivery_date'] == today] if len(active_orders) > 0 else pd.DataFrame()
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔄 Active Orders", len(active_orders))
    with col2:
        st.metric("✅ Completed", len(completed_orders))
    with col3:
        st.metric("📅 Today's Deliveries", len(todays_deliveries))
    with col4:
        total_revenue = 0
        for _, order in active_orders.iterrows():
            items = get_order_items(order['id'])
            total_revenue += (items['quantity'] * items['rate']).sum()
        st.metric("💰 Active Orders Value", f"₹{total_revenue:,.0f}")
    
    st.divider()
    
    # Today's Deliveries
    if len(todays_deliveries) > 0:
        st.subheader("📅 Today's Deliveries")
        for _, order in todays_deliveries.iterrows():
            with st.expander(f"👤 {order['customer_name']} - ₹{order['id']}"):
                items = get_order_items(order['id'])
                st.dataframe(items[['item_name', 'quantity', 'rate']], hide_index=True)
                total = (items['quantity'] * items['rate']).sum()
                st.write(f"**Total: ₹{total:,.2f}**")
    
    st.divider()
    
    # Low stock alerts
    st.subheader("⚠️ Stock Alerts")
    stock_data = get_stock_vs_orders()
    low_stock = stock_data[stock_data['difference'] < 5]
    
    if len(low_stock) > 0:
        for _, item in low_stock.iterrows():
            if item['difference'] < 0:
                st.error(f"🔴 {item['name']}: Short by {abs(item['difference']):.1f} kg!")
            else:
                st.warning(f"🟡 {item['name']}: Only {item['stock']:.1f} kg remaining")
    else:
        st.success("✅ All items have sufficient stock!")

# New Order Page
elif page == "📝 New Order":
    st.title("📝 Create New Order")
    
    with st.form("new_order_form"):
        st.subheader("Customer Details")
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name *", placeholder="Enter name")
            customer_phone = st.text_input("Phone Number", placeholder="10-digit number")
        
        with col2:
            delivery_date = st.date_input("Delivery Date *", min_value=date.today())
            payment_status = st.selectbox("Payment Status", ["Pending", "Paid", "Partial"])
        
        customer_address = st.text_area("Delivery Address", placeholder="Enter full address")
        notes = st.text_area("Special Notes", placeholder="Any special instructions")
        
        st.divider()
        st.subheader("Order Items")
        
        items_df = get_all_items()
        selected_items = []
        
        for _, item in items_df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"**{item['name']}**")
            with col2:
                st.write(f"₹{item['rate']}/kg")
            with col3:
                qty = st.number_input(f"Qty (kg)", min_value=0.0, max_value=1000.0, 
                                     step=0.5, key=f"qty_{item['id']}", label_visibility="collapsed")
                if qty > 0:
                    selected_items.append({
                        'name': item['name'],
                        'quantity': qty,
                        'rate': item['rate']
                    })
        
        st.divider()
        
        # Calculate total
        if selected_items:
            total = sum(item['quantity'] * item['rate'] for item in selected_items)
            st.subheader(f"💰 Total Amount: ₹{total:,.2f}")
        
        submitted = st.form_submit_button("✅ Create Order", use_container_width=True)
        
        if submitted:
            if not customer_name:
                st.error("Please enter customer name!")
            elif not selected_items:
                st.error("Please select at least one item!")
            else:
                order_id = add_order(customer_name, customer_phone, customer_address, 
                                   delivery_date.strftime('%Y-%m-%d'), selected_items, 
                                   payment_status, notes)
                st.success(f"✅ Order #{order_id} created successfully!")
                st.balloons()

# All Orders Page
elif page == "📋 All Orders":
    st.title("📋 All Orders")
    
    tab1, tab2 = st.tabs(["🔄 Active Orders", "✅ Completed Orders"])
    
    with tab1:
        active_orders = get_all_orders('Active')
        
        if len(active_orders) > 0:
            for _, order in active_orders.iterrows():
                delivery = datetime.strptime(order['delivery_date'], '%Y-%m-%d').date()
                days_left = (delivery - date.today()).days
                
                if days_left < 0:
                    date_color = "🔴"
                    date_text = f"OVERDUE by {abs(days_left)} days"
                elif days_left == 0:
                    date_color = "🟠"
                    date_text = "TODAY"
                elif days_left == 1:
                    date_color = "🟡"
                    date_text = "TOMORROW"
                else:
                    date_color = "🟢"
                    date_text = f"in {days_left} days"
                
                with st.expander(f"{date_color} {order['customer_name']} - {date_text}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**📱 Phone:** {order['customer_phone'] or 'N/A'}")
                        st.write(f"**📍 Address:** {order['customer_address'] or 'N/A'}")
                        st.write(f"**📅 Delivery:** {order['delivery_date']}")
                        st.write(f"**💳 Payment:** {order['payment_status']}")
                        if order['notes']:
                            st.write(f"**📝 Notes:** {order['notes']}")
                    
                    with col2:
                        if st.button("✅ Complete", key=f"complete_{order['id']}", use_container_width=True):
                            update_order_status(order['id'], 'Completed')
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"delete_{order['id']}", use_container_width=True):
                            delete_order(order['id'])
                            st.rerun()
                    
                    st.divider()
                    
                    # Order items
                    items = get_order_items(order['id'])
                    items['Amount'] = items['quantity'] * items['rate']
                    
                    st.dataframe(
                        items[['item_name', 'quantity', 'rate', 'Amount']].rename(columns={
                            'item_name': 'Item',
                            'quantity': 'Qty (kg)',
                            'rate': 'Rate (₹/kg)'
                        }),
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    total = items['Amount'].sum()
                    st.markdown(f"### **Total: ₹{total:,.2f}**")
        else:
            st.info("No active orders found!")
    
    with tab2:
        completed_orders = get_all_orders('Completed')
        
        if len(completed_orders) > 0:
            for _, order in completed_orders.iterrows():
                with st.expander(f"✅ {order['customer_name']} - {order['delivery_date']}", expanded=False):
                    st.write(f"**📱 Phone:** {order['customer_phone'] or 'N/A'}")
                    st.write(f"**💳 Payment:** {order['payment_status']}")
                    
                    items = get_order_items(order['id'])
                    items['Amount'] = items['quantity'] * items['rate']
                    
                    st.dataframe(
                        items[['item_name', 'quantity', 'rate', 'Amount']].rename(columns={
                            'item_name': 'Item',
                            'quantity': 'Qty (kg)',
                            'rate': 'Rate (₹/kg)'
                        }),
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    total = items['Amount'].sum()
                    st.markdown(f"### **Total: ₹{total:,.2f}**")
                    
                    if st.button("🔄 Reactivate", key=f"reactivate_{order['id']}"):
                        update_order_status(order['id'], 'Active')
                        st.rerun()
        else:
            st.info("No completed orders found!")

# Inventory Page
elif page == "📦 Inventory":
    st.title("📦 Inventory Management")
    
    items_df = get_all_items()
    
    st.subheader("Update Stock Levels")
    
    for _, item in items_df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.write(f"**{item['name']}**")
        
        with col2:
            st.write(f"₹{item['rate']}/kg")
        
        with col3:
            current_stock = item['stock']
            new_stock = st.number_input(
                "Stock (kg)", 
                min_value=0.0, 
                value=float(current_stock),
                step=0.5,
                key=f"stock_{item['id']}",
                label_visibility="collapsed"
            )
        
        with col4:
            if st.button("💾", key=f"save_{item['id']}", help="Save"):
                if new_stock != current_stock:
                    update_stock(item['name'], new_stock)
                    st.success("✅")
    
    st.divider()
    
    # Stock summary
    st.subheader("📊 Stock Summary")
    total_stock_value = (items_df['stock'] * items_df['rate']).sum()
    st.metric("Total Inventory Value", f"₹{total_stock_value:,.2f}")

# Stock Analysis Page
elif page == "📈 Stock Analysis":
    st.title("📈 Stock vs Orders Analysis")
    
    analysis_df = get_stock_vs_orders()
    
    st.subheader("Current Status")
    
    for _, item in analysis_df.iterrows():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write(f"**{item['name']}**")
        
        with col2:
            st.metric("Available", f"{item['stock']:.1f} kg")
        
        with col3:
            st.metric("Required", f"{item['required']:.1f} kg")
        
        with col4:
            diff = item['difference']
            if diff < 0:
                st.metric("Status", f"{abs(diff):.1f} kg", delta=f"Short", delta_color="inverse")
            elif diff < 5:
                st.metric("Status", f"+{diff:.1f} kg", delta="Low", delta_color="off")
            else:
                st.metric("Status", f"+{diff:.1f} kg", delta="OK", delta_color="normal")
        
        st.divider()
    
    # Shopping list
    shortage_items = analysis_df[analysis_df['difference'] < 5]
    
    if len(shortage_items) > 0:
        st.subheader("🛒 Shopping List")
        st.info("Items to purchase/prepare:")
        
        for _, item in shortage_items.iterrows():
            needed = max(0, 10 - item['stock'])  # Keep buffer of 10kg
            st.write(f"- **{item['name']}**: {needed:.1f} kg")

# Footer
st.sidebar.divider()
st.sidebar.info("🪔 **Diwali Snacks Order Manager**\n\nBuilt with Python & Streamlit")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")