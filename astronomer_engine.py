import matplotlib.pyplot as plt
from astroquery.simbad import Simbad
from astroquery.gaia import Gaia
import astropy.units as u
from astropy.coordinates import SkyCoord
import pandas as pd

def get_stellar_data(object_name):
    """
    Fetches real Gaia satellite data by resolving an object name via SIMBAD.
    Fixes the 'RA' KeyError by checking for both 'RA' and 'ra'.
    """
    try:
        # 1. Resolve the name to coordinates
        result_table = Simbad.query_object(object_name)
        if result_table is None:
            return None, f"Object '{object_name}' not found in SIMBAD database."
        
        # --- FIX FOR 'RA' ERROR ---
        # Get all column names from the table
        cols = result_table.colnames
        
        # Find the column that matches 'RA' regardless of case
        ra_col = next((c for c in cols if c.upper() == 'RA'), None)
        dec_col = next((c for c in cols if c.upper() == 'DEC'), None)

        if not ra_col or not dec_col:
            return None, "Error: Could not find RA/Dec columns in SIMBAD response."

        # Use the found column names to get the data
        ra_val = result_table[ra_col][0]
        dec_val = result_table[dec_col][0]
        # ---------------------------

        # Create coordinate object
        coord = SkyCoord(ra_val, dec_val, unit=(u.hourangle, u.deg))

        # 2. Query Gaia (Top 500 stars within 0.3 degrees)
        query = f"""
        SELECT TOP 500 ra, dec, phot_g_mean_mag 
        FROM gaiadr3.gaia_source 
        WHERE CONTAINS(POINT('ICRS', ra, dec), 
                       CIRCLE('ICRS', {coord.ra.deg}, {coord.dec.deg}, 0.3)) = 1 
        ORDER BY phot_g_mean_mag ASC
        """
        job = Gaia.launch_job(query)
        results = job.get_results()
        
        # Convert to Pandas and drop rows with missing brightness data
        df = results.to_pandas().dropna(subset=['phot_g_mean_mag'])
        
        return df, coord
        
    except Exception as e:
        return None, f"System Error: {str(e)}"

def create_star_plot(df, title):
    """Generates a dark-themed matplotlib figure from the dataframe."""
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('#0E1117') # Match Streamlit dark background
    ax.set_facecolor('black')
    
    # Scale: Brighter stars (lower magnitude) get larger sizes
    sizes = (22 - df['phot_g_mean_mag']) ** 1.8
    
    scatter = ax.scatter(
        df['ra'], 
        df['dec'], 
        c=df['phot_g_mean_mag'], 
        cmap='magma', 
        s=sizes, 
        alpha=0.8,
        edgecolors='none'
    )
    
    cb = plt.colorbar(scatter)
    cb.set_label('Brightness (Magnitude)', color='white')
    cb.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cb.ax.axes, 'yticklabels'), color='white')

    ax.set_xlabel('Right Ascension (deg)', color='white')
    ax.set_ylabel('Declination (deg)', color='white')
    ax.set_title(f"Star Distribution: {title}", color='white', fontsize=14)
    
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.invert_xaxis() # Sky coordinates are visually inverted
    
    return fig