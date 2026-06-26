import os
import shutil
from PIL import Image
from pillow_heif import register_heif_opener
from tqdm import tqdm

register_heif_opener()

path = "./nicole"
k = 1

os.makedirs("heic", exist_ok=True)

fotos = os.listdir(path)
for foto in tqdm(fotos):
    full_path = os.path.join(path, foto)

    if foto.lower().endswith('.heic'):
        img = Image.open(full_path)
        img.save(os.path.join(path, f"n{k}.jpg"))
        shutil.move(full_path, os.path.join("heic", foto))
        k += 1

    elif foto.lower().endswith('.jpg') and not foto.startswith('n'):
        dst = os.path.join(path, f"n{k}.jpg")
        os.rename(full_path, dst)  # rinomina invece di copiare
        k += 1