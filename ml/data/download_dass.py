import requests
import zipfile
import os
import io

url = "https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip"
extract_dir = r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\ml\data\raw"

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
print(f"Connecting to {url} ...")
res = requests.get(url, headers=headers, timeout=60)
print(f"Status: {res.status_code}, Bytes: {len(res.content)}")

if res.status_code == 200:
    print("Unzipping content in memory...")
    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
        z.extractall(extract_dir)
    print("Files in raw directory:", os.listdir(extract_dir))
