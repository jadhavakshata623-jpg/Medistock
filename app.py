import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import init_database, get_all_medicines, add_medicine, update_stock, get_low_stock_medicines, get_expiring_medicines
from ai_services import get_medicine_info, get_drug_interactions, get_inventory_recommendations
from utils import calculate_days_until_expiry, get_stock_status, format_currency
from barcode_service import barcode_service

# Page configuration
st.set_page_config(
    page_title="AI Pharmacy Inventory Management",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for medical theme
st.markdown("""
<style>
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E7D32;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-critical {
        background-color: #FFEBEE;
        border-left: 4px solid #D32F2F;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-warning {
        background-color: #FFF8E1;
        border-left: 4px solid #F57C00;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-good {
        color: #2E7D32;
        font-weight: bold;
    }
    .status-warning {
        color: #F57C00;
        font-weight: bold;
    }
    .status-critical {
        color: #D32F2F;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize database
    init_database()
    
    # Main title
    st.title("🏥 AI Pharmacy Inventory Management System")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["Dashboard", "Inventory Management", "Add New Medicine", "Barcode Scanner", "AI Search & Analysis", "Reports"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Inventory Management":
        show_inventory_management()
    elif page == "Add New Medicine":
        show_add_medicine()
    elif page == "Barcode Scanner":
        show_barcode_scanner()
    elif page == "AI Search & Analysis":
        show_ai_search()
    elif page == "Reports":
        show_reports()

def show_dashboard():
    st.header("📊 Dashboard Overview")
    
    # Get all medicines for calculations
    medicines = get_all_medicines()
    
    if not medicines:
        st.warning("No medicines in inventory. Please add some medicines to get started.")
        return
    
    df = pd.DataFrame(medicines)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_medicines = len(df)
        st.metric("Total Medicines", total_medicines, delta=None)
    
    with col2:
        if len(df) > 0:
            total_value = df['current_stock'].sum() * df['unit_price'].mean()
            st.metric("Total Inventory Value", format_currency(total_value))
        else:
            st.metric("Total Inventory Value", format_currency(0))
    
    with col3:
        low_stock_count = len(get_low_stock_medicines())
        st.metric("Low Stock Items", low_stock_count, delta=None)
    
    with col4:
        expiring_count = len(get_expiring_medicines(30))
        st.metric("Expiring Soon (30 days)", expiring_count, delta=None)
    
    st.markdown("---")
    
    # Alerts section
    st.subheader("🚨 Critical Alerts")
    
    # Critical alerts
    critical_medicines = get_expiring_medicines(7)
    if critical_medicines:
        st.markdown('<div class="alert-critical">', unsafe_allow_html=True)
        st.error("**CRITICAL: Medicines expiring within 7 days**")
        for med in critical_medicines:
            days_left = calculate_days_until_expiry(med['expiry_date'])
            st.write(f"• **{med['name']}** - Expires in {days_left} days (Batch: {med['batch_number']})")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Warning alerts
    warning_medicines = get_low_stock_medicines()
    if warning_medicines:
        st.markdown('<div class="alert-warning">', unsafe_allow_html=True)
        st.warning("**WARNING: Low stock medicines**")
        for med in warning_medicines:
            st.write(f"• **{med['name']}** - Current: {med['current_stock']}, Reorder at: {med['reorder_point']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    if not critical_medicines and not warning_medicines:
        st.success("✅ No critical alerts at this time!")
    
    st.markdown("---")
    
    # Stock status chart
    st.subheader("📈 Stock Status Overview")
    
    # Calculate stock status for each medicine
    if len(df) > 0:
        stock_status_data = []
        for _, row in df.iterrows():
            status = get_stock_status(row['current_stock'], row['reorder_point'])
            stock_status_data.append(status)
        
        df['stock_status'] = stock_status_data
    if len(df) > 0 and 'stock_status' in df.columns:
        status_counts = df['stock_status'].value_counts()
    else:
        status_counts = pd.Series(dtype=int)
    
    if len(status_counts) > 0:
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Stock Status Distribution",
            color_discrete_map={
                'Good': '#2E7D32',
                'Low': '#F57C00',
                'Critical': '#D32F2F'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for stock status chart")

def show_inventory_management():
    st.header("📦 Inventory Management")
    
    medicines = get_all_medicines()
    
    if not medicines:
        st.warning("No medicines in inventory.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(medicines)
    df.columns = ['ID', 'Name', 'Current Stock', 'Reorder Point', 'Expiry Date', 
                  'Unit Price', 'Batch Number', 'Supplier', 'Category', 'Location']
    
    # Add calculated columns
    df['Days Until Expiry'] = df['Expiry Date'].apply(calculate_days_until_expiry)
    df['Stock Status'] = df.apply(lambda row: get_stock_status(row['Current Stock'], row['Reorder Point']), axis=1)
    df['Total Value'] = df['Current Stock'] * df['Unit Price']
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search medicines", placeholder="Enter medicine name...")
    with col2:
        status_filter = st.selectbox("Filter by status", ["All", "Good", "Low", "Critical"])
    
    # Apply filters
    filtered_df = df.copy()
    if search_term:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(search_term, case=False)]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['Stock Status'] == status_filter]
    
    # Display table with color coding
    st.subheader("Current Inventory")
    
    if len(filtered_df) == 0:
        st.info("No medicines match your search criteria.")
        return
    
    # Display the dataframe with custom highlighting
    st.dataframe(filtered_df, use_container_width=True)
    
    # Update stock section
    st.markdown("---")
    st.subheader("📝 Update Stock")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        medicine_names = [med['name'] for med in medicines]
        selected_medicine = st.selectbox("Select Medicine", medicine_names)
    
    with col2:
        new_stock = st.number_input("New Stock Quantity", min_value=0, value=0)
    
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Update Stock", type="primary"):
            if selected_medicine and new_stock >= 0:
                # Find medicine ID
                medicine_id = None
                for med in medicines:
                    if med['name'] == selected_medicine:
                        medicine_id = med['id']
                        break
                
                if medicine_id:
                    update_stock(medicine_id, new_stock)
                    st.success(f"Stock updated for {selected_medicine}")
                    st.rerun()

def show_add_medicine():
    st.header("➕ Add New Medicine")
    
    with st.form("add_medicine_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Medicine Name *", placeholder="Enter medicine name")
            current_stock = st.number_input("Current Stock *", min_value=0, value=0)
            reorder_point = st.number_input("Reorder Point *", min_value=0, value=10)
            expiry_date = st.date_input("Expiry Date *", value=datetime.now().date() + timedelta(days=365))
            unit_price = st.number_input("Unit Price ($) *", min_value=0.0, value=0.0, format="%.2f")
        
        with col2:
            batch_number = st.text_input("Batch Number", placeholder="Enter batch number")
            supplier = st.text_input("Supplier", placeholder="Enter supplier name")
            category = st.selectbox("Category", [
                "Prescription", "Over-the-counter", "Controlled substance", 
                "Antibiotic", "Pain relief", "Vitamins", "Other"
            ])
            location = st.text_input("Storage Location", placeholder="e.g., Shelf A-1")
        
        submitted = st.form_submit_button("Add Medicine", type="primary")
        
        if submitted:
            if name and current_stock >= 0 and reorder_point >= 0 and unit_price >= 0:
                try:
                    add_medicine(
                        name, current_stock, reorder_point, expiry_date,
                        unit_price, batch_number, supplier, category, location
                    )
                    st.success(f"Medicine '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding medicine: {str(e)}")
            else:
                st.error("Please fill in all required fields marked with *")

def show_barcode_scanner():
    st.header("📱 Barcode Scanner")
    
    # Instructions
    st.info("""
    **How to use the barcode scanner:**
    1. Enter the barcode number manually or scan using your device's camera
    2. Click 'Lookup Medicine' to get product information
    3. Review and edit the auto-filled information
    4. Add to inventory or update existing stock
    """)
    
    # Barcode input methods
    st.subheader("🔍 Barcode Input")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Manual barcode entry
        barcode_input = st.text_input(
            "Enter Barcode Number",
            placeholder="Scan or type barcode (UPC, EAN, NDC, etc.)",
            help="Common pharmacy barcodes: UPC (12 digits), EAN (13 digits), NDC (11 digits)"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        lookup_button = st.button("🔍 Lookup Medicine", type="primary", disabled=not barcode_input)
    
    # Camera-based scanning instruction
    st.markdown("---")
    st.subheader("📷 Camera Scanning (Instructions)")
    st.info("""
    **For camera-based scanning:**
    1. Use your phone's camera or barcode scanner app
    2. Scan the medicine barcode
    3. Copy the barcode number and paste it above
    4. Common barcode locations: back of packaging, prescription labels, or bottle caps
    """)
    
    # Barcode lookup results
    if lookup_button and barcode_input:
        with st.spinner("Looking up barcode information..."):
            try:
                # Get barcode information
                barcode_info = barcode_service.get_medicine_info_from_barcode(barcode_input.strip())
                
                if barcode_info:
                    st.success("✅ Barcode information found!")
                    
                    # Display barcode information
                    st.subheader("📋 Product Information")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Barcode:**", barcode_info.get('barcode', barcode_input))
                        st.write("**Product Name:**", barcode_info.get('name') or barcode_info.get('product_name', 'N/A'))
                        st.write("**Category:**", barcode_info.get('category', 'N/A'))
                        st.write("**Brand:**", barcode_info.get('brand', 'N/A'))
                    
                    with col2:
                        st.write("**Is Medicine:**", "Yes" if barcode_info.get('is_medicine', False) else "Unknown")
                        st.write("**Confidence:**", barcode_info.get('confidence', 'N/A'))
                        st.write("**Barcode Type:**", barcode_info.get('barcode_type', 'N/A'))
                    
                    # Show AI analysis if available
                    if barcode_info.get('ai_analysis'):
                        with st.expander("🤖 AI Analysis"):
                            st.write(barcode_info.get('ai_analysis'))
                    
                    # Auto-fill form section
                    st.markdown("---")
                    st.subheader("➕ Add to Inventory")
                    
                    # Get suggested form data
                    suggestions = barcode_service.suggest_medicine_data(barcode_info)
                    
                    # Pre-filled form
                    with st.form("barcode_medicine_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            name = st.text_input(
                                "Medicine Name *", 
                                value=suggestions.get('name', ''),
                                placeholder="Enter medicine name"
                            )
                            current_stock = st.number_input("Current Stock *", min_value=0, value=0)
                            reorder_point = st.number_input(
                                "Reorder Point *", 
                                min_value=0, 
                                value=suggestions.get('reorder_point', 10)
                            )
                            expiry_date = st.date_input("Expiry Date *", value=datetime.now().date() + timedelta(days=365))
                            unit_price = st.number_input(
                                "Unit Price ($) *", 
                                min_value=0.0, 
                                value=suggestions.get('unit_price', 0.0), 
                                format="%.2f"
                            )
                        
                        with col2:
                            batch_number = st.text_input(
                                "Batch Number", 
                                value=suggestions.get('batch_number', ''),
                                placeholder="Enter batch number"
                            )
                            supplier = st.text_input("Supplier", placeholder="Enter supplier name")
                            category = st.selectbox(
                                "Category", 
                                ["Prescription", "Over-the-counter", "Controlled substance", 
                                 "Antibiotic", "Pain relief", "Vitamins", "Other"],
                                index=0 if suggestions.get('category') == 'Prescription' else 1
                            )
                            location = st.text_input(
                                "Storage Location", 
                                value=suggestions.get('location', ''),
                                placeholder="e.g., Shelf A-1"
                            )
                        
                        submitted = st.form_submit_button("Add Medicine from Barcode", type="primary")
                        
                        if submitted:
                            if name and current_stock >= 0 and reorder_point >= 0 and unit_price >= 0:
                                try:
                                    add_medicine(
                                        name, current_stock, reorder_point, expiry_date,
                                        unit_price, batch_number, supplier, category, location
                                    )
                                    st.success(f"✅ Medicine '{name}' added successfully from barcode scan!")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error adding medicine: {str(e)}")
                            else:
                                st.error("Please fill in all required fields marked with *")
                    
                    # Quick stock update section
                    st.markdown("---")
                    st.subheader("📝 Quick Stock Update")
                    
                    # Check if medicine already exists
                    existing_medicines = get_all_medicines()
                    medicine_names = [med['name'] for med in existing_medicines]
                    suggested_name = suggestions.get('name', '')
                    
                    if suggested_name in medicine_names:
                        st.info(f"📦 Medicine '{suggested_name}' already exists in inventory.")
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            stock_update = st.number_input(
                                "Add/Remove Stock", 
                                value=0, 
                                help="Positive numbers add stock, negative numbers remove stock"
                            )
                        with col2:
                            st.write("")  # Spacing
                            st.write("")  # Spacing
                            if st.button("Update Stock", type="secondary"):
                                # Find medicine ID
                                medicine_id = None
                                current_stock_val = 0
                                for med in existing_medicines:
                                    if med['name'] == suggested_name:
                                        medicine_id = med['id']
                                        current_stock_val = med['current_stock']
                                        break
                                
                                if medicine_id:
                                    new_stock = max(0, current_stock_val + stock_update)
                                    update_stock(medicine_id, new_stock, f"Barcode scan update: {barcode_input}")
                                    st.success(f"Stock updated for {suggested_name}: {current_stock_val} → {new_stock}")
                                    st.rerun()
                
                else:
                    st.warning("⚠️ No product information found for this barcode.")
                    st.info("""
                    **Possible reasons:**
                    - Barcode not in public databases
                    - Invalid or damaged barcode
                    - Proprietary pharmacy barcode
                    
                    **Next steps:**
                    - Try manual entry in 'Add New Medicine'
                    - Contact supplier for product information
                    - Use internal pharmacy database if available
                    """)
                    
            except Exception as e:
                st.error(f"Error looking up barcode: {str(e)}")
                st.info("Please try manual entry or contact system administrator.")
    
    # Recent barcode scans (session state)
    if 'barcode_history' not in st.session_state:
        st.session_state.barcode_history = []
    
    # Add to history when lookup is performed
    if lookup_button and barcode_input and barcode_input.strip():
        from datetime import datetime
        scan_entry = {
            'barcode': barcode_input.strip(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Check if barcode already exists in history
        existing_barcodes = [entry['barcode'] for entry in st.session_state.barcode_history]
        if barcode_input.strip() not in existing_barcodes:
            st.session_state.barcode_history.insert(0, scan_entry)
            st.session_state.barcode_history = st.session_state.barcode_history[:10]  # Keep last 10
    
    # Show scan history
    if st.session_state.barcode_history:
        st.markdown("---")
        st.subheader("🕒 Recent Scans")
        
        for i, scan_entry in enumerate(st.session_state.barcode_history):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"📱 {scan_entry['barcode']}")
            with col2:
                st.write(f"🕐 {scan_entry['timestamp']}")
            with col3:
                if st.button("🔄", key=f"rescan_{i}", help="Scan again"):
                    # Set the barcode input to this value
                    st.experimental_set_query_params(barcode=scan_entry['barcode'])
                    st.rerun()

def show_ai_search():
    st.header("🤖 AI Search & Drug Analysis")
    
    # Medicine Information Search
    st.subheader("💊 Medicine Information Search")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        medicine_query = st.text_input(
            "Search for medicine information", 
            placeholder="Enter medicine name (e.g., 'Aspirin', 'Amoxicillin')"
        )
    with col2:
        st.write("")  # Spacing
        search_button = st.button("Search", type="primary")
    
    if search_button and medicine_query:
        with st.spinner("Searching for medicine information..."):
            try:
                medicine_info = get_medicine_info(medicine_query)
                st.success("Information retrieved successfully!")
                st.markdown("### Medicine Information")
                st.write(medicine_info)
            except Exception as e:
                st.error(f"Error retrieving medicine information: {str(e)}")
    
    st.markdown("---")
    
    # Drug Interactions
    st.subheader("⚠️ Drug Interaction Checker")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        drugs_input = st.text_area(
            "Enter medications to check for interactions",
            placeholder="Enter medication names separated by commas (e.g., 'Aspirin, Warfarin, Ibuprofen')",
            height=100
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        check_interactions = st.button("Check Interactions", type="primary")
    
    if check_interactions and drugs_input:
        with st.spinner("Checking for drug interactions..."):
            try:
                interactions = get_drug_interactions(drugs_input)
                st.success("Interaction check completed!")
                st.markdown("### Drug Interaction Analysis")
                st.write(interactions)
            except Exception as e:
                st.error(f"Error checking drug interactions: {str(e)}")
    
    st.markdown("---")
    
    # Inventory Optimization
    st.subheader("📈 AI Inventory Optimization")
    
    medicines = get_all_medicines()
    if medicines:
        if st.button("Get AI Recommendations", type="primary"):
            with st.spinner("Analyzing inventory and generating recommendations..."):
                try:
                    # Prepare inventory data for AI analysis
                    df = pd.DataFrame(medicines)
                    df.columns = ['ID', 'Name', 'Current Stock', 'Reorder Point', 'Expiry Date', 
                                  'Unit Price', 'Batch Number', 'Supplier', 'Category', 'Location']
                    
                    inventory_summary = df.to_dict('records')
                    recommendations = get_inventory_recommendations(inventory_summary)
                    
                    st.success("AI recommendations generated!")
                    st.markdown("### AI-Powered Inventory Recommendations")
                    st.write(recommendations)
                except Exception as e:
                    st.error(f"Error generating recommendations: {str(e)}")
    else:
        st.info("Add some medicines to inventory to get AI recommendations.")

def show_reports():
    st.header("📊 Reports & Analytics")
    
    medicines = get_all_medicines()
    
    if not medicines:
        st.warning("No data available for reports.")
        return
    
    df = pd.DataFrame(medicines)
    df.columns = ['ID', 'Name', 'Current Stock', 'Reorder Point', 'Expiry Date', 
                  'Unit Price', 'Batch Number', 'Supplier', 'Category', 'Location']
    
    # Add calculated columns
    df['Days Until Expiry'] = df['Expiry Date'].apply(calculate_days_until_expiry)
    df['Stock Status'] = df.apply(lambda row: get_stock_status(row['Current Stock'], row['Reorder Point']), axis=1)
    df['Total Value'] = df['Current Stock'] * df['Unit Price']
    
    # Key metrics summary
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_value = df['Total Value'].sum()
        st.metric("Total Inventory Value", format_currency(total_value))
    
    with col2:
        avg_days_to_expiry = df['Days Until Expiry'].mean()
        st.metric("Avg Days to Expiry", f"{avg_days_to_expiry:.0f} days")
    
    with col3:
        total_stock = df['Current Stock'].sum()
        st.metric("Total Stock Units", f"{total_stock:,}")
    
    with col4:
        unique_suppliers = len(df['Supplier'].unique())
        st.metric("Active Suppliers", unique_suppliers)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Stock value by category
        category_value = df.groupby('Category')['Total Value'].sum().reset_index()
        fig1 = px.bar(
            category_value, 
            x='Category', 
            y='Total Value',
            title="Inventory Value by Category",
            color_discrete_sequence=['#2E7D32']
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Expiry timeline
        expiry_bins = []
        for days in df['Days Until Expiry']:
            if days < 30:
                expiry_bins.append('< 30 days')
            elif days < 90:
                expiry_bins.append('30-90 days')
            elif days < 180:
                expiry_bins.append('90-180 days')
            else:
                expiry_bins.append('> 180 days')
        
        df['Expiry Bin'] = expiry_bins
        expiry_counts = df['Expiry Bin'].value_counts()
        
        fig2 = px.pie(
            values=expiry_counts.values,
            names=expiry_counts.index,
            title="Medicines by Expiry Timeline",
            color_discrete_sequence=['#D32F2F', '#F57C00', '#1976D2', '#2E7D32']
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed tables
    st.subheader("📋 Detailed Reports")
    
    tab1, tab2, tab3 = st.tabs(["Low Stock Report", "Expiring Soon", "High Value Items"])
    
    with tab1:
        low_stock = df[df['Stock Status'].isin(['Low', 'Critical'])]
        if len(low_stock) > 0:
            st.dataframe(low_stock[['Name', 'Current Stock', 'Reorder Point', 'Stock Status']], use_container_width=True)
        else:
            st.success("No low stock items!")
    
    with tab2:
        expiring_soon = df[df['Days Until Expiry'] <= 30]
        if len(expiring_soon) > 0:
            st.dataframe(expiring_soon[['Name', 'Days Until Expiry', 'Batch Number', 'Current Stock']], use_container_width=True)
        else:
            st.success("No medicines expiring soon!")
    
    with tab3:
        high_value = df.nlargest(10, 'Total Value')
        st.dataframe(high_value[['Name', 'Current Stock', 'Unit Price', 'Total Value']], use_container_width=True)

if __name__ == "__main__":
    main()
