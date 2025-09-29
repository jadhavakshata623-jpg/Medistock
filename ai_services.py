import json
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# This is using OpenAI's API, which points to OpenAI's API servers and requires your own API key.
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_medicine_info(medicine_name):
    """Get detailed information about a medicine using AI."""
    try:
        prompt = f"""
        Provide comprehensive information about the medicine '{medicine_name}'. 
        Include the following details:
        
        1. Generic and brand names
        2. Primary uses and indications
        3. Common dosage forms and strengths
        4. Mechanism of action
        5. Common side effects
        6. Important contraindications
        7. Storage requirements
        8. Special handling considerations for pharmacy staff
        
        Please provide accurate, up-to-date medical information suitable for pharmacy professionals.
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are a pharmaceutical expert providing accurate information to pharmacy professionals. Always emphasize the importance of consulting official drug references and prescribing information."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Failed to retrieve medicine information: {str(e)}")

def get_drug_interactions(medications_list):
    """Check for potential drug interactions between multiple medications."""
    try:
        prompt = f"""
        Analyze the following medications for potential drug interactions:
        {medications_list}
        
        Please provide:
        1. Major drug interactions (if any)
        2. Moderate interactions to monitor
        3. Minor interactions or considerations
        4. Recommendations for pharmacy staff
        5. Any special monitoring requirements
        
        Format the response in a clear, structured manner suitable for pharmacy professionals.
        If no significant interactions are found, clearly state this.
        Always recommend consulting official drug interaction databases for complete information.
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical pharmacist expert in drug interactions. Provide thorough analysis while emphasizing the need to consult official databases and healthcare providers for clinical decisions."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Failed to check drug interactions: {str(e)}")

def get_inventory_recommendations(inventory_data):
    """Generate AI-powered inventory optimization recommendations."""
    try:
        # Prepare inventory summary for AI analysis
        inventory_summary = []
        for item in inventory_data[:20]:  # Limit to first 20 items for API efficiency
            summary_item = {
                "name": item.get("Name", ""),
                "current_stock": item.get("Current Stock", 0),
                "reorder_point": item.get("Reorder Point", 0),
                "category": item.get("Category", ""),
                "unit_price": item.get("Unit Price", 0),
                "supplier": item.get("Supplier", "")
            }
            inventory_summary.append(summary_item)
        
        prompt = f"""
        Analyze the following pharmacy inventory data and provide optimization recommendations:
        
        {json.dumps(inventory_summary, indent=2)}
        
        Please provide recommendations in the following areas:
        1. Stock level optimization (items that may be overstocked or understocked)
        2. Reorder point adjustments based on current stock patterns
        3. Cost optimization opportunities
        4. Supplier diversification suggestions
        5. Category-based inventory management insights
        6. Risk mitigation strategies for critical medications
        
        Provide specific, actionable recommendations that a pharmacy manager can implement.
        Focus on improving efficiency, reducing costs, and ensuring medication availability.
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an inventory management expert specializing in pharmacy operations. Provide practical, data-driven recommendations that improve efficiency and patient care while managing costs."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Failed to generate inventory recommendations: {str(e)}")

def analyze_inventory_trends(historical_data):
    """Analyze inventory trends and predict future needs."""
    try:
        prompt = f"""
        Analyze the following historical inventory data and provide trend analysis:
        
        {json.dumps(historical_data, indent=2)}
        
        Please provide:
        1. Usage trend analysis for key medications
        2. Seasonal patterns (if any)
        3. Demand forecasting for the next quarter
        4. Recommendations for inventory planning
        5. Risk assessment for stock-outs
        
        Provide insights that help with strategic inventory planning.
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data analyst specializing in pharmaceutical inventory forecasting. Provide analytical insights based on historical patterns."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Failed to analyze inventory trends: {str(e)}")

def get_medicine_alternatives(medicine_name, reason="shortage"):
    """Get alternative medicines for substitution purposes."""
    try:
        prompt = f"""
        Provide alternative medications for '{medicine_name}' due to {reason}.
        
        Please include:
        1. Generic alternatives (if applicable)
        2. Therapeutic alternatives with similar mechanisms
        3. Considerations for substitution
        4. Dosage conversion information (if different)
        5. Important differences pharmacists should note
        
        Focus on clinically appropriate alternatives that a pharmacist might recommend 
        in consultation with prescribers.
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical pharmacist providing alternative medication options. Always emphasize the importance of prescriber consultation for any therapeutic substitutions."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Failed to get medicine alternatives: {str(e)}")
