import csv
import requests
import time
import json
import os
import sys
import re
from typing import Dict, Optional, List, Tuple
from urllib.parse import quote

def lookup_npi_specialty(npi: str) -> Tuple[Optional[str], str]:
    """
    Look up specialty information from NPI Registry API.
    Returns: (specialty, source)
    """
    try:
        url = f"https://npiregistry.cms.hhs.gov/api/?version=2.1&number={npi}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('result_count', 0) > 0:
            result = data['results'][0]
            
            # Check taxonomy classifications for specialty
            taxonomies = result.get('taxonomies', [])
            for taxonomy in taxonomies:
                desc = taxonomy.get('desc', '').upper()
                code = taxonomy.get('code', '')
                
                # Extract specialty from taxonomy description
                if 'FAMILY' in desc or code == '363LF0000X':
                    return 'Family Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'ADULT' in desc or code == '363LA2200X':
                    return 'Adult Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'PEDIATRIC' in desc or 'PEDIATRICS' in desc or code == '363LP0200X':
                    return 'Pediatric Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'WOMEN' in desc or 'WOMENS' in desc or code == '363LW0102X':
                    return 'Women\'s Health Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'PSYCHIATRIC' in desc or 'MENTAL HEALTH' in desc or code == '363LP0808X':
                    return 'Psychiatric-Mental Health Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'ACUTE CARE' in desc or code == '363LA2100X':
                    return 'Acute Care Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'GERONTOLOGY' in desc or 'GERIATRIC' in desc or code == '363LG0600X':
                    return 'Gerontology Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'NEONATAL' in desc or code == '363LN0000X':
                    return 'Neonatal Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'ONCOLOGY' in desc or code == '363LX0001X':
                    return 'Oncology Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'EMERGENCY' in desc or code == '363LE0003X':
                    return 'Emergency Nurse Practitioner', f'NPI Registry (NPI: {npi})'
            
            # If no specific specialty found, check primary taxonomy
            if taxonomies:
                primary = taxonomies[0]
                desc = primary.get('desc', '')
                if desc:
                    # Extract specialty from description
                    if 'FAMILY' in desc.upper():
                        return 'Family Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                    elif 'ADULT' in desc.upper():
                        return 'Adult Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                    elif 'PEDIATRIC' in desc.upper():
                        return 'Pediatric Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                    elif 'WOMEN' in desc.upper():
                        return 'Women\'s Health Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                    elif 'PSYCHIATRIC' in desc.upper() or 'MENTAL HEALTH' in desc.upper():
                        return 'Psychiatric-Mental Health Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                    elif 'ACUTE CARE' in desc.upper():
                        return 'Acute Care Nurse Practitioner', f'NPI Registry (NPI: {npi})'
            
            # Fallback: check credentials in basic info
            basic = result.get('basic', {})
            credentials = basic.get('credential', '')
            if credentials:
                cred_upper = credentials.upper()
                if 'FNP' in cred_upper or 'FAMILY' in cred_upper:
                    return 'Family Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'ANP' in cred_upper or 'ADULT' in cred_upper:
                    return 'Adult Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'PNP' in cred_upper or 'PEDIATRIC' in cred_upper:
                    return 'Pediatric Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'WHNP' in cred_upper or 'WOMEN' in cred_upper:
                    return 'Women\'s Health Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'PMHNP' in cred_upper or 'PSYCH' in cred_upper:
                    return 'Psychiatric-Mental Health Nurse Practitioner', f'NPI Registry (NPI: {npi})'
                elif 'ACNP' in cred_upper or 'ACUTE' in cred_upper:
                    return 'Acute Care Nurse Practitioner', f'NPI Registry (NPI: {npi})'
        
        return None, f'NPI Registry (NPI: {npi}) - Not found'
    
    except Exception as e:
        return None, f'NPI Registry API Error: {str(e)}'

