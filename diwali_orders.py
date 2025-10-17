import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
import json

# Page configuration
st.set_page_config(
    page_title="Diwali Snacks Orders",
    page_icon="🪔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    </style>
    """, unsafe_allow_html=True)

# Initialize Google Sheets connection
@st.cache_resource
def init_connection():
    try:
        # Get credentials from Streamlit secrets
        credentials_dict = dict(st.secrets["gcp_service_account"])
        
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scope
        )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        st.info("Please check your credentials in Streamlit secrets")
        return None

# Connect to specific spreadsheet
def get_spreadsheet():
    try:
        client = init_connection()
        if client:
            sheet_url = st.secrets["spreadsheet_url"]
            return client.open_by_url(sheet_url)
        return None
    except Exception as e:
        st.error(f"Error opening spreadsheet: {e}")
        return None

# Get all items
def get_all_items():
    try:
        spreadsheet = get_spreadsheet()
        if spreadsheet:
            worksheet = spreadsheet.worksheet("items")
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        return pd.DataFrame(columns=['name', 'rate', 'stock'])
    except Exception as e:
        st.error(f"Error reading items: {e}")
        return pd.DataFrame(columns=['name', 'rate', 'stock'])

# Get all orders
def get_all_orders(status=None):
    try:
        spreadsheet = get_spreadsheet()
        if spreadsheet:
            worksheet = spreadsheet.worksheet("orders")
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            if len(df) > 0:
                if status:
                    df = df[df['status'] == status]
                return df.sort_values('delivery_date')
            return df
        return pd.DataFrame(columns=['id', 'customer_name', 'customer_phone', 'customer_address', 
                                    'delivery_date', 'status', 'payment_status', 'order_date', 'notes'])
    except Exception as e:
        st.error(f"Error reading orders: {e}")
        return pd.DataFrame()

# Get order items
def get_order_items(order_id):
    try:
        spreadsheet = get_spreadsheet()
        if spreadsheet:
            worksheet = spreadsheet.worksheet("order_items")
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            if len(df) > 0:
                return df[df['order_id'] == order_id]
            return df
        return pd.DataFrame(columns=['order_id', 'item_name', 'quantity', 'rate'])
    except Exception as e:
        st.error(f"Error reading order items: {e}")
        return pd.DataFrame()

# Add new order
def add_order(customer_name, phone, address, delivery_date, items_data, payment_status, notes):
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return None
        
        # Get next order ID
        orders_ws = spreadsheet.worksheet("orders")
        existing_orders = orders_ws.get_all_records()
        next_id = max([o['id'] for o in existing_orders], default=0) + 1
        
        order_date = datetime.now().strftime('%Y-%m-%d')
        
        # Add to orders sheet
        new_order = [next_id, customer_name, phone or "", address or "", 
                    delivery_date, "Active", payment_status, order_date, notes or ""]
        orders_ws.append_row(new_order)
        
        # Add to order_items sheet
        items_ws = spreadsheet.worksheet("order_items")
        for item in items_data:
            item_row = [next_id, item['name'], item['quantity'], item['rate']]
            items_ws.append_row(item_row)
        
        return next_id
    except Exception as e:
        st.error(f"Error adding order: {e}")
        return None

# Update order status
def update_order_status(order_id, new_status):
    try:
        spreadsheet = get_spreadsheet()
        if spreadsheet:
            worksheet = spreadsheet.worksheet("orders")
            cell = worksheet.find(str(order_id))
            
            if cell:
                # Status is in column 6 (F)
                worksheet.update_cell(cell.row, 6, new_status)
                return True
        return False
    except Exception as e:
        st.error(f"Error updating status: {e}")
        return False

# Update stock
def update_stock(item_name, quantity):
    try:
        spreadsheet = get_spreadsheet()
        if spreadsheet:
            worksheet = spreadsheet.worksheet("items")
            cell = worksheet.find(item_name)
            
            if cell:
                # Stock is in column 3 (C)
                worksheet.update_cell(cell.row, 3, quantity)
                return True
        return False
    except Exception as e:
        st.error(f"Error updating stock: {e}")
        return False

# Delete order
def delete_order(order_id):
    try:
        spreadsheet = get_spreadsheet()
        if spreadsheet:
            # Delete from orders
            orders_ws = spreadsheet.worksheet("orders")
            cell = orders_ws.find(str(order_id))
            if cell:
                orders_ws.delete_rows(cell.row)
            
            # Delete from order_items
            items_ws = spreadsheet.worksheet("order_items")
            all_data = items_ws.get_all_values()
            rows_to_delete = []
            
            for idx, row in enumerate(all_data[1:], start=2):  # Skip header
                if str(row[0]) == str(order_id):
                    rows_to_delete.append(idx)
            
            # Delete in reverse order to maintain row numbers
            for row_num in reversed(rows_to_delete):
                items_ws.delete_rows(row_num)
            
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting order: {e}")
        return False

# Get stock vs orders analysis
def get_stock_vs_orders():
    try:
        items_df = get_all_items()
        active_orders = get_all_orders('Active')
        
        if len(items_df) == 0:
            return pd.DataFrame(columns=['name', 'stock', 'required', 'difference'])
        
        # Calculate required quantities
        required = {}
        if len(active_orders) > 0:
            for _, order in active_orders.iterrows():
                order_items = get_order_items(order['id'])
                for _, item in order_items.iterrows():
                    item_name = item['item_name']
                    qty = item['quantity']
                    required[item_name] = required.get(item_name, 0) + qty
        
        # Create result dataframe
        result = items_df.copy()
        result['required'] = result['name'].map(required).fillna(0)
        result['difference'] = result['stock'] - result['required']
        
        return result[['name', 'stock', 'required', 'difference']]
    except Exception as e:
        st.error(f"Error in stock analysis: {e}")
        return pd.DataFrame()

# Sidebar navigation
st.sidebar.title("🪔 Diwali Orders")
st.sidebar.info("✅ Connected to Google Sheets - Your data is safe!")
page = st.sidebar.radio("Navigation", 
                        ["📊 Dashboard", "📝 New Order", "📋 All Orders", 
                         "📦 Inventory", "📈 Stock Analysis"])

# Dashboard Page
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    all_orders = get_all_orders()
    active_orders = get_all_orders('Active')
    completed_orders = get_all_orders('Completed')
    
    today = date.today().strftime('%Y-%m-%d')
    todays_deliveries = active_orders[active_orders['delivery_date'] == today] if len(active_orders) > 0 else pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔄 Active Orders", len(active_orders))
    with col2:
        st.metric("✅ Completed", len(completed_orders))
    with col3:
        st.metric("📅 Today's Deliveries", len(todays_deliveries))
    with col4:
        total_revenue = 0
        if len(active_orders) > 0:
            for _, order in active_orders.iterrows():
                items = get_order_items(order['id'])
                if len(items) > 0:
                    total_revenue += (items['quantity'] * items['rate']).sum()
        st.metric("💰 Active Orders Value", f"₹{total_revenue:,.0f}")
    
    st.divider()
    
    if len(todays_deliveries) > 0:
        st.subheader("📅 Today's Deliveries")
        for _, order in todays_deliveries.iterrows():
            with st.expander(f"👤 {order['customer_name']}"):
                items = get_order_items(order['id'])
                if len(items) > 0:
                    st.dataframe(items[['item_name', 'quantity', 'rate']], hide_index=True)
                    total = (items['quantity'] * items['rate']).sum()
                    st.write(f"**Total: ₹{total:,.2f}**")
    
    st.divider()
    
    st.subheader("⚠️ Stock Alerts")
    stock_data = get_stock_vs_orders()
    if len(stock_data) > 0:
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
        
        if len(items_df) > 0:
            for idx, item in items_df.iterrows():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(f"**{item['name']}**")
                with col2:
                    st.write(f"₹{item['rate']}/kg")
                with col3:
                    qty = st.number_input(f"Qty (kg)", min_value=0.0, max_value=1000.0, 
                                         step=0.5, key=f"qty_{idx}", label_visibility="collapsed")
                    if qty > 0:
                        selected_items.append({
                            'name': item['name'],
                            'quantity': qty,
                            'rate': item['rate']
                        })
        
        st.divider()
        
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
                if order_id:
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
                            if update_order_status(order['id'], 'Completed'):
                                st.success("Order completed!")
                                st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"delete_{order['id']}", use_container_width=True):
                            if delete_order(order['id']):
                                st.success("Order deleted!")
                                st.rerun()
                    
                    st.divider()
                    
                    items = get_order_items(order['id'])
                    if len(items) > 0:
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
                    if len(items) > 0:
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
                        if update_order_status(order['id'], 'Active'):
                            st.success("Order reactivated!")
                            st.rerun()
        else:
            st.info("No completed orders found!")

# Inventory Page
elif page == "📦 Inventory":
    st.title("📦 Inventory Management")
    
    items_df = get_all_items()
    
    if len(items_df) > 0:
        st.subheader("Update Stock Levels")
        
        for idx, item in items_df.iterrows():
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
                    key=f"stock_{idx}",
                    label_visibility="collapsed"
                )
            
            with col4:
                if st.button("💾", key=f"save_{idx}", help="Save"):
                    if new_stock != current_stock:
                        if update_stock(item['name'], new_stock):
                            st.success("✅")
                            st.rerun()
        
        st.divider()
        
        st.subheader("📊 Stock Summary")
        total_stock_value = (items_df['stock'] * items_df['rate']).sum()
        st.metric("Total Inventory Value", f"₹{total_stock_value:,.2f}")
    else:
        st.warning("No items found in inventory!")

# Stock Analysis Page
elif page == "📈 Stock Analysis":
    st.title("📈 Stock vs Orders Analysis")
    
    analysis_df = get_stock_vs_orders()
    
    if len(analysis_df) > 0:
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
        
        shortage_items = analysis_df[analysis_df['difference'] < 5]
        
        if len(shortage_items) > 0:
            st.subheader("🛒 Shopping List")
            st.info("Items to purchase/prepare:")
            
            for _, item in shortage_items.iterrows():
                needed = max(0, 10 - item['stock'])
                st.write(f"- **{item['name']}**: {needed:.1f} kg")
    else:
        st.warning("No stock data available!")

# Footer
st.sidebar.divider()
st.sidebar.success("🔒 **Data is Safe in Google Sheets!**")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
