#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import geopandas as gpd
pd.set_option('display.max_columns', None)


# In[2]:


import folium
import mapclassify
from matplotlib import pyplot as plt


# In[3]:


np_address = pd.read_csv("~/Downloads/aidatalab/shape_mapping.csv")
np_address["County"] = np_address["County"].astype(str).str[:5]
np_address


# In[4]:


georgia = gpd.read_file("~/Downloads/aidatalab/cb_2024_13_bg_500k/cb_2024_13_bg_500k.shp")
georgia['COUNTYFP'] = '13' + georgia['COUNTYFP'].astype(str).str.zfill(3)
georgia = georgia.rename(columns={'COUNTYFP': 'County'})
georgia


# In[5]:


merged = georgia.merge(np_address, on='County', how='right')
merged


# In[6]:


# Count number of NPs per county and NP type, but keep all columns
merged['count'] = merged.groupby(['County_Name', 'NP_Type_Grouped'])['NPI'].transform('count')
merged


# ## aggregating

# In[7]:


# Count number of NPs per county
merged['NP_count'] = merged.groupby('County_Name')['NPI'].transform('count')
merged


# In[8]:


georgia_agg = georgia.dissolve(by='County', as_index=False)
merged = georgia_agg.merge(np_address, on='County', how='right')
merged


# In[9]:


merged['County'].nunique()


# In[10]:


print(merged['County_Name'].unique())


# In[11]:


merged = gpd.GeoDataFrame(merged, geometry='geometry', crs="EPSG:4269")  # or 4326 if needed
merged


# In[12]:


import geopandas as gpd
import pandas as pd

# 1. Define specialties
specialties = [
    "Acute Care NP",
    "Adult/Gero NP",
    "Community/Occupational/School NP",
    "Critical Care NP",
    "Family/Primary Care NP",
    "Neonatal NP",
    "Neonatal Critical Care NP",
    "OBGYN/Womens Health NP",
    "Pediatrics NP",
    "Pediatrics Critical Care NP",
    "Psych/Mental Health NP",
    "NP, No Subspecialty Noted"
]

# 2. Count NPs per county and specialty
county_specialty_counts = (
    merged
    .groupby(["County_Name", "NP_Type_Grouped"])
    .size()
    .reset_index(name="count")
)

# 3. Pivot to wide format
pivot = (
    county_specialty_counts
    .pivot(index="County_Name", columns="NP_Type_Grouped", values="count")
    .fillna(0)
)

# 4. Ensure all specialties exist
for s in specialties:
    if s not in pivot.columns:
        pivot[s] = 0
pivot = pivot[specialties]

# 5. Add total NP count
pivot["NP Count"] = pivot.sum(axis=1)

# 6. Merge counts into GeoDataFrame
# Assume np_address is a GeoDataFrame with geometry column
# Keep only unique geometry per county
county_geometry = merged[["County_Name", "geometry"]].drop_duplicates(subset="County_Name")

# Merge without changing the geometry
final = county_geometry.merge(pivot, left_on="County_Name", right_index=True, how="left")

# Fill missing NP counts with 0
final[specialties + ["NP Count"]] = final[specialties + ["NP Count"]].fillna(0)

# 7. Rename for final CSV
final = final.rename(columns={"County_Name": "County", "geometry": "Shape"})


# In[13]:


final


# In[14]:


final['County'].nunique()


# In[15]:


#make all int
# List of NP count columns
np_count_cols = [
    "Acute Care NP",
    "Adult/Gero NP",
    "Community/Occupational/School NP",
    "Critical Care NP",
    "Family/Primary Care NP",
    "Neonatal NP",
    "Neonatal Critical Care NP",
    "OBGYN/Womens Health NP",
    "Pediatrics NP",
    "Pediatrics Critical Care NP",
    "Psych/Mental Health NP",
    "NP, No Subspecialty Noted",
    "NP Count"
]

# Fill NaNs with 0 and convert to int
final[np_count_cols] = final[np_count_cols].fillna(0).astype(int)

