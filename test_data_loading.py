#!/usr/bin/env python3
"""
Test script to verify CSV data loading.
This script checks the data before and after loading to ensure everything works correctly.
"""

import csv
import json
import sys
import os
from typing import Dict, List

def validate_csv_files():
    """Validate CSV files before loading."""
    print("Validating CSV files...")
    
    # Check if files exist
    churches_csv = "churches_with_denominations.csv"
    speakers_csv = "speakers.csv"
    
    if not os.path.exists(churches_csv):
        print(f"Error: {churches_csv} not found")
        return False
    
    if not os.path.exists(speakers_csv):
        print(f"Error: {speakers_csv} not found")
        return False
    
    # Validate churches CSV
    print("Validating churches CSV...")
    church_names = set()
    
    with open(churches_csv, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        required_fields = ['name', 'denomination']
        
        for row_num, row in enumerate(reader, start=2):
            # Check required fields
            for field in required_fields:
                if not row.get(field):
                    print(f"Error: Missing required field '{field}' in churches CSV at row {row_num}")
                    return False
            
            # Check for duplicate church names
            church_name = row['name']
            if church_name in church_names:
                print(f"Warning: Duplicate church name '{church_name}' in churches CSV")
            church_names.add(church_name)
            
            # Validate JSON fields
            json_fields = ['address', 'service_times', 'social_media']
            for field in json_fields:
                if row.get(field):
                    try:
                        json.loads(row[field])
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON in field '{field}' at row {row_num}")
                        return False
    
    print(f"  Found {len(church_names)} unique churches")
    
    # Validate speakers CSV
    print("Validating speakers CSV...")
    speaker_names = set()
    referenced_churches = set()
    
    with open(speakers_csv, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        required_fields = ['name']
        
        for row_num, row in enumerate(reader, start=2):
            # Check required fields
            for field in required_fields:
                if not row.get(field):
                    print(f"Error: Missing required field '{field}' in speakers CSV at row {row_num}")
                    return False
            
            # Check for duplicate speaker names
            speaker_name = row['name']
            if speaker_name in speaker_names:
                print(f"Warning: Duplicate speaker name '{speaker_name}' in speakers CSV")
            speaker_names.add(speaker_name)
            
            # Collect referenced church names
            church_name = row.get('church_name', '')
            if church_name:
                referenced_churches.add(church_name)
            
            # Validate JSON fields
            json_fields = ['social_media', 'speaking_topics']
            for field in json_fields:
                if row.get(field):
                    try:
                        json.loads(row[field])
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON in field '{field}' at row {row_num}")
                        return False
            
            # Validate enum fields
            enum_fields = {
                'teaching_style': ['WARM_AND_CONVERSATIONAL', 'CALM_AND_REFLECTIVE', 'PASSIONATE_AND_HIGH_ENERGY'],
                'bible_approach': ['MORE_SCRIPTURE', 'MORE_APPLICATION', 'BALANCED'],
                'environment_style': ['TRADITIONAL', 'CONTEMPORARY', 'BLENDED'],
                'gender': ['MALE', 'FEMALE']
            }
            
            for field, valid_values in enum_fields.items():
                value = row.get(field, '')
                if value and value not in valid_values:
                    print(f"Warning: Invalid enum value '{value}' for field '{field}' at row {row_num}")
    
    print(f"  Found {len(speaker_names)} unique speakers")
    print(f"  Found {len(referenced_churches)} referenced churches")
    
    # Check for orphaned church references
    orphaned_churches = referenced_churches - church_names
    if orphaned_churches:
        print(f"Warning: Speakers reference churches not found in churches CSV:")
        for church in orphaned_churches:
            print(f"  - {church}")
    
    print("CSV validation completed successfully!")
    return True

def check_data_consistency():
    """Check data consistency between CSV files."""
    print("\nChecking data consistency...")
    
    # Load church names from churches CSV
    church_names = set()
    with open("churches_with_denominations.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            church_names.add(row['name'])
    
    # Check speaker church references
    missing_churches = set()
    with open("speakers.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            church_name = row.get('church_name', '')
            if church_name and church_name not in church_names:
                missing_churches.add(church_name)
    
    if missing_churches:
        print(f"Error: {len(missing_churches)} speakers reference churches not found in churches CSV:")
        for church in missing_churches:
            print(f"  - {church}")
        return False
    
    print("Data consistency check passed!")
    return True

def generate_summary():
    """Generate a summary of the data to be loaded."""
    print("\nGenerating data summary...")
    
    # Churches summary
    denominations = {}
    with open("churches_with_denominations.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            denom = row['denomination']
            denominations[denom] = denominations.get(denom, 0) + 1
    
    print("Churches by denomination:")
    for denom, count in sorted(denominations.items()):
        print(f"  {denom}: {count}")
    
    # Speakers summary
    genders = {}
    teaching_styles = {}
    with open("speakers.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            gender = row.get('gender', 'Unknown')
            teaching_style = row.get('teaching_style', 'Unknown')
            
            genders[gender] = genders.get(gender, 0) + 1
            teaching_styles[teaching_style] = teaching_styles.get(teaching_style, 0) + 1
    
    print("\nSpeakers by gender:")
    for gender, count in sorted(genders.items()):
        print(f"  {gender}: {count}")
    
    print("\nSpeakers by teaching style:")
    for style, count in sorted(teaching_styles.items()):
        print(f"  {style}: {count}")

def main():
    """Main function to run all validation checks."""
    print("CSV Data Loading Validation")
    print("=" * 40)
    
    # Validate CSV files
    if not validate_csv_files():
        print("\nValidation failed!")
        return 1
    
    # Check data consistency
    if not check_data_consistency():
        print("\nData consistency check failed!")
        return 1
    
    # Generate summary
    generate_summary()
    
    print("\nAll validation checks passed!")
    print("The CSV files are ready for database loading.")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
