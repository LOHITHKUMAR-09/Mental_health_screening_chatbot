import requests
import zipfile
import os

url = "https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip"
zip_file = r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\ml\data\dass_data.zip"
extract_dir = r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\ml\data\raw"

headers = {"User-Agent": "Mozilla/5.0"}
print(f"Streaming {url} to {zip_file}...")

with requests.get(url, headers=headers, stream=True, timeout=30) as r:
    r.raise_for_status()
    with open(zip_file, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)

print(f"Downloaded! Size: {os.path.getsize(zip_file)} bytes")
print("Extracting...")
with zipfile.ZipFile(zip_file, "r") as z:
    z.extractall(extract_dir)

print("Extraction complete. Files in raw:")
for f in os.listdir(extract_dir):
    print(" -", f)
