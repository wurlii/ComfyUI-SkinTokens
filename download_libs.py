import os
import urllib.request

urls = [
    ("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js", "three.min.js"),
    ("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js", "GLTFLoader.js"),
    ("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js", "OBJLoader.js"),
    ("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/MTLLoader.js", "MTLLoader.js"),
    ("https://cdn.jsdelivr.net/npm/fflate@0.8.0/umd/index.js", "fflate.js"),
    ("https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/loaders/FBXLoader.js", "FBXLoader.js"),
    ("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/TGALoader.js", "TGALoader.js")
]

base_dir = r"C:\Users\Renew\Downloads\ComfyUI-Easy-Install\ComfyUI-Easy-Install\ComfyUI\custom_nodes\ComfyUI-SkinTokens\web\js\libs"
os.makedirs(base_dir, exist_ok=True)

for url, filename in urls:
    filepath = os.path.join(base_dir, filename)
    print(f"Downloading {url} to {filepath}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
print("All downloads complete.")
