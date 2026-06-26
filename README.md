# 🎨 APPSP — Applicazione Per Produzione di Sequenze Personalizzate

> **Editing creativo avanzato con AI generativa — Flux 2 · LTX-2 · LoRA**

APPSP è un'applicazione di editing visivo potenziata dall'intelligenza artificiale, progettata per creare sequenze di immagini e video personalizzati con preset artistici esclusivi. Sfrutta modelli di diffusione all'avanguardia per generare contenuti visivi di alta qualità: dall'editing sensuale al romanticismo cosmico, dalle pose atletiche alle trasformazioni VFX.

---

## ✨ Funzionalità

| Feature | Descrizione |
|---|---|
| 🖼️ **Image Editing AI** | Editing avanzato con preset stilistici e prompt preimpostati |
| 💫 **Stili creativi** | Sensuale, romanticismo cosmico, pose atletiche & acrobatiche |
| 🎬 **Cortometraggi** | Azione, fantasy, drammatico, transformer design |
| 🔄 **Trasmutazioni & VFX** | Effetti visivi, morphing, transfer di pose |
| 🎥 **Animazioni video** | Generazione video con LTX-2 quantizzato |
| 🔊 **Rendering con audio** | Output video completo con traccia audio |
| ✏️ **Tavoletta grafica** | Supporto penna grafica per disegno e controllo |
| 🔁 **Conversione formati** | HEIC → JPG, cambio sfondo, conversione LoRA |

---

## 🧠 Modelli AI utilizzati

| Modello | Uso | Link |
|---|---|---|
| **Flux 2 Klein 9B** | Generazione e editing immagini (con LoRA personalizzate) | [Hugging Face](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B) |
| **LTX-2** | Generazione video quantizzato | [Hugging Face](https://huggingface.co/Lightricks/LTX-2) |
| **LoRA personalizzate** | Preset stilistici esclusivi per ogni mood creativo | [Asprho/megalora](https://huggingface.co/Asprho/megalora/tree/main) |

---

## 🖥️ Requisiti di sistema

| Componente | Requisito |
|---|---|
| **OS** | Windows 10/11 (64-bit) |
| **GPU** | NVIDIA con almeno 12 GB VRAM (consigliati 16 GB+) |
| **CUDA** | 12.6+ |
| **RAM** | 32 GB consigliati |
| **Spazio disco** | ~150 GB per i modelli + spazio per gli output |

---

## ⚙️ Installazione

### 1. Prerequisiti

Installa i seguenti software prima di procedere:

| Software | Link |
|---|---|
| Python 3.10 | https://www.python.org/downloads/release/python-3100/ |
| Anaconda | https://www.anaconda.com/download |
| Cursor IDE | https://cursor.com/download |

> ⚠️ Durante l'installazione di Python, spunta **"Add Python to PATH"**

---

### 2. Clona il repository

Apri il terminale Anaconda e digita:

```bash
git clone https://github.com/asprho-arkimete/EditImage.git
cd EditImage
```

---

### 3. Crea e attiva l'ambiente virtuale

```bash
python -m venv vmix
vmix\Scripts\activate
```

> Il prompt diventerà `(vmix)` — sei dentro l'ambiente isolato.

---

### 4. Installa PyTorch con CUDA

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

---

### 5. Installa le dipendenze

```bash
pip install -r requirements.txt
```

---

### 6. Scarica i modelli

> 📦 I modelli **non sono inclusi** nel repository per via delle dimensioni. Scaricali separatamente dai link seguenti.

| Cartella | Contenuto | Dimensione | Link |
|---|---|---|---|
| `Lora/` | LoRA per Flux 2 | ~10 GB | [Asprho/megalora](https://huggingface.co/Asprho/megalora/tree/main) |
| `modelLTX2/` | Modello LTX-2 quantizzato | ~5 GB | [Asprho/megalora](https://huggingface.co/Asprho/megalora/tree/main) |

> Il modello base Flux 2 Klein 9B pesa circa **46 GB**, LTX-2 circa **90 GB** — totale circa **136 GB** solo per i modelli base.

Estrai i file `.rar` e verifica che la struttura del progetto sia la seguente:

```
EditImage/
├── Lora/           ← cartella LoRA estratta
├── modelLTX2/      ← modello LTX-2 estratto
├── mix.py
├── conv.py
├── bg.py
├── forma.py
├── design.py
├── ltx2.py
├── requirements.txt
└── README.md
```

---

## 🚀 Avvio

```bash
python mix.py
```

---

## 📁 Script disponibili

| File | Funzione |
|---|---|
| `mix.py` | **App principale** — editing immagini con Flux 2 e preset LoRA |
| `conv.py` | Converte immagini **HEIC → JPG** |
| `bg.py` | **Cambio sfondo** automatico |
| `forma.py` | Converte LoRA in formato standard (se non leggibile) |
| `design.py` | **Disegno con penna grafica** e tavolozza colori |
| `ltx2.py` | **Generazione video** con LTX-2 |

---

## 📝 Note

- Se la GPU non dispone di abbastanza VRAM, l'app utilizzerà la CPU (molto più lenta).
- I modelli quantizzati riducono il consumo di VRAM mantenendo una buona qualità dell'output.
- Per problemi con la tavoletta grafica, verifica che i driver Wacom/XP-Pen siano aggiornati.

---

## 🔗 Riferimenti modelli

- [Flux 2 Klein 9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B)
- [Diffusers — Flux API](https://huggingface.co/docs/diffusers/api/pipelines/flux)
- [LTX-2](https://huggingface.co/Lightricks/LTX-2)

---

## 📄 Licenza

Uso personale e creativo. I modelli AI utilizzati sono soggetti alle rispettive licenze pubblicate su Hugging Face.

---

<div align="center">
  <b>Buon divertimento! 🎨🚀</b><br>
  <i>Crea, trasforma, anima — senza limiti.</i>
</div>
