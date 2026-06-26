from PIL import Image  # PLI → PIL
import os
from tqdm import tqdm

path = "./pose"

for i in tqdm(os.listdir(path),desc='conversione'):
    if i.endswith(".png"):
        img = Image.open(f"{path}/{i}").convert("RGBA")  # converti in RGBA per gestire la trasparenza
    
        bg = Image.new("RGB", (img.width, img.height), (255, 255, 255))  # "RGB" stringa, size come tupla, colore come tupla
    
        bg.paste(img, (0, 0), img)  # (0,0) come tupla, img come maschera alpha
    
        bg.save(f"{path}/{os.path.splitext(i)[0]}_bg.jpg")  # splitext più sicuro di split('.')