final = final[['County',
               'Shape',
               'NP Count',
                'Acute Care NP',
                'Adult/Gero NP',
                'Community/Occupational/School NP',
                'Critical Care NP',
                'Family/Primary Care NP',
                'Neonatal NP',
                'Neonatal Critical Care NP',
                'OBGYN/Womens Health NP',
                'Pediatrics NP',
                'Pediatrics Critical Care NP',
                'Psych/Mental Health NP',
                'NP, No Subspecialty Noted'
              ]]
final


# In[16]:


missing_counties = pd.DataFrame({
    "County": ["13263", "13265"],
    "County_Name": ["Talbot", "Taliaferro"]
})

georgia_agg = georgia.dissolve(by='County', as_index=False)

# 4. Replace FIPS codes with county names for only the missing counties
georgia_agg = georgia_agg.merge(missing_counties, on='County', how='left')
georgia_agg['County'] = georgia_agg['County_Name'].combine_first(georgia_agg['County'])
georgia_agg = georgia_agg.drop(columns=['County_Name'])

# 5. Get shapes only for the missing counties
missing_shapes = georgia_agg[georgia_agg['County'].isin(missing_counties['County_Name'])][['County', 'geometry']]
missing_shapes = missing_shapes.rename(columns={'geometry': 'Shape'})

# 6. Add NP count columns with zeros for only missing counties
np_count_cols = [
    'NP Count',
    'Acute Care NP',
    'Adult/Gero NP',
    'Community/Occupational/School NP',
    'Critical Care NP',
    'Family/Primary Care NP',
    'Neonatal NP',
    'Neonatal Critical Care NP',
    'OBGYN/Womens Health NP',
    'Pediatrics NP',
    'Pediatrics Critical Care NP',
    'Psych/Mental Health NP',
    'NP, No Subspecialty Noted'
]

for col in np_count_cols:
    missing_shapes[col] = 0

# 7. Reorder columns to match final
missing_shapes = missing_shapes[['County', 'Shape'] + np_count_cols]

# 8. Append only the missing counties to final
final_df = pd.concat([final, missing_shapes], ignore_index=True)

# 9. Optional: sort by county
final_df = final_df.sort_values('County').reset_index(drop=True)

final_df


# In[17]:


# Remove any rows where County is NaN
final_df = final_df[final_df['County'].notna()].reset_index(drop=True)
final_df


# In[18]:


#merge population counts
georgia_pop = pd.read_csv("~/Downloads/aidatalab/georgia_pop.csv")
georgia_pop


# In[19]:


fips = pd.read_csv("~/Downloads/aidatalab/GA_FIPS.csv")
fips['FIPS Code'] = fips['FIPS Code'].astype(str)
fips


# In[20]:


fips_map = fips.set_index('FIPS Code')['County Name'].to_dict()
georgia_pop['fips'] = georgia_pop['fips'].astype(str).str.zfill(5)
fips['FIPS Code'] = fips['FIPS Code'].astype(str).str.zfill(5)
georgia_pop['County'] = georgia_pop['fips'].map(fips_map)
georgia_pop


# In[21]:


final_df = final_df.merge(
    georgia_pop[['County', 'pop2025']], 
    left_on='County', 
    right_on='County', 
    how='left'
)
final_df


# In[22]:


#new col for density calculation
final_df['NP Density Per 10,000 Residents'] = (final_df['NP Count'] / final_df['pop2025']) * 10000
final_df


# In[23]:


#individual specialty densities
final_df['Acute NP Density Per 10,000 Residents'] = (final_df['Acute Care NP'] / final_df['pop2025']) * 10000
final_df['Adult/Gero NP Density Per 10,000 Residents'] = (final_df['Adult/Gero NP'] / final_df['pop2025']) * 10000
final_df['Community/Occupational/School NP Density Per 10,000 Residents'] = (final_df['Community/Occupational/School NP'] / final_df['pop2025']) * 10000
final_df['Critical Care NP Density Per 10,000 Residents'] = (final_df['Critical Care NP'] / final_df['pop2025']) * 10000
final_df['Family/Primary Care NP Density Per 10,000 Residents'] = (final_df['Family/Primary Care NP'] / final_df['pop2025']) * 10000
final_df['Neonatal NP Density Per 10,000 Residents'] = (final_df['Neonatal NP'] / final_df['pop2025']) * 10000
final_df['Neonatal Critical Care NP Density Per 10,000 Residents'] = (final_df['Neonatal Critical Care NP'] / final_df['pop2025']) * 10000
final_df['OBGYN/Womens Health NP Density Per 10,000 Residents'] = (final_df['OBGYN/Womens Health NP'] / final_df['pop2025']) * 10000
final_df['Pediatrics NP Density Per 10,000 Residents'] = (final_df['Pediatrics NP'] / final_df['pop2025']) * 10000
final_df['Pediatrics Critical Care NP Density Per 10,000 Residents'] = (final_df['Pediatrics Critical Care NP'] / final_df['pop2025']) * 10000
final_df['Psych/Mental Health NP Density Per 10,000 Residents'] = (final_df['Psych/Mental Health NP'] / final_df['pop2025']) * 10000