def search_web_specialty(first_name: str, last_name: str, npi: str, city: str = '') -> Tuple[Optional[str], str]:
    """
    Search for NP specialty using web search across multiple sources.
    Returns: (specialty, source)
    """
    # More specific keyword matching - require exact credential matches or specific phrases
    specialty_keywords = {
        'Family Nurse Practitioner': ['fnp', 'fnp-c', 'fnp-bc', 'family nurse practitioner', 'family practice np'],
        'Adult Nurse Practitioner': ['anp', 'anp-c', 'anp-bc', 'adult nurse practitioner', 'adult health np'],
        'Pediatric Nurse Practitioner': ['pnp', 'pnp-c', 'pnp-bc', 'pediatric nurse practitioner', 'pediatric np'],
        'Women\'s Health Nurse Practitioner': ['whnp', 'whnp-c', 'women\'s health nurse practitioner', 'womens health np', 'ob/gyn np'],
        'Psychiatric-Mental Health Nurse Practitioner': ['pmhnp', 'pmhnp-c', 'psychiatric nurse practitioner', 'mental health np', 'psychiatric mental health'],
        'Acute Care Nurse Practitioner': ['acnp', 'acnp-c', 'acute care nurse practitioner', 'acute care np'],
        'Gerontology Nurse Practitioner': ['gnp', 'gnp-c', 'gerontology nurse practitioner', 'geriatric np'],
        'Neonatal Nurse Practitioner': ['nnp', 'nnp-c', 'neonatal nurse practitioner', 'neonatal np'],
        'Oncology Nurse Practitioner': ['oncology nurse practitioner', 'oncology np'],
        'Emergency Nurse Practitioner': ['enp', 'enp-c', 'emergency nurse practitioner', 'emergency np'],
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # Try HIPAASpace NPI lookup
    if npi:
        try:
            url = f'https://www.hipaaspace.com/medical/provider/npi/{npi}'
            response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
            if response.status_code == 200:
                content = response.text.upper()
                # Look for specialty keywords - require exact credential matches or full specialty name
                for specialty, keywords in specialty_keywords.items():
                    for keyword in keywords:
                        # Only match if it's a credential code or full specialty name (more specific)
                        if keyword.upper() in content:
                            # Additional check: make sure it's not just a generic word match
                            if len(keyword) >= 3 and (keyword.upper() in ['FNP', 'ANP', 'PNP', 'WHNP', 'PMHNP', 'ACNP', 'GNP', 'NNP', 'ENP'] or 
                                'nurse practitioner' in keyword.lower() or 'np' in keyword.lower()):
                                return specialty, f'HIPAASpace (NPI: {npi})'
        except Exception as e:
            pass
    
    # Try NPI Profile
    if npi:
        try:
            url = f'https://npiprofile.com/npi/{npi}'
            response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
            if response.status_code == 200:
                content = response.text.upper()
                for specialty, keywords in specialty_keywords.items():
                    for keyword in keywords:
                        if keyword.upper() in content:
                            return specialty, f'NPI Profile (NPI: {npi})'
        except Exception as e:
            pass
    
    # Try searching NPI Registry website directly (not API)
    if npi:
        try:
            url = f'https://npiregistry.cms.hhs.gov/provider-view/{npi}'
            response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
            if response.status_code == 200:
                content = response.text.upper()
                for specialty, keywords in specialty_keywords.items():
                    for keyword in keywords:
                        if keyword.upper() in content:
                            return specialty, f'NPI Registry Website (NPI: {npi})'
        except Exception as e:
            pass
    
    # Try MediFind search - be very careful with matching
    try:
        search_name = f"{first_name.lower()}-{last_name.lower()}"
        url = f'https://www.medifind.com/doctors/{search_name}'
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            content = response.text.upper()
            # Only match on credential codes or full specialty phrases, avoid generic words
            for specialty, keywords in specialty_keywords.items():
                for keyword in keywords:
                    keyword_upper = keyword.upper()
                    # Only trust credential codes (FNP, ANP, etc.) or full specialty names
                    if keyword_upper in content:
                        # Skip if it's just a generic word that might appear in page text
                        if keyword_upper in ['FNP', 'ANP', 'PNP', 'WHNP', 'PMHNP', 'ACNP', 'GNP', 'NNP', 'ENP']:
                            return specialty, f'MediFind'
                        elif 'NURSE PRACTITIONER' in keyword_upper or 'NP' in keyword_upper:
                            # Only match if it's a full specialty phrase, not just "emergency" or "acute"
                            if len(keyword) > 10:  # Full phrases are more reliable
                                return specialty, f'MediFind'
    except Exception as e:
        pass
    
    return None, 'Web search - Not found in additional sources'

def infer_specialty_from_credentials(credentials: str) -> Optional[str]:
    """
    Infer specialty from credentials field if available.
    """
    if not credentials:
        return None
    
    cred_upper = credentials.upper()
    
    if 'FNP' in cred_upper or 'FAMILY' in cred_upper:
        return 'Family Nurse Practitioner'
    elif 'ANP' in cred_upper or 'ADULT' in cred_upper:
        return 'Adult Nurse Practitioner'
    elif 'PNP' in cred_upper or 'PEDIATRIC' in cred_upper:
        return 'Pediatric Nurse Practitioner'
    elif 'WHNP' in cred_upper or 'WOMEN' in cred_upper:
        return 'Women\'s Health Nurse Practitioner'
    elif 'PMHNP' in cred_upper or 'PSYCH' in cred_upper:
        return 'Psychiatric-Mental Health Nurse Practitioner'
    elif 'ACNP' in cred_upper or 'ACUTE' in cred_upper:
        return 'Acute Care Nurse Practitioner'
    elif 'GNP' in cred_upper or 'GERONTOLOGY' in cred_upper or 'GERIATRIC' in cred_upper:
        return 'Gerontology Nurse Practitioner'
    elif 'NNP' in cred_upper or 'NEONATAL' in cred_upper:
        return 'Neonatal Nurse Practitioner'
    elif 'ONCOLOGY' in cred_upper:
        return 'Oncology Nurse Practitioner'
    elif 'ENP' in cred_upper or 'EMERGENCY' in cred_upper:
        return 'Emergency Nurse Practitioner'
    
    return None

def process_csv(input_file: str, output_file: str, start_row: int = 0, batch_size: int = 100):
    """
    Process the CSV file and add Specialty column.
    
    Args:
        input_file: Input CSV file path
        output_file: Output CSV file path
        start_row: Starting row index (0-based, excluding header)
        batch_size: Number of rows to process in this batch
    """
    rows = []
    headers = []
    
    # Read the CSV file
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    # Add Specialty and Source columns if they don't exist
    if 'Specialty' not in headers:
        headers = list(headers) + ['Specialty', 'Source']
    else:
        headers = list(headers)
        if 'Source' not in headers:
            headers.append('Source')
    
    total_rows = len(rows)
    end_row = min(start_row + batch_size, total_rows)
    
    print(f"Processing rows {start_row + 1} to {end_row} (batch size: {batch_size})")
    print(f"Total rows in file: {total_rows}\n")
    
    # Process only the specified batch
    batch_rows = rows[start_row:end_row]
    
    for idx, row in enumerate(batch_rows, start=start_row + 1):
        # Skip if already has specialty (from previous batch)
        if row.get('Specialty') and row.get('Specialty') != 'Specialty Not Found':
            print(f"Skipping row {idx} - already has specialty: {row.get('Specialty')}")
            continue
            
        npi = row.get('NPI', '').strip()
        credentials = row.get('Credentials', '').strip()
        first_name = row.get('First_Name', '').strip()
        last_name = row.get('Last_Name', '').strip()
        
        specialty = None
        source = ''
        
        # First, try to infer from credentials if available
        if credentials:
            specialty = infer_specialty_from_credentials(credentials)
            if specialty:
                source = f'Inferred from Credentials field: {credentials}'
        
        # If not found, look up via NPI Registry API
        if not specialty and npi:
            print(f"Looking up {first_name} {last_name} (NPI: {npi})... [Row {idx}/{total_rows}]")
            specialty, source = lookup_npi_specialty(npi)
            time.sleep(0.5)  # Be respectful to the API
        
        # If still not found, try web search on additional sources
        if not specialty or specialty == 'Specialty Not Found':
            city = row.get('City', '').strip()
            print(f"  Searching additional sources for {first_name} {last_name}...")
            web_specialty, web_source = search_web_specialty(first_name, last_name, npi, city)
            if web_specialty:
                specialty = web_specialty
                source = web_source
            time.sleep(1)  # Be respectful to web sources
        
        # If still not found, mark as unknown
        if not specialty or specialty == 'Specialty Not Found':
            specialty = 'Specialty Not Found'
            if not source or source == 'Not found in NPI Registry or credentials':
                source = 'Not found in NPI Registry, credentials, or additional web sources'
        
        row['Specialty'] = specialty
        row['Source'] = source
        
        # Progress update every 25 rows
        if (idx - start_row) % 25 == 0:
            print(f"Processed {idx - start_row}/{len(batch_rows)} rows in this batch...")
    
    # Check if output file exists and merge with existing data
    if os.path.exists(output_file):
        # Read existing output file with error handling
        try:
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                existing_rows = list(reader)
        except Exception as e:
            print(f"Warning: Could not read existing output file: {e}. Starting fresh.")
            existing_rows = []
        
        # Update the batch rows in existing data
        for i, batch_row in enumerate(batch_rows):
            row_idx = start_row + i
            if row_idx < len(existing_rows):
                existing_rows[row_idx] = batch_row
            else:
                # If output file has fewer rows, append
                existing_rows.append(batch_row)
        all_rows = existing_rows
    else:
        # First time: use all rows from input, with updated batch
        all_rows = rows[:start_row] + batch_rows + rows[end_row:]
    
    # Write the updated CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\nBatch completed! Updated CSV saved to: {output_file}")
    print(f"Processed rows {start_row + 1} to {end_row} of {total_rows}")
    print(f"Next batch: start_row={end_row}, batch_size={batch_size}")

if __name__ == '__main__':
    input_file = '/Users/jiwonii/Desktop/specialty_not_found_only.csv'
    output_file = '/Users/jiwonii/Desktop/secondbathofthefile.csv'
    
    # Get batch parameters from command line or use defaults
    start_row = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    print("=" * 60)
    print("NP Specialty Lookup - Batch Processing")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Starting at row: {start_row + 1} (0-based index: {start_row})")
    print(f"Batch size: {batch_size} rows")
    print("=" * 60)
    print("\nStarting NP Specialty lookup process...")
    print("This may take a while due to API rate limiting...\n")
    
    process_csv(input_file, output_file, start_row=start_row, batch_size=batch_size)

