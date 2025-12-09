#!/usr/bin/env python
# coding: utf-8

# # data cleaning (np_address)

# In[1]:


import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)


# In[2]:


np_address = pd.read_csv("~/Downloads/aidatalab/Georgia_NPs_AddressesNPIs_new.csv")
np_address


# In[3]:


#they're all the same for every row so we can get rid of this col
# np_address['Entity_Type_Code'].nunique()
np_address['MEDICARE_PROVIDER_SUPPLIER_TYPE'].nunique()


# In[4]:


#renames columns and drops unnessecary ones
np_address = np_address.rename(columns={'Provider_Last_Name': 'Last_Name'})
np_address = np_address.rename(columns={'Provider_First_Name': 'First_Name'})
np_address = np_address.rename(columns={'Provider_Credentials': 'Credentials'})
np_address = np_address.rename(columns={'Provider_Enumeration_Date': 'Enumeration_Date'})
np_address = np_address.rename(columns={'Provider_Sex': 'Sex'})
np_address = np_address.rename(columns={'Provider_Taxonomy_Code': 'Taxonomy_Code'})
np_address = np_address.rename(columns={'Provider_License_Number_1': 'License_Number'})
np_address = np_address.rename(columns={'Healthcare_Provider_Primary_Tax': 'Primary_Tax'})
np_address = np_address.rename(columns={'PROVIDER_TAXONOMY_DESCRIPTION_': 'Taxonomy_Description'})
np_address = np_address.rename(columns={'MEDICARE_PROVIDER_SUPPLIER_TYPE': 'Medicare_Supplier_Type'})
np_address = np_address.rename(columns={'MEDICARE_SPECIALTY_CODE': 'Medicare_Specialty_Code'})

np_address = np_address[['NPI', 'Last_Name', 'First_Name', 'Sex', 'Street1', 'Street2', 'City', 'ZIP', 'Credentials', 'Certification_Date', 'Enumeration_Date', 'License_Number', 'NP_Type', 'Taxonomy_Code', 'Taxonomy_Description', 'Medicare_Supplier_Type', 'Primary_Tax', 'Medicare_Specialty_Code']]
np_address


# In[ ]:





# ## grouping np types

# In[5]:


print(np_address["NP_Type"].value_counts())


# groupings:
# 
# Acute Care NP: 744
# Adult/Gero NP: 995
# Community Health/Occupational Health/School NP: 30
# Critical Care NP: 54
# Family/Primary Care NP: 7870
# Neonatal NP: 99
# Neonatal Critical Care NP: 67
# OBGYN/Womens Health NP: 424
# Pediatrics NP: 789
# Pediatrics Critical Care NP: 34
# Psych/Mental Health NP: 768

# In[6]:


mapping = {
    "Acute Care NP": "Acute Care NP",
    "Adult/Gero NP": "Adult/Gero NP",
    "Community Health NP": "Community/Occupational/School NP",
    "Occupational Health NP": "Community/Occupational/School NP",
    "School NP": "Community/Occupational/School NP",
    "Critical Care NP": "Critical Care NP",
    "Family NP": "Family/Primary Care NP",
    "Primary Care NP": "Family/Primary Care NP",
    "Neonatal NP": "Neonatal NP",
    "Neonatal Critical Care NP": "Neonatal Critical Care NP",
    "OBGYN NP": "OBGYN/Womens Health NP",
    "Womens Health NP": "OBGYN/Womens Health NP",
    "Pediatrics NP": "Pediatrics NP",
    "Pediatrics Critical Care NP": "Pediatrics Critical Care NP",
    "Psych/Mental Health NP": "Psych/Mental Health NP",
    "NP, No Subspecialty Noted": "NP, No Subspecialty Noted"
}