# In[24]:


final_df = final_df.rename(columns={'pop2025': 'Population'})

count_cols = [
    'Population',
    'NP Count',
    'Acute Care NP',
    'Adult/Gero NP',
    'Community/Occupational/School NP',
    'Critical Care NP',
    'Family/Primary Care NP',
    'Neonatal NP',
    'Neonatal Critical Care NP',
    'OBGYN/Womens Health NP',
    'Pediatrics NP',
    'Pediatrics Critical Care NP',
    'Psych/Mental Health NP',
    'NP, No Subspecialty Noted'
]

final_df[count_cols] = final_df[count_cols].astype(int)

final_df = final_df[['County',
                     'Shape',
                     'Population',

                     'NP Density Per 10,000 Residents',
                     'NP Count',

                     'Acute NP Density Per 10,000 Residents',
                     'Adult/Gero NP Density Per 10,000 Residents',
                     'Community/Occupational/School NP Density Per 10,000 Residents',
                     'Critical Care NP Density Per 10,000 Residents',
                     'Family/Primary Care NP Density Per 10,000 Residents',
                     'Neonatal NP Density Per 10,000 Residents',
                     'Neonatal Critical Care NP Density Per 10,000 Residents',
                     'OBGYN/Womens Health NP Density Per 10,000 Residents',
                     'Pediatrics NP Density Per 10,000 Residents',
                     'Pediatrics Critical Care NP Density Per 10,000 Residents',
                     'Psych/Mental Health NP Density Per 10,000 Residents',

                     'Acute Care NP',
                     'Adult/Gero NP',
                     'Community/Occupational/School NP',
                     'Critical Care NP',
                     'Family/Primary Care NP',
                     'Neonatal NP',
                     'Neonatal Critical Care NP',
                     'OBGYN/Womens Health NP',
                     'Pediatrics NP',
                     'Pediatrics Critical Care NP',
                     'Psych/Mental Health NP',
                     'NP, No Subspecialty Noted'
              ]]
final_df


# In[25]:


final_df.to_csv('final_df.csv', index=False)


# In[ ]:





# ## secondary data ! 

# In[63]:


FINAL_DF = pd.read_csv("~/Downloads/aidatalab/FINAL_DF.csv")
FINAL_DF


# In[64]:


medicaid = pd.read_csv("~/Downloads/aidatalab/GA_Medicaid_Coverage.csv")
medicaid


# In[65]:


medicaid['County'] = medicaid['County Name'].str.replace(' County', '', regex=False)
medicaid


# In[66]:


mapping = medicaid.set_index('County')['Total Medicaid Coverage Rate']
FINAL_DF['Total Medicaid Coverage Rate'] = FINAL_DF['County'].map(mapping)
FINAL_DF


# In[69]:


HPSA = pd.read_csv("~/Downloads/aidatalab/GA_HPSA.csv")
HPSA['County'] = HPSA['County Name'].str.replace(' County', '', regex=False)
HPSA


# In[70]:


mapping2 = HPSA.set_index('County')['Population HPSA']
FINAL_DF['Population HPSA Status'] = FINAL_DF['County'].map(mapping2)
FINAL_DF


# In[79]:


FINAL_DF["Population HPSA Status"] = FINAL_DF["Population HPSA Status"].astype(int)
FINAL_DF["Total Medicaid Coverage Rate"] = (
    FINAL_DF["Total Medicaid Coverage Rate"]
    .str.replace("%", "", regex=False)   # remove %
    .astype(float)                       # convert to float
)


