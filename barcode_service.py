import requests
import os
from typing import Dict, Optional
from ai_services import openai

class BarcodeService:
    """Service for barcode scanning and medicine lookup"""
    
    def __init__(self):
        self.openai_client = openai
    
    def get_medicine_info_from_barcode(self, barcode: str) -> Optional[Dict]:
        """
        Get medicine information from barcode using AI and external APIs
        """
        try:
            # First try to get basic product info from barcode
            product_info = self._lookup_barcode_basic(barcode)
            
            # If we got basic info, enhance it with AI
            if product_info and product_info.get('product_name'):
                enhanced_info = self._enhance_with_ai(product_info)
                return enhanced_info
            else:
                # If no basic info, try AI-based lookup
                return self._ai_barcode_lookup(barcode)
                
        except Exception as e:
            print(f"Error looking up barcode {barcode}: {str(e)}")
            return None
    
    def _lookup_barcode_basic(self, barcode: str) -> Optional[Dict]:
        """
        Basic barcode lookup using free APIs
        """
        try:
            # Try UPC database API (free tier available)
            response = requests.get(
                f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items') and len(data['items']) > 0:
                    item = data['items'][0]
                    return {
                        'barcode': barcode,
                        'product_name': item.get('title', ''),
                        'brand': item.get('brand', ''),
                        'description': item.get('description', ''),
                        'category': item.get('category', ''),
                        'images': item.get('images', [])
                    }
            
            # Fallback to other free barcode APIs could be added here
            return None
            
        except Exception as e:
            print(f"Basic barcode lookup failed: {str(e)}")
            return None
    
    def _enhance_with_ai(self, product_info: Dict) -> Dict:
        """
        Enhance basic product info with AI-generated medicine details
        """
        try:
            product_name = product_info.get('product_name', '')
            prompt = f"""
            Based on the product name "{product_name}", provide detailed pharmacy inventory information.
            Analyze if this is a pharmaceutical product and provide the following in JSON format:
            
            {{
                "is_medicine": true/false,
                "name": "standardized medicine name",
                "category": "medicine category (Prescription/Over-the-counter/etc.)",
                "estimated_price": "estimated unit price in USD",
                "suggested_reorder_point": "suggested reorder quantity",
                "storage_requirements": "storage conditions",
                "common_dosage": "common dosage information",
                "safety_notes": "important safety considerations"
            }}
            
            If this is not a medicine, set is_medicine to false and provide basic product info.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a pharmaceutical expert analyzing products for pharmacy inventory management. Provide accurate, structured information."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            # Try to extract JSON from response
            import json
            try:
                if ai_response:
                    start_idx = ai_response.find('{')
                    end_idx = ai_response.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = ai_response[start_idx:end_idx]
                    ai_data = json.loads(json_str)
                    
                    # Merge with original product info
                    enhanced_info = {**product_info, **ai_data}
                    return enhanced_info
            except json.JSONDecodeError:
                pass
            
            # If JSON parsing fails, return original with AI text
            product_info['ai_analysis'] = ai_response
            return product_info
            
        except Exception as e:
            print(f"AI enhancement failed: {str(e)}")
            return product_info
    
    def _ai_barcode_lookup(self, barcode: str) -> Optional[Dict]:
        """
        AI-based barcode lookup when no API data is available
        """
        try:
            prompt = f"""
            A barcode scan returned the code: {barcode}
            
            Please analyze this barcode and provide medicine information if possible.
            Common barcode formats for medicines include:
            - UPC/EAN codes for over-the-counter medicines
            - NDC (National Drug Code) for prescription medicines
            - GTIN for pharmaceutical products
            
            Provide the following information in JSON format:
            {{
                "barcode": "{barcode}",
                "likely_medicine": true/false,
                "product_name": "best guess product name",
                "category": "estimated category",
                "barcode_type": "UPC/EAN/NDC/GTIN/Unknown",
                "confidence": "high/medium/low",
                "recommendations": "suggestions for pharmacy staff"
            }}
            
            If you cannot identify the product, indicate low confidence and suggest manual entry.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a pharmaceutical barcode expert helping pharmacy staff identify products from barcode scans."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            ai_response = response.choices[0].message.content
            
            # Try to extract JSON
            import json
            try:
                if ai_response:
                    start_idx = ai_response.find('{')
                    end_idx = ai_response.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
            # Return basic structure if parsing fails
            return {
                'barcode': barcode,
                'likely_medicine': False,
                'product_name': 'Unknown Product',
                'confidence': 'low',
                'ai_response': ai_response
            }
            
        except Exception as e:
            print(f"AI barcode lookup failed: {str(e)}")
            return None
    
    def suggest_medicine_data(self, barcode_info: Dict) -> Dict:
        """
        Convert barcode information into suggested medicine form data
        """
        if not barcode_info:
            return {}
        
        suggestions = {}
        
        # Map barcode info to medicine form fields
        if barcode_info.get('name') or barcode_info.get('product_name'):
            suggestions['name'] = barcode_info.get('name') or barcode_info.get('product_name')
        
        if barcode_info.get('category'):
            suggestions['category'] = barcode_info.get('category')
        
        if barcode_info.get('estimated_price'):
            try:
                # Extract numeric price from string
                price_str = str(barcode_info.get('estimated_price'))
                price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_str)))
                suggestions['unit_price'] = price
            except (ValueError, TypeError):
                pass
        
        if barcode_info.get('suggested_reorder_point'):
            try:
                reorder_value = barcode_info.get('suggested_reorder_point')
                if reorder_value is not None:
                    reorder = int(reorder_value)
                    suggestions['reorder_point'] = reorder
            except (ValueError, TypeError):
                suggestions['reorder_point'] = 10  # Default
        
        # Add barcode as batch number for tracking
        if barcode_info.get('barcode'):
            suggestions['batch_number'] = f"BC_{barcode_info.get('barcode')}"
        
        # Add storage location suggestion
        if barcode_info.get('storage_requirements'):
            suggestions['location'] = barcode_info.get('storage_requirements')
        
        return suggestions

# Global instance
barcode_service = BarcodeService()