np_address["NP_Type_Grouped"] = np_address["NP_Type"].map(mapping)
np_address = np_address[['NPI', 'Last_Name', 'First_Name', 'Sex', 'Street1', 'Street2', 'City', 'ZIP', 'Credentials', 'Certification_Date', 'Enumeration_Date', 'License_Number', 'NP_Type_Grouped', 'Taxonomy_Code', 'Taxonomy_Description', 'Medicare_Supplier_Type', 'Primary_Tax', 'Medicare_Specialty_Code']]
np_address


# ## webscraping

# In[7]:


found = pd.read_csv("~/Downloads/aidatalab/webscrappingversion1.csv")
found


# In[8]:


# Ensure NPI is string so matching works
found['NPI'] = found['NPI'].astype(str)
np_address['NPI'] = np_address['NPI'].astype(str)

# Create a mapping: NPI → specialty
specialty_map = found.set_index('NPI')['Specialty']

# Overwrite NP_Type_Grouped ONLY where an NPI exists in found
np_address['NP_Type_Grouped'] = np_address['NPI'].map(specialty_map).fillna(np_address['NP_Type_Grouped'])


# In[9]:


np_address


# In[10]:


found2 = pd.read_csv("~/Downloads/aidatalab/webscrappingversion2.csv")
found2


# In[11]:


found2['NPI'] = found2['NPI'].astype(str)
np_address['NPI'] = np_address['NPI'].astype(str)

specialty_map2 = found2.set_index('NPI')['Specialty']

np_address['NP_Type_Grouped'] = np_address['NPI'].map(specialty_map2).fillna(np_address['NP_Type_Grouped'])
np_address


# In[12]:


found3 = pd.read_csv("~/Downloads/aidatalab/1-1000.csv")
found3['NPI'] = found3['NPI'].astype(str)
np_address['NPI'] = np_address['NPI'].astype(str)

specialty_map3 = found3.set_index('NPI')['Specialty']

np_address['NP_Type_Grouped'] = np_address['NPI'].map(specialty_map3).fillna(np_address['NP_Type_Grouped'])


# In[13]:


found4 = pd.read_csv("~/Downloads/aidatalab/1001-REST.csv")
found4['NPI'] = found4['NPI'].astype(str)
np_address['NPI'] = np_address['NPI'].astype(str)

specialty_map4 = found4.set_index('NPI')['Specialty']

np_address['NP_Type_Grouped'] = np_address['NPI'].map(specialty_map4).fillna(np_address['NP_Type_Grouped'])


# ## filling np no subspeciatly based on credential (more accurate)

# In[14]:


# --- 1. Create mapping dictionary from your groups ---

specialty_map = {
    "Acute Care NP": [
        "ACNPC-AG", "ACNP", "NP (ACNP", "ACNP-BC", "A.C.N.P.", "ACNPC"
    ],
    "Adult/Gero NP": [
        "AGACNP-B", "AGNP-C", "AGNP", "GNP", "AGACNP", "ACNP-AG", "MSN, ANP", "ANP",
        "AGPCNP-B", "AGACNP,", "AGPCNP", "A-GNP", "AGPCNP-C", "APRN, AG", "ANP-BC,",
        "AGACNP-C", "ANP, CNS", "AGPC-BC"
    ],
    "Family/Primary Care NP": [
        "FNP-C", "FNP", "FNP-BC", "MSN, FNP", "FNP, B.C", "DNP, FNP", "FNP, PHD", "CFNP",
        "APRN, FN", "FNP, PNP", "FNP-L", "FNP C", "MSN-FNP,", "F.N.P.", "FNPC"
    ],
    "Neonatal NP": [
        "NNP-BC"
    ],
    "NP No Subspecialty Noted": [
        # Very large group, but we do NOT use this group for replacement
    ],
    "OBGYN/Womens Health NP": [
        "WHNP-BC", "WHNP", "FP/WHNP-", "CNM MSN", "CNM"
    ],
    "Pediatrics Critical Care NP": [
        "PNP-PC/A", "CPNP-AC"
    ],
    "Pediatrics NP": [
        "CPNP", "PNP", "DNP, CPN", "CPNP-PC", "C.P.N.P."
    ],
    "Psych/Mental Health NP": [
        "PMHNP-BC", "APRN, PM"
    ]
}

