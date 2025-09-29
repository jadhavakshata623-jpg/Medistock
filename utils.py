from datetime import datetime, timedelta
import re

def calculate_days_until_expiry(expiry_date_str):
    """Calculate the number of days until a medicine expires."""
    try:
        if isinstance(expiry_date_str, str):
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        else:
            expiry_date = expiry_date_str
        
        today = datetime.now().date()
        delta = expiry_date - today
        return delta.days
    except (ValueError, TypeError):
        return 0

def get_stock_status(current_stock, reorder_point):
    """Determine stock status based on current stock and reorder point."""
    if current_stock <= 0:
        return "Critical"
    elif current_stock <= reorder_point:
        return "Low"
    elif current_stock <= reorder_point * 1.5:
        return "Warning"
    else:
        return "Good"

def format_currency(amount):
    """Format a number as currency."""
    return f"${amount:,.2f}"

def validate_medicine_name(name):
    """Validate medicine name format."""
    if not name or len(name.strip()) < 2:
        return False, "Medicine name must be at least 2 characters long"
    
    # Check for special characters that might cause issues
    if re.search(r'[<>"\']', name):
        return False, "Medicine name contains invalid characters"
    
    return True, "Valid"

def validate_batch_number(batch_number):
    """Validate batch number format."""
    if not batch_number:
        return True, "Valid"  # Batch number is optional
    
    # Basic validation - alphanumeric with some special characters
    if not re.match(r'^[A-Za-z0-9\-_/]+$', batch_number):
        return False, "Batch number can only contain letters, numbers, hyphens, underscores, and slashes"
    
    if len(batch_number) > 50:
        return False, "Batch number is too long (max 50 characters)"
    
    return True, "Valid"

def validate_price(price):
    """Validate price value."""
    try:
        price_float = float(price)
        if price_float < 0:
            return False, "Price cannot be negative"
        if price_float > 10000:  # Reasonable upper limit
            return False, "Price seems unreasonably high"
        return True, "Valid"
    except (ValueError, TypeError):
        return False, "Price must be a valid number"

def validate_stock_quantity(quantity):
    """Validate stock quantity."""
    try:
        qty_int = int(quantity)
        if qty_int < 0:
            return False, "Stock quantity cannot be negative"
        if qty_int > 1000000:  # Reasonable upper limit
            return False, "Stock quantity seems unreasonably high"
        return True, "Valid"
    except (ValueError, TypeError):
        return False, "Stock quantity must be a valid whole number"

def format_expiry_alert(days_until_expiry):
    """Format expiry alert message based on days remaining."""
    if days_until_expiry < 0:
        return f"⚠️ EXPIRED {abs(days_until_expiry)} days ago"
    elif days_until_expiry == 0:
        return "⚠️ EXPIRES TODAY"
    elif days_until_expiry <= 7:
        return f"🚨 CRITICAL: Expires in {days_until_expiry} days"
    elif days_until_expiry <= 30:
        return f"⚠️ WARNING: Expires in {days_until_expiry} days"
    elif days_until_expiry <= 90:
        return f"ℹ️ INFO: Expires in {days_until_expiry} days"
    else:
        return f"✅ Good: {days_until_expiry} days until expiry"

def get_alert_priority(current_stock, reorder_point, days_until_expiry):
    """Get alert priority level for a medicine."""
    priority = 0
    
    # Stock-based priority
    if current_stock <= 0:
        priority += 10  # Critical
    elif current_stock <= reorder_point * 0.5:
        priority += 8   # High
    elif current_stock <= reorder_point:
        priority += 5   # Medium
    
    # Expiry-based priority
    if days_until_expiry < 0:
        priority += 10  # Critical - expired
    elif days_until_expiry <= 7:
        priority += 8   # High - expires very soon
    elif days_until_expiry <= 30:
        priority += 5   # Medium - expires soon
    
    return min(priority, 20)  # Cap at maximum priority

def categorize_medicines_by_criticality(medicines):
    """Categorize medicines by their criticality level."""
    critical = []
    high = []
    medium = []
    low = []
    
    for medicine in medicines:
        current_stock = medicine[2]  # Assuming index 2 is current_stock
        reorder_point = medicine[3]  # Assuming index 3 is reorder_point
        expiry_date = medicine[4]    # Assuming index 4 is expiry_date
        
        days_until_expiry = calculate_days_until_expiry(expiry_date)
        priority = get_alert_priority(current_stock, reorder_point, days_until_expiry)
        
        if priority >= 15:
            critical.append(medicine)
        elif priority >= 10:
            high.append(medicine)
        elif priority >= 5:
            medium.append(medicine)
        else:
            low.append(medicine)
    
    return {
        'critical': critical,
        'high': high,
        'medium': medium,
        'low': low
    }

def generate_reorder_suggestion(current_stock, reorder_point, avg_daily_usage=None, lead_time_days=7):
    """Generate intelligent reorder quantity suggestion."""
    if avg_daily_usage is None:
        # If no usage data, use a simple formula
        suggested_order = max(reorder_point * 2, 30)  # At least 30 units or 2x reorder point
    else:
        # Calculate based on usage and lead time
        safety_stock = avg_daily_usage * 3  # 3 days safety stock
        order_quantity = (avg_daily_usage * lead_time_days) + safety_stock - current_stock
        suggested_order = max(order_quantity, reorder_point)
    
    return int(suggested_order)

def format_medicine_summary(medicine_data):
    """Format medicine data for display or export."""
    return {
        'id': medicine_data[0],
        'name': medicine_data[1],
        'current_stock': medicine_data[2],
        'reorder_point': medicine_data[3],
        'expiry_date': medicine_data[4],
        'unit_price': medicine_data[5],
        'batch_number': medicine_data[6],
        'supplier': medicine_data[7],
        'category': medicine_data[8],
        'location': medicine_data[9],
        'days_until_expiry': calculate_days_until_expiry(medicine_data[4]),
        'stock_status': get_stock_status(medicine_data[2], medicine_data[3]),
        'total_value': medicine_data[2] * medicine_data[5]
    }

def search_and_highlight(text, search_term):
    """Search for term in text and return highlighted result."""
    if not search_term or not text:
        return text
    
    # Simple highlighting - in a real app, you might use more sophisticated methods
    highlighted = re.sub(
        f'({re.escape(search_term)})', 
        r'**\1**', 
        text, 
        flags=re.IGNORECASE
    )
    return highlighted