# ## geojson visualization

# In[80]:


FINAL_DF["Shape"].apply(lambda x: type(x)).value_counts()


# In[ ]:


from shapely import wkt
FINAL_DF["Shape"] = FINAL_DF["Shape"].apply(wkt.loads)


# In[82]:


FINAL_DF


# In[83]:


import geopandas as gpd
from shapely.geometry import mapping

geo_county = FINAL_DF.copy()
geo_county["geometry"] = geo_county["Shape"]  # shapely polygons already
gdf = gpd.GeoDataFrame(geo_county, geometry="geometry", crs="EPSG:4326")
gdf = gdf.drop(columns=["Shape"])
gdf.to_file("secondary_georgia_counties.geojson", driver="GeoJSON")


# In[ ]:





# ## (old plotly) visualization

# In[29]:


geo_county = final_df.copy()


# In[30]:


type(geo_county.loc[0, "Shape"])


# In[31]:


from shapely.geometry import mapping
geo_county["Shape"] = final_df["Shape"].apply(mapping)
geo_county


# In[32]:


type(geo_county.loc[0, "Shape"])


# In[ ]:





# In[28]:


#14467-14456 = 11
#lost 11 from them being in different states LOL
geo_county["NP Count"].sum()


# In[29]:


#convert to geo_json
import json

geojson = {
    "type": "FeatureCollection",
    "features": []
}

for _, row in geo_county.iterrows():
    feature = {
        "type": "Feature",
        "geometry": row["Shape"],  # GeoJSON dict
        "properties": {
            "County": row["County"],
            "NP Density": row["NP Density Per 10,000 Residents"],
            "NP Count": row["NP Count"],
            "Acute Care NP": row["Acute Care NP"],
            "Adult/Gero NP": row["Adult/Gero NP"],
            "Community/Occupational/School NP": row["Community/Occupational/School NP"],
            "Critical Care NP": row["Critical Care NP"],
            "Family/Primary Care NP": row["Family/Primary Care NP"],
            "Neonatal NP": row["Neonatal NP"],
            "Neonatal Critical Care NP": row["Neonatal Critical Care NP"],
            "OBGYN/Womens Health NP": row["OBGYN/Womens Health NP"],
            "Pediatrics NP": row["Pediatrics NP"],
            "Pediatrics Critical Care NP": row["Pediatrics Critical Care NP"],
            "Psych/Mental Health NP": row["Psych/Mental Health NP"],
            "NP No Subspecialty Noted": row["NP, No Subspecialty Noted"]
        }
    }
    geojson["features"].append(feature)


# In[30]:


import dash
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import json
import pandas as pd


# In[31]:


app = Dash(__name__)

# List of columns users can toggle
layer_options = [
    "NP Density Per 10,000 Residents",
    "NP Count",
    "Acute Care NP",
    "Adult/Gero NP",
    "Community/Occupational/School NP",
    "Critical Care NP",
    "Family/Primary Care NP",
    "Neonatal NP",
    "Neonatal Critical Care NP",
    "OBGYN/Womens Health NP",
    "Pediatrics NP",
    "Pediatrics Critical Care NP",
    "Psych/Mental Health NP",
    "NP, No Subspecialty Noted"
]

app.layout = html.Div([
    html.H2("Georgia Nurse Practitioner Workforce"),
    dcc.Dropdown(
        id="layer-dropdown",
        options=[{"label": col, "value": col} for col in layer_options],
        value="NP Density",
        clearable=False
    ),
    dcc.Graph(id="map")
])


# In[32]:


@app.callback(
    Output("map", "figure"),
    Input("layer-dropdown", "value")
)
def update_map(selected_layer):
    fig = px.choropleth(
        geo_county,
        geojson=geojson,
        locations="County",
        featureidkey="properties.County",
        color=selected_layer,
        hover_data=layer_options,   # show all NP stats on hover
        projection="mercator"       # use Mercator projection for zoom/pan
    )

    # Fit map bounds to the county geometries
    fig.update_geos(fitbounds="locations", visible=False)

    # Remove extra margins
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig


# In[33]:


if __name__ == "__main__":
    app.run(debug=True, port=8051)  # <-- no 'mode' argument


# In[47]:





# In[ ]:




