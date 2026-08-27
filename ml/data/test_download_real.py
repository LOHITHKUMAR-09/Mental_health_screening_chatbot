import urllib.request
import zipfile
import os
import pandas as pd

url = "https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip"
zip_path = r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\ml\data\dass_raw.zip"
extract_dir = r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\ml\data\raw"

print(f"Downloading real dataset from {url} ...")
try:
    urllib.request.urlretrieve(url, zip_path)
    print("Download successful! Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"Extracted to {extract_dir}")
    
    # Check extracted files
    files = os.listdir(extract_dir)
    print("Extracted files:", files)
    
    csv_file = [f for f in files if f.endswith('.csv') or 'data' in f.lower()][0]
    full_csv_path = os.path.join(extract_dir, csv_file)
    print(f"Loading {full_csv_path} ...")
    
    # Try reading tab or comma
    try:
        df = pd.read_csv(full_csv_path, sep='\t')
    except Exception:
        df = pd.read_csv(full_csv_path)
        
    print(f"Dataset Shape: {df.shape}")
    print("Columns sample:", list(df.columns[:25]))
    print("Total rows (real human participants):", len(df))
except Exception as e:
    print(f"Error: {e}")