# --- 2. Reverse-map each credential to its specialty group ---

credential_to_specialty = {}

for specialty, creds in specialty_map.items():
    for c in creds:
        credential_to_specialty[c] = specialty


# --- 3. Function to match credential to specialty ---
def map_specialty_from_credential(credential):
    if pd.isna(credential):
        return None

    credential_str = str(credential).strip()

    # exact match first
    if credential_str in credential_to_specialty:
        return credential_to_specialty[credential_str]

    # fuzzy match: contains string (helps for trailing commas, etc.)
    for cred, spec in credential_to_specialty.items():
        if isinstance(cred, str) and cred in credential_str:
            return spec

    return None


# --- 4. Apply: only replace rows where np_type_grouped == "NP, No Subspecialty Noted" ---

mask = np_address["NP_Type_Grouped"] == "NP, No Subspecialty Noted"

np_address.loc[mask, "NP_Type_Grouped"] = (
    np_address.loc[mask, "Credentials"]
    .apply(map_specialty_from_credential)
    .fillna("NP, No Subspecialty Noted")  # keep original if no match found
)

np_address


# ## (old) filling missing specialties

# In[10]:


undefined = np_address[np_address['NP_Type_Grouped'] == 'NP, No Subspecialty Noted']
undefined


# In[11]:


#nps matched from web scraping + matching on credentials
2593-609


# In[17]:


undefined.to_csv('NEW_missing_specialty.csv', index=False)


# In[17]:


#how many people are missing credentials and np specialty entirely
miss_cred = undefined[undefined['Credentials'].isna()]
miss_cred


# In[ ]:


# num nps with either no credentials or general credentials that have no specialty notes


# In[ ]:





# In[18]:


#print(missing['Taxonomy_Code'].unique()) => only returns '363L00000X' which is the generic NP code
#but they have different credentials!
print(undefined['Credentials'].unique())


# In[10]:


#list the credentials that each np_type has in the np_address df and use that list of credentials to map 'NP, No Subspecialty Noted' nps to an NP_Type
defined = np_address[np_address['NP_Type_Grouped'] != 'NP, No Subspecialty Noted']
cred_by_type = (
    defined.groupby('NP_Type_Grouped')['Credentials']
    .unique()
    .apply(lambda x: sorted([str(i).strip().upper() for i in x if pd.notna(i)]))
)

for np_type, creds in cred_by_type.items():
    print(f"\n{np_type}:")
    print(creds)


# In[11]:


#credential -> most common NP_Type_Grouped
cred_to_type = (
    defined.groupby('Credentials')['NP_Type_Grouped']
    .agg(lambda x: x.value_counts().idxmax())  # most frequent NP_Type for that credential
    .dropna()
)

#check the mapping
mapping_df = cred_to_type.reset_index().rename(columns={'index': 'Credentials', 'NP_Type_Grouped': 'Mapped_NP_Type'})
mapping_df


# In[12]:


#may group generic NPs with family/primary since that makes up the large majority of NPs nationally
#verified by frequency!!!!!!
test = mapping_df[mapping_df['Credentials'].isin(['NP', 'N.P.'])]
test


# In[13]:


#fill in missing NP_Type_Grouped values
mask = np_address['NP_Type_Grouped'] == 'NP, No Subspecialty Noted'
np_address.loc[mask, 'NP_Type_Grouped'] = np_address.loc[mask, 'Credentials'].map(cred_to_type)
np_address


# In[14]:


#verify how many were filled
filled_count = np_address.loc[mask, 'NP_Type_Grouped'].notna().sum()
print(f"Filled {filled_count} previously 'No Subspecialty' NPs")


# In[15]:


#missing 2593 - 2230 specialties = 363
not_grouped = np_address[np_address['NP_Type_Grouped'].isna()]
not_grouped


# In[16]:


#which in not_grouped are NOT in miss_cred (should be 363-288=75)
weird = not_grouped[not_grouped['Credentials'].notna()]
weird


# In[17]:


#these are ones with credentials that the other nurses didn't have so we have to assign them to a NP_Group_Type based on what these credentials typically mean
print(weird['Credentials'].unique())


# In[18]:


#repeat mapping procedure with new credentials
np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'ACNP|NP-ADVAN|APRN OR|A.C.N.P.|CRNFA|DCNP|AOCNP|AGPC-BC|RNFA|NP \(ACNP', 
        case=False, na=False), 'NP_Type_Grouped'] = 'Acute Care NP'

np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'APN-C, A|ANP|GNP|ADULT NU|APRN AGA|GNP-BC', 
        case=False, na=False), 'NP_Type_Grouped'] = 'Adult/Gero NP'

np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'CNS|RN, CDE', 
        case=False, na=False), 'NP_Type_Grouped'] = 'Community/Occupational/School NP'

np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'LPN|C\\.N\\.P|MSN, PHD|PH\\.D\\. AP|N\\.P\\.C\\.|FNP|FNPC|F\\.N\\.P\\.|FNB|MSN-FNP|FNP-L|NP, AANP|BSN NP|MS, NP-C|MSN,NP-C|FNP-BC|FNP-C|FNPC FAM|CPT,FNP-|F.N.P.-B|FNP-BC,N|FNP, PHD|FNP, PNP|FNP, B.C|MS, ARNP|MSN, OCN|NP-C, DN', 
        case=False, na=False), 'NP_Type_Grouped'] = 'Family/Primary Care NP'

np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'PNP|NP, RNC|PNP-PC', 
        case=False, na=False), 'NP_Type_Grouped'] = 'Neonatal NP'

np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'WHNP|CNM|FP/WHNP|APRN WHN|CNM/ARNP|CNM MSN', 
        case=False, na=False), 'NP_Type_Grouped'] = 'OBGYN/Womens Health NP'

np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'RN PNP|PNP', 
        case=False, na=False), 'NP_Type_Grouped'] = 'Pediatrics NP'

np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].notna() & 
    np_address['Credentials'].str.contains(
        'PMHNP|PHD, CAN', 
        case=False, na=False), 'NP_Type_Grouped'] = 'Psych/Mental Health NP'

np_address.loc[np_address['NP_Type_Grouped'].isna(), 'NP_Type_Grouped'] = 'Unclassified NP'

np_address


# In[19]:


#0 means we successfully matched all previously no specialty defined NPs to a specialty
#but there are remaining NaNs: should only be rows where both Credentials and NP_Type_Grouped are missing (288 as seen in miss_cred!)
test = np_address[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].isna()]
test


# In[20]:


#so what to do with these people???
print(test['Taxonomy_Code'].unique())
print(test['Taxonomy_Description'].unique())
print(test['Medicare_Supplier_Type'].unique())
#since all other possible identifiers are the same across all these NPs, we will just make a new category of unknown specialty :(


# In[21]:


np_address.loc[np_address['NP_Type_Grouped'].isna() & np_address['Credentials'].isna(), 'NP_Type_Grouped'] = 'Unclassified NP'
x = np_address[np_address['NP_Type_Grouped'].isna()]
print(x['Credentials'].unique())

#other noncategorizable credentials: 'RN 03380', 'RN 12088', 'RN 05389', 'EDD, RN,' (bc Doctor of Education doesn't actually do clinical care), 'MD' 


# In[22]:


test2 = np_address[np_address['NP_Type_Grouped']=='Unclassified NP']
test2


# # mapping zip (hud crosswalk)

# In[15]:


crosswalk = pd.read_csv("~/Downloads/aidatalab/ZipCounty_Crosswalk.csv")
crosswalk = crosswalk[crosswalk["USPS_ZIP_PREF_STATE"] == ("GA")]
crosswalk["ZIP"] = crosswalk["ZIP"].astype(str).str[:5]
crosswalk


# In[16]:


np_address["ZIP"] = np_address["ZIP"].astype(str).str[:5]
np_address


# In[17]:


#lookup dict
zip_county_weights = (crosswalk.groupby('ZIP').apply(lambda g: (g['COUNTY'].tolist(), g['RES_RATIO'].tolist())).to_dict())

#function to assign based on res_ratio
def assign_county(ZIP):
    entry = zip_county_weights.get(ZIP)
    if not entry:
        return np.nan

    counties, weights = entry
    weights = np.array(weights, dtype=float)

    weights = np.where(np.isnan(weights) | (weights < 0), 0, weights)
    total = weights.sum()
    if total == 0:
        # all weights invalid → choose randomly among available counties
        return np.random.choice(counties)

    weights = np.nan_to_num(weights)
    weights = weights / weights.sum()

    return np.random.choice(counties, p=weights)

np_address['County'] = np_address['ZIP'].apply(assign_county)
np_address


# In[18]:


print("Mapped:", np_address['County'].notna().sum(), "of", len(np_address))


# In[19]:


#almost all in other states??? LOL
14467-14456


# In[ ]:





# In[20]:


np_address["County"] = np_address["County"].astype(str).str[:5]
np_address


# In[21]:


fips = pd.read_csv("~/Downloads/aidatalab/GA_FIPS.csv")
fips['FIPS Code'] = fips['FIPS Code'].astype(str)
fips


# In[22]:


fips_map = fips.set_index('FIPS Code')['County Name'].to_dict()
np_address['County'] = np_address['County'].astype(str)
np_address['County_Name'] = np_address['County'].map(fips_map)
np_address


# In[30]:


np_address["County_Name"].nunique()


# In[51]:


np_address[np_address["County_Name"] == "Talbot"]


# In[52]:


np_address.to_csv('shape_mapping.csv', index=False)


# In[43]:


agg = np_address.groupby(['County_Name']).size().reset_index(name='count')
agg


# In[50]:


agg["County_Name"].unique()


# In[ ]:


final


# # mapping zip (geocoding)

# In[32]:


#standardize address:

np_address['Street1'] = np_address['Street1'].fillna('')
np_address['Street2'] = np_address['Street2'].fillna('')

#convert to lower case
np_address['Street1'] = np_address['Street1'].str.upper().str.strip()
np_address['Street2'] = np_address['Street2'].str.upper().str.strip()

#punctuation
np_address['Street1'] = np_address['Street1'].str.replace(r'[^\w\s]', '', regex=True)
np_address['Street2'] = np_address['Street2'].str.replace(r'[^\w\s]', '', regex=True)

#common abbreviations
abbrev_map = {
    r'\bST\b\.?': 'STREET',
    r'\bRD\b\.?': 'ROAD',
    r'\bAVE\b\.?': 'AVENUE',
    r'\bBLVD\b\.?': 'BOULEVARD',
    r'\bDR\b\.?': 'DRIVE',
    r'\bLN\b\.?': 'LANE',
    r'\bCT\b\.?': 'COURT',
    r'\bPL\b\.?': 'PLACE',
    r'\bPKWY\b\.?': 'PARKWAY',
    r'\bHWY\b\.?': 'HIGHWAY',
    r'\bTER\b\.?': 'TERRACE',
    r'\bST\b\.?': 'SUITE',
    r'\bHO\b\.?': 'HOSPITAL',
}

for abbrev, full in abbrev_map.items():
    np_address['Street1'] = np_address['Street1'].str.replace(abbrev, full, regex=True)
    np_address['Street2'] = np_address['Street2'].str.replace(abbrev, full, regex=True)

#all zip codes to first 5 digits
np_address["ZIP"] = np_address["ZIP"].astype(str).str[:5]
np_address

np_address


# In[33]:


#combine to one address line
np_address['full_address'] = (
    np_address['Street1'] + ' ' +
    np_address['Street2'] + ', ' +
    np_address['City'] + ', ' +
    'GA'
)

np_address

