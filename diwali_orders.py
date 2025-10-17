import streamlit as st
import pandas as pd
from datetime import datetime, date
from io import StringIO

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
    .stButton>button {
        width: 100%;
        height: 50px;
        font-size: 18px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# EMBEDDED DATA - Your CSV data directly in code!

ITEMS_DATA = """Item_Name,Rate,Stock,Value
Besan Laddu,580,16,9280
Chakli,400,8,3200
Shev (Masala),380,8.5,3230
Shev(Thin),380,8.5,3230
Shankarpade(Salty),380,6.5,2470
Shankarpade(Sweet),380,5,1900
Chivda,290,10,2900
Anarse,720,0,0
Karanji (Pitthi),540,1,540
Karanji (Ola Naral),540,0.5,270
Rava Laddu,400,1,400"""

ORDERS_DATA = """Order_ID,Customer_Name,Phone,Address,Delivery_Date,Status,Payment,Order_Date,Notes
1,Pradnya Ingle,,Amravati,10/8/2025,Completed,Paid,10/6/2025,
2,Dhakulkar Sir,,Amravati,10/8/2025,Completed,Paid,10/6/2025,
3,Jagdale Madam,,Amravati,10/9/2025,Completed,Paid,10/7/2025,
4,Bhagat Sir,,Amravati,10/11/2025,Completed,Paid,10/8/2025,
5,Raja Bhau,,Amravati,10/16/2025,Completed,Paid,10/10/2025,
6,Rani Bhonde,,Amravati,10/16/2025,Completed,Paid,10/10/2025,
7,Katle Sister,,Amravati,10/20/2025,Active,Pending,10/17/2025,
8,Bhatkar,,Amravati,10/20/2025,Active,Pending,10/17/2025,
9,Harne,,Amravati,10/20/2025,Active,Pending,10/17/2025,
10,Vanita Bai,,Amravati,10/17/2025,Completed,Paid,10/12/2025,
11,Jadhav Madam,,Amravati,10/17/2025,Completed,Paid,10/15/2025,
12,Bapat,,Amravati,10/17/2025,Completed,Paid,10/16/2025,
13,Wavage Saheb,,Amravati,10/20/2025,Active,Pending,10/11/2025,
14,Thakur Saheb,,Amravati,10/20/2025,Active,Pending,10/11/2025,
15,Meenal Thakare Madam,,Amravati,10/20/2025,Active,Pending,10/11/2025,
16,Wadve Sir,,Amravati,10/17/2025,Completed,Pending,10/11/2025,
17,Pradnya Madam Ingle,,Amravati,10/17/2025,Completed,Pending,10/11/2025,
18,Ambore Madam,,Amravati,10/18/2025,Active,Pending,10/11/2025,
19,Kate Sir,,Amravati,10/18/2025,Completed,Pending,10/11/2025,
20,Girase Madam,,Amravati,10/19/2025,Active,Pending,10/11/2025,
21,Sonal Pachange,,Amravati,10/17/2025,Completed,Pending,10/11/2025,
22,Thoke Sir,,Amravati,10/19/2025,Active,Pending,10/11/2025,
23,Sunil Bhau Bhonde,,Amravati,10/19/2025,Active,Pending,10/11/2025,
24,Yogesh Bhau,,Amravati,10/19/2025,Active,Pending,10/11/2025,
25,Pradnya Madam Ingle(Friend),,Amravati,10/17/2025,Completed,Pending,10/11/2025,
26,Yeole Madam,,Amravati,10/18/2025,Completed,Pending,10/11/2025,
27,Anagha Ronghe,,Amravati,10/19/2025,Active,Pending,10/11/2025,
28,Sonam Savde,,Amravati,10/19/2025,Active,Pending,10/11/2025,
29,Sunanda Kaldate,,Amravati,10/19/2025,Active,Pending,10/11/2025,
30,Snehal Ingle,,Amravati,10/19/2025,Active,Pending,10/11/2025,
31,Minakshi Bole,,Amravati,10/19/2025,Active,Pending,10/11/2025"""

ORDER_ITEMS_DATA = """Order_ID,Item_Name,quantity,rate,Amount
1,Shev (Masala),0.25,380,95
1,Shev(Thin),0.125,380,47.5
1,Shankarpade(Salty),0.25,380,95
2,Shankarpade(Salty),0.5,380,190
2,Chakli,0.5,400,200
3,Chivda,0.25,290,72.5
3,Shev (Masala),0.25,380,95
3,Chakli,0.25,400,100
3,Besan Laddu,0.5,580,290
4,Shev (Masala),0.5,380,190
4,Shev(Thin),0.5,380,190
4,Shankarpade(Sweet),0.5,380,190
4,Chakli,0.5,400,200
5,Chivda,2,290,580
5,Shev(Thin),1,380,380
5,Shev (Masala),1,380,380
5,Chakli,1,400,400
5,Besan Laddu,1,580,580
5,Shankarpade(Salty),1,380,380
5,Shankarpade(Sweet),0.5,380,190
6,Rani Bhonde,2,580,1160
6,Rani Bhonde,0.5,380,190
7,Besan Laddu,0.5,580,290
7,Shankarpade(Salty),0.5,380,190
8,Besan Laddu,0.5,580,290
9,Chakli,0.5,400,200
9,Shankarpade(Salty),0.5,380,190
9,Chivda,0.5,290,145
9,Karanji (Ola Naral),0.5,540,270
10,Shev (Masala),0.5,380,190
11,Besan Laddu,0.5,580,290
11,Karanji (Ola Naral),0.5,540,270
12,Shev (Masala),0.25,380,95
12,Shev(Thin),0.25,380,95
12,Chakli,0.25,400,100
12,Shankarpade(Salty),0.25,380,95
12,Shankarpade(Sweet),0.25,380,95
13,Besan Laddu,1,580,580
14,Besan Laddu,0.5,580,290
15,Shev (Masala),2,380,760
15,Shev(Thin),0.5,380,190
15,Besan Laddu,2,580,1160
15,Shankarpade(Salty),1,380,380
15,Karanji (Ola Naral),1.5,540,810
16,Shev (Masala),0.5,380,190
16,Shev(Thin),0.5,380,190
16,Karanji (Pitthi),0.5,540,270
16,Shankarpade(Salty),0.5,380,190
16,Besan Laddu,0.5,580,290
17,Besan Laddu,1,580,580
17,Shev (Masala),0.5,380,190
17,Shev(Thin),1,380,380
17,Shankarpade(Sweet),0.5,380,190
17,Shankarpade(Salty),0.5,380,190
17,Chakli,0.5,400,200
18,Chakli,1.5,400,600
18,Besan Laddu,0.5,580,290
18,Rava Laddu,0.5,400,200
18,Shev (Masala),0.5,380,190
18,Shankarpade(Salty),0.5,380,190
18,Karanji (Pitthi),0.5,540,270
18,Anarse,0.25,760,190
19,Besan Laddu,0.5,580,290
19,Shankarpade(Salty),0.5,380,190
19,Shev(Thin),0.25,380,95
20,Shev (Masala),1,380,380
20,Karanji (Ola Naral),0.5,540,270
20,Chivda,1,290,290
20,Karanji (Pitthi),0.5,540,270
21,Chivda,1,290,290
21,Shankarpade(Sweet),1,380,380
21,Chakli,0.5,400,200
21,Karanji,0.5,540,270
22,Chakli,0.5,400,200
22,Chivda,0.5,145,72.5
22,Shankarpade(Sweet),0.5,380,190
22,Karanji (Ola Naral),0.5,540,270
22,Shev (Masala),0.5,380,190
22,Anarse,0.5,760,380
23,Besan Laddu,1,580,580
24,Chakli,0.5,400,200
24,Besan Laddu,0.5,580,290
25,Besan Laddu,0.5,580,290
25,Shev(Thin),0.5,380,190
26,Chakli,2,400,800
26,Chivda,2,290,580
26,Shev (Masala),2,380,760
26,Shankarpade(Sweet),2,380,760
27,Besan Laddu,0.5,580,290
27,Chakli,0.5,400,200
27,Chivda,0.5,290,145
27,Karanji,0.25,540,135
27,Shev(Thin),0.5,380,190
27,Shankarpade(Sweet),0.5,380,190
28,Besan Laddu,1,580,580
28,Chakli,1,400,400
28,Chivda,1,290,290
28,Karanji (Ola Naral),1,540,540
28,Shankarpade(Sweet),1,380,380
28,Shev (Masala),1,380,380
29,Chivda,0.5,290,145
29,Shev (Masala),0.5,380,190
29,Shev(Thin),0.5,380,190
29,Chakli,1,400,400
29,Shankarpade(Salty),0.5,380,190
29,Karanji (Pitthi),1,540,540
30,Chivda,0.5,290,145
30,Chakli,0.5,400,200
30,Shev (Masala),0.5,380,190
30,Karanji (Pitthi),0.5,540,270
30,Shankarpade(Salty),0.5,380,190
31,Shev (Masala),0.5,380,190
31,Shev(Thin),0.5,380,190
31,Shankarpade(Salty),0.5,380,190
31,Shankarpade(Sweet),0.5,380,190
31,Chakli,0.5,400,200
31,Chivda,0.5,290,145"""

# Load data into DataFrames
@st.cache_data
def load_data():
    items_df = pd.read_csv(StringIO(ITEMS_DATA))
    orders_df = pd.read_csv(StringIO(ORDERS_DATA))
    order_items_df = pd.read_csv(StringIO(ORDER_ITEMS_DATA))
    
    # Convert dates
    orders_df['Delivery_Date'] = pd.to_datetime(orders_df['Delivery_Date'], format='%m/%d/%Y')
    orders_df['Order_Date'] = pd.to_datetime(orders_df['Order_Date'], format='%m/%d/%Y')
    
    return items_df, orders_df, order_items_df

items_df, orders_df, order_items_df = load_data()

# Helper functions
def get_order_total(order_id):
    order_items = order_items_df[order_items_df['Order_ID'] == order_id]
    return order_items['Amount'].sum()

def get_item_customers(item_name):
    # Get all order IDs for this item
    item_orders = order_items_df[order_items_df['Item_Name'] == item_name]['Order_ID'].unique()
    # Get customer details for these orders
    customers = orders_df[orders_df['Order_ID'].isin(item_orders)][['Customer_Name', 'Delivery_Date', 'Status', 'Payment']]
    return customers

# Sidebar
st.sidebar.title("🪔 Diwali Orders")
st.sidebar.success("✅ Data Embedded - No Database!")
st.sidebar.info(f"📊 {len(orders_df)} Orders\n📦 {len(items_df)} Items")

page = st.sidebar.radio("Navigation", 
                        ["📊 Dashboard", "📋 All Orders", "📦 Inventory", 
                         "📈 Stock Analysis", "🔍 Item-wise Customers"])

# Dashboard
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    # Calculate metrics
    active_orders = orders_df[orders_df['Status'] == 'Active']
    completed_orders = orders_df[orders_df['Status'] == 'Completed']
    
    # Calculate amounts
    total_amount = 0
    active_amount = 0
    completed_amount = 0
    pending_amount = 0
    
    for _, order in orders_df.iterrows():
        order_total = get_order_total(order['Order_ID'])
        total_amount += order_total
        
        if order['Status'] == 'Active':
            active_amount += order_total
            if order['Payment'] == 'Pending':
                pending_amount += order_total
        elif order['Status'] == 'Completed':
            completed_amount += order_total
    
    # Today's deliveries
    today = pd.Timestamp(date.today())
    todays_deliveries = active_orders[active_orders['Delivery_Date'].dt.date == today.date()]
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔄 Active Orders", len(active_orders))
        st.metric("💰 Active Amount", f"₹{active_amount:,.0f}")
    
    with col2:
        st.metric("✅ Completed Orders", len(completed_orders))
        st.metric("💰 Completed Amount", f"₹{completed_amount:,.0f}")
    
    with col3:
        st.metric("📅 Today's Deliveries", len(todays_deliveries))
        st.metric("⚠️ Pending Payment", f"₹{pending_amount:,.0f}")
    
    with col4:
        st.metric("📊 Total Orders", len(orders_df))
        st.metric("💵 Total Amount", f"₹{total_amount:,.0f}")
    
    st.divider()
    
    # Today's deliveries detail
    if len(todays_deliveries) > 0:
        st.subheader("📅 Today's Deliveries")
        for _, order in todays_deliveries.iterrows():
            order_total = get_order_total(order['Order_ID'])
            with st.expander(f"👤 {order['Customer_Name']} - ₹{order_total:,.0f}"):
                items = order_items_df[order_items_df['Order_ID'] == order['Order_ID']]
                st.dataframe(items[['Item_Name', 'quantity', 'rate', 'Amount']], hide_index=True)
    
    st.divider()
    
    # Top 5 Items by Quantity
    st.subheader("🏆 Top 5 Items by Quantity Sold")
    item_summary = order_items_df.groupby('Item_Name').agg({
        'quantity': 'sum',
        'Amount': 'sum'
    }).sort_values('quantity', ascending=False).head(5)
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(item_summary.style.format({'quantity': '{:.2f} kg', 'Amount': '₹{:,.0f}'}))
    
    with col2:
        st.bar_chart(item_summary['quantity'])
    
    st.divider()
    
    # Stock Alerts
    st.subheader("⚠️ Stock Alerts")
    
    # Calculate required for active orders
    active_order_ids = active_orders['Order_ID'].tolist()
    required_items = order_items_df[order_items_df['Order_ID'].isin(active_order_ids)].groupby('Item_Name')['quantity'].sum()
    
    for _, item in items_df.iterrows():
        required = required_items.get(item['Item_Name'], 0)
        difference = item['Stock'] - required
        
        if difference < 0:
            st.error(f"🔴 {item['Item_Name']}: Stock {item['Stock']} kg | Required {required:.1f} kg | **SHORT by {abs(difference):.1f} kg**")
        elif difference < 2:
            st.warning(f"🟡 {item['Item_Name']}: Stock {item['Stock']} kg | Required {required:.1f} kg | Only {difference:.1f} kg surplus")

# All Orders
elif page == "📋 All Orders":
    st.title("📋 All Orders")
    
    tab1, tab2 = st.tabs(["🔄 Active Orders", "✅ Completed Orders"])
    
    with tab1:
        active_orders = orders_df[orders_df['Status'] == 'Active'].sort_values('Delivery_Date')
        
        if len(active_orders) > 0:
            for _, order in active_orders.iterrows():
                order_total = get_order_total(order['Order_ID'])
                delivery = order['Delivery_Date'].date()
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
                
                with st.expander(f"{date_color} {order['Customer_Name']} - {date_text} - ₹{order_total:,.0f}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**📱 Phone:** {order['Phone'] if order['Phone'] else 'N/A'}")
                        st.write(f"**📍 Address:** {order['Address']}")
                        st.write(f"**📅 Delivery:** {delivery.strftime('%d %b %Y')}")
                        st.write(f"**💳 Payment:** {order['Payment']}")
                        if order['Notes']:
                            st.write(f"**📝 Notes:** {order['Notes']}")
                    
                    with col2:
                        # Edit button
                        if st.button("✏️ Edit", key=f"edit_{order['Order_ID']}", use_container_width=True):
                            st.info("To edit orders, modify the data in the code and redeploy!")
                        
                        st.metric("Order Total", f"₹{order_total:,.2f}")
                    
                    st.divider()
                    
                    # Order items
                    items = order_items_df[order_items_df['Order_ID'] == order['Order_ID']]
                    st.dataframe(
                        items[['Item_Name', 'quantity', 'rate', 'Amount']].rename(columns={
                            'Item_Name': 'Item',
                            'quantity': 'Qty (kg)',
                            'rate': 'Rate (₹/kg)'
                        }),
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.markdown(f"### **Total: ₹{order_total:,.2f}**")
        else:
            st.info("No active orders found!")
    
    with tab2:
        completed_orders = orders_df[orders_df['Status'] == 'Completed'].sort_values('Delivery_Date', ascending=False)
        
        if len(completed_orders) > 0:
            for _, order in completed_orders.iterrows():
                order_total = get_order_total(order['Order_ID'])
                delivery = order['Delivery_Date'].date()
                
                with st.expander(f"✅ {order['Customer_Name']} - {delivery.strftime('%d %b %Y')} - ₹{order_total:,.0f}"):
                    st.write(f"**📱 Phone:** {order['Phone'] if order['Phone'] else 'N/A'}")
                    st.write(f"**💳 Payment:** {order['Payment']}")
                    
                    items = order_items_df[order_items_df['Order_ID'] == order['Order_ID']]
                    st.dataframe(
                        items[['Item_Name', 'quantity', 'rate', 'Amount']].rename(columns={
                            'Item_Name': 'Item',
                            'quantity': 'Qty (kg)',
                            'rate': 'Rate (₹/kg)'
                        }),
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    st.markdown(f"### **Total: ₹{order_total:,.2f}**")
        else:
            st.info("No completed orders found!")

# Inventory
elif page == "📦 Inventory":
    st.title("📦 Inventory")
    
    st.dataframe(
        items_df.style.format({'Rate': '₹{:.0f}', 'Stock': '{:.2f} kg', 'Value': '₹{:,.0f}'}),
        hide_index=True,
        use_container_width=True
    )
    
    st.divider()
    
    total_value = items_df['Value'].sum()
    total_stock = items_df['Stock'].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📦 Total Stock", f"{total_stock:.1f} kg")
    with col2:
        st.metric("💰 Total Inventory Value", f"₹{total_value:,.0f}")

# Stock Analysis
elif page == "📈 Stock Analysis":
    st.title("📈 Stock vs Orders Analysis")
    
    # Calculate required for active orders
    active_order_ids = orders_df[orders_df['Status'] == 'Active']['Order_ID'].tolist()
    required_items = order_items_df[order_items_df['Order_ID'].isin(active_order_ids)].groupby('Item_Name')['quantity'].sum()
    
    analysis_data = []
    for _, item in items_df.iterrows():
        required = required_items.get(item['Item_Name'], 0)
        difference = item['Stock'] - required
        status = "✅ OK" if difference >= 0 else f"⚠️ SHORT"
        
        analysis_data.append({
            'Item': item['Item_Name'],
            'Current Stock': f"{item['Stock']:.1f} kg",
            'Required': f"{required:.1f} kg",
            'Difference': f"{difference:.1f} kg",
            'Status': status
        })
    
    analysis_df = pd.DataFrame(analysis_data)
    st.dataframe(analysis_df, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Shopping list
    shortage_items = [item for item in analysis_data if "SHORT" in item['Status']]
    
    if shortage_items:
        st.subheader("🛒 Shopping List - Items to Prepare/Purchase")
        for item in shortage_items:
            st.write(f"- **{item['Item']}**: Need {item['Difference']}")
    else:
        st.success("✅ All items have sufficient stock for active orders!")

# Item-wise Customers
elif page == "🔍 Item-wise Customers":
    st.title("🔍 Item-wise Customer Analysis")
    
    st.info("Select an item to see all customers who ordered it")
    
    # Get unique items with order counts
    item_orders = order_items_df.groupby('Item_Name').agg({
        'Order_ID': 'count',
        'quantity': 'sum',
        'Amount': 'sum'
    }).rename(columns={'Order_ID': 'Total_Orders'}).sort_values('Total_Orders', ascending=False)
    
    selected_item = st.selectbox("Select Item:", items_df['Item_Name'].tolist())
    
    if selected_item:
        st.subheader(f"📊 {selected_item} - Customer Details")
        
        # Get statistics
        item_stats = item_orders.loc[selected_item] if selected_item in item_orders.index else None
        
        if item_stats is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Orders", int(item_stats['Total_Orders']))
            with col2:
                st.metric("Total Quantity", f"{item_stats['quantity']:.2f} kg")
            with col3:
                st.metric("Total Revenue", f"₹{item_stats['Amount']:,.0f}")
            
            st.divider()
            
            # Get customers
            customers = get_item_customers(selected_item)
            
            if len(customers) > 0:
                st.subheader("👥 Customers Who Ordered This Item")
                
                # Add order details
                customer_details = []
                for _, customer in customers.iterrows():
                    customer_order_id = orders_df[orders_df['Customer_Name'] == customer['Customer_Name']]['Order_ID'].values[0]
                    item_qty = order_items_df[
                        (order_items_df['Order_ID'] == customer_order_id) & 
                        (order_items_df['Item_Name'] == selected_item)
                    ]['quantity'].sum()
                    
                    customer_details.append({
                        'Customer': customer['Customer_Name'],
                        'Quantity': f"{item_qty:.2f} kg",
                        'Delivery Date': customer['Delivery_Date'].strftime('%d %b %Y'),
                        'Status': customer['Status'],
                        'Payment': customer['Payment']
                    })
                
                customer_df = pd.DataFrame(customer_details)
                st.dataframe(customer_df, hide_index=True, use_container_width=True)
                
                # Active vs Completed breakdown
                active_customers = customers[customers['Status'] == 'Active']
                completed_customers = customers[customers['Status'] == 'Completed']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🔄 Active Orders", len(active_customers))
                with col2:
                    st.metric("✅ Completed Orders", len(completed_customers))
            else:
                st.info("No customers found for this item")
        else:
            st.warning("This item hasn't been ordered yet")

# Footer
st.sidebar.divider()
st.sidebar.success("🎉 **Data Embedded in Code!**")
st.sidebar.info("To add new orders:\n1. Edit the data strings in code\n2. Redeploy app\n3. Data updates automatically!")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

