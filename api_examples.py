# Case Service API Examples
# This file contains examples of how to use the enhanced dental case management API

import requests
import json
from datetime import datetime, date, timedelta

# Base URL for the API
BASE_URL = "http://127.0.0.1:5000/api/v1"

# Example JWT token (replace with actual token from UMS)
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Headers for authenticated requests
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def create_fixed_prosthetic_case():
    """Example: Create a case for a zirconia crown"""
    case_data = {
        "doctor_id": "doctor_123",
        "product_id": "crown_zirconia_001",
        "case_name": "Patient Smith - Upper Right Molar Crown",
        "description": "Single crown replacement for tooth #3",
        "priority": "medium",
        "case_type": "fixed_prosthetic",
        "due_date": (date.today() + timedelta(days=14)).isoformat(),
        "rush_order": False,
        "patient_info": {
            "patient_id": "patient_456",
            "age": 45,
            "gender": "female",
            "medical_history": "No significant medical history"
        },
        "special_instructions": "Patient prefers natural appearance, match adjacent teeth",
        "fixed_prosthetic": {
            "type": "crown",
            "material": "zirconia",
            "tooth_numbers": [3],
            "preparation_type": "full_coverage",
            "margin_type": "shoulder",
            "shade": {
                "shade_system": "vita_classical",
                "shade_value": "A2",
                "translucency": "low_translucent",
                "notes": "Match to adjacent tooth #2"
            },
            "occlusion_type": "centric_occlusion"
        }
    }
    
    response = requests.post(f"{BASE_URL}/cases/", json=case_data, headers=headers)
    return response.json()

def create_denture_case():
    """Example: Create a case for a complete upper denture"""
    case_data = {
        "doctor_id": "doctor_789",
        "product_id": "denture_complete_upper_001",
        "case_name": "Patient Johnson - Complete Upper Denture",
        "description": "Conventional complete upper denture replacement",
        "priority": "high",
        "case_type": "denture",
        "due_date": (date.today() + timedelta(days=21)).isoformat(),
        "rush_order": False,
        "patient_info": {
            "patient_id": "patient_789",
            "age": 68,
            "gender": "male",
            "medical_history": "Diabetes Type 2, well controlled"
        },
        "special_instructions": "Patient has high smile line, ensure proper tooth display",
        "denture": {
            "type": "complete_upper",
            "material": "acrylic_resin",
            "tooth_material": "acrylic",
            "shade": {
                "shade_system": "vita_classical",
                "shade_value": "A3",
                "shade_description": "Natural aging appearance"
            },
            "retention_type": "conventional_suction"
        }
    }
    
    response = requests.post(f"{BASE_URL}/cases/", json=case_data, headers=headers)
    return response.json()

def create_night_guard_case():
    """Example: Create a case for a dual laminate night guard"""
    case_data = {
        "doctor_id": "doctor_456",
        "product_id": "night_guard_dual_001",
        "case_name": "Patient Williams - Dual Laminate Night Guard",
        "description": "Custom night guard for bruxism protection",
        "priority": "medium",
        "case_type": "night_guard",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "rush_order": True,
        "patient_info": {
            "patient_id": "patient_321",
            "age": 32,
            "gender": "female",
            "medical_history": "History of TMJ disorder"
        },
        "special_instructions": "Patient reports severe nighttime grinding, needs maximum protection",
        "night_guard": {
            "type": "dual_laminate",
            "material": "dual_layer",
            "thickness": "3mm",
            "arch": "upper",
            "design": "full_coverage",
            "special_features": ["bite_ramps", "breathing_holes"]
        }
    }
    
    response = requests.post(f"{BASE_URL}/cases/", json=case_data, headers=headers)
    return response.json()

def create_implant_case():
    """Example: Create a case for an implant crown"""
    case_data = {
        "doctor_id": "doctor_654",
        "product_id": "implant_crown_001",
        "case_name": "Patient Davis - Implant Crown #19",
        "description": "Single implant crown restoration",
        "priority": "high",
        "case_type": "implant",
        "due_date": (date.today() + timedelta(days=10)).isoformat(),
        "rush_order": False,
        "patient_info": {
            "patient_id": "patient_987",
            "age": 55,
            "gender": "male",
            "medical_history": "Osteointegration completed, ready for restoration"
        },
        "special_instructions": "Ensure proper emergence profile for gingival health",
        "implant": {
            "implant_system": "straumann",
            "implant_diameter": "4.1mm",
            "implant_length": "10mm",
            "platform_type": "morse_taper",
            "abutment_type": "custom_abutment",
            "restoration_type": "single_crown",
            "tooth_number": 19,
            "tissue_level": "tissue_level"
        }
    }
    
    response = requests.post(f"{BASE_URL}/cases/", json=case_data, headers=headers)
    return response.json()

def get_case_types():
    """Get available case types and specifications"""
    response = requests.get(f"{BASE_URL}/cases/types", headers=headers)
    return response.json()

def get_shade_systems():
    """Get available shade systems and values"""
    response = requests.get(f"{BASE_URL}/cases/shades", headers=headers)
    return response.json()

def get_materials():
    """Get available materials by category"""
    response = requests.get(f"{BASE_URL}/cases/materials", headers=headers)
    return response.json()

def get_doctor_info(doctor_id):
    """Get doctor account information"""
    response = requests.get(f"{BASE_URL}/cases/doctor-info/{doctor_id}", headers=headers)
    return response.json()

def list_cases_with_filters():
    """Example: List cases with various filters"""
    # Get all pending crown cases
    params = {
        "status": "pending",
        "page": 1,
        "per_page": 20
    }
    response = requests.get(f"{BASE_URL}/cases/", params=params, headers=headers)
    return response.json()

def update_case_status(case_id, new_status):
    """Example: Update case status"""
    status_data = {"status": new_status}
    response = requests.patch(f"{BASE_URL}/cases/{case_id}/status", json=status_data, headers=headers)
    return response.json()

# Example usage
if __name__ == "__main__":
    print("Case Service API Examples")
    print("=" * 40)
    
    try:
        # Get reference data
        print("1. Getting case types...")
        case_types = get_case_types()
        print(json.dumps(case_types, indent=2))
        
        print("\n2. Getting shade systems...")
        shades = get_shade_systems()
        print(json.dumps(shades, indent=2))
        
        print("\n3. Getting materials...")
        materials = get_materials()
        print(json.dumps(materials, indent=2))
        
        # Create different types of cases
        print("\n4. Creating fixed prosthetic case...")
        crown_case = create_fixed_prosthetic_case()
        print(json.dumps(crown_case, indent=2))
        
        print("\n5. Creating denture case...")
        denture_case = create_denture_case()
        print(json.dumps(denture_case, indent=2))
        
        print("\n6. Creating night guard case...")
        guard_case = create_night_guard_case()
        print(json.dumps(guard_case, indent=2))
        
        print("\n7. Creating implant case...")
        implant_case = create_implant_case()
        print(json.dumps(implant_case, indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"Error: {e}")