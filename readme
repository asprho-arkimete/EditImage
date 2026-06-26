
Markdown# 🎨 APPSP — Applicazione Per Produzione di Sequenze Personalizzate

> **Editing creativo avanzato con AI generativa — Flux 2 · LTX-2 · LoRA**

APPSP è un'applicazione di editing visivo potenziata dall'intelligenza artificiale, progettata per creare sequenze di immagini e video personalizzati con preset artistici esclusivi. Sfrutta modelli di diffusione all'avanguardia per generare contenuti visivi di alta qualità: dall'editing sensuale al romanticismo cosmico, dalle pose atletiche alle trasformazioni VFX.

---

## ✨ Funzionalità

| Feature | Descrizione |
|---|---|
| 🖼️ **Image Editing AI** | Editing avanzato con preset **Hard-tistici** e prompt preimpostati |
| 💫 **Stili creativi** | Sensuale, romanticismo cosmico, pose atletiche & acrobatiche |
| 🎬 **Cortometraggi** | Azione, fantasy, drammatico, transformer design |
| 🔄 **Trasmutazioni & VFX** | Effetti visivi, morphing, transfer pose |
| 🎥 **Animazioni video** | Generazione video con **LTX-2 quantizzato** |
| 🔊 **Rendering con audio** | Output video completo con traccia audio |
| ✏️ **Tavoletta grafica** | Supporto **penna grafica** per disegno e controllo |
| 🔁 **Conversione formati** | **HEIC → JPG**, cambio sfondo, conversione LoRA |

---

## 🧠 Modelli AI Utilizzati

* **[Flux 2 Klein 9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B)** — Generazione e editing immagini (con LoRA personalizzate).
* **[LTX-2](https://huggingface.co/Lightricks/LTX-2)** — Generazione video quantizzato.
* **LoRA personalizzate** — Preset stilistici esclusivi per ogni mood creativo.

---

## 🖥️ Requisiti di Sistema

* **OS:** Windows 10 / 11 (64-bit)
* **GPU:** **NVIDIA** con almeno **12GB VRAM** (consigliati **16GB+**)
* **CUDA:** **12.6+**
* **RAM:** **32GB** consigliati
* **Spazio su Disco:** **~150GB minimo** per i modelli + spazio per i file di output

---

## ⚙️ Installazione

### 1. Installa i prerequisiti

| Software | Link di Download |
|---|---|
| **Python 3.10** | [Download Python 3.10](https://www.python.org/downloads/release/python-3100/) |
| **Anaconda** | [Download Anaconda](https://www.anaconda.com/download) |
| **Cursor IDE** | [Download Cursor](https://cursor.com/download) |

> ⚠️ **IMPORTANTE:** Durante l'installazione di Python, spunta tassativamente la voce **"Add Python to PATH"**.

---

### 2. Clona il repository

Apri il **terminale Anaconda** e digita:

```bash
git clone [https://github.com/asprho-arkimete/EditImage.git](https://github.com/asprho-arkimete/EditImage.git)
cd EditImage
3. Crea e attiva l'ambiente virtualeBashpython -m venv vmix
vmix\Scripts\activate
💡 Il prompt del terminale diventerà (vmix), a indicare che sei dentro l'ambiente isolato.4. Installa PyTorch con supporto CUDA 12.6Bashpip install torch torchvision --index-url [https://download.pytorch.org/whl/cu126](https://download.pytorch.org/whl/cu126)
5. Installa le dipendenze del progettoBashpip install -r requirements.txt
6. Scarica i modelli pesanti📦 NOTA SULLO SPAZIO: I modelli di base non sono inclusi nel repository a causa delle loro dimensioni elevate.Flux 2 Kevin 9B: ~46 GBLTX-2: ~90 GBSpazio Totale Modelli: ~136 GBScarica i pacchetti aggiuntivi dai seguenti link (estratti da file .rar):📁 MegaLora/ — LoRA per Flux 2 (~10 GB) ➔ Hugging Face Repository📁 modelLTX2/ — Modello LTX-2 ottimizzato (~5 GB) ➔ Hugging Face RepositoryDopo averli estratti, assicurati che la struttura delle cartelle corrisponda esattamente a questa:PlaintextEditImage/
├── Lora/           ← Cartella LoRA estratta 
├── modelLTX2/      ← Modello LTX-2 estratto
├── mix.py
├── conv.py
├── bg.py
├── forma.py
├── design.py
├── ltx2.py
├── requirements.txt
└── README.md
🚀 Avvio dell'ApplicazionePer lanciare l'interfaccia principale, esegui nel terminale attivato:Bashpython mix.py
📁 Script e Strumenti DisponibiliFileFunzione Principalemix.pyApp Principale — Interfaccia per l'editing immagini con Flux 2 e preset LoRAconv.pyUtility di conversione di massa HEIC → JPGbg.pyStrumento di rimozione e cambio sfondo automaticoforma.pyScript di conversione formato LoRA (in caso di file non leggibili)design.pyModulo per disegno con tavoletta grafica e gestione tavolozza coloriltx2.pyGeneratore autonomo di video con modello LTX-2🔗 Link ai Modelli OriginaliFlux 2 Klein 9B: Black Forest Labs on Hugging FaceDiffusers Flux API: Hugging Face DocumentationLTX-2: Lightricks on Hugging Face📝 Note Tecniche ImportantiGestione VRAM: Se la scheda video ha meno di 12GB di VRAM, il sistema passerà automaticamente in modalità CPU (il processo di generazione risulterà significativamente più lento).Quantizzazione: I modelli inclusi sono quantizzati per ridurre l'impatto sulla memoria mantenendo intatta la qualità visiva.Periferiche esterne: In caso di mancato input della tavoletta grafica, verifica che i driver (Wacom / XP-Pen / Huion) siano aggiornati all'ultima versione.📄 LicenzaUso personale e creativo. I modelli AI terzi utilizzati all'interno del software rimangono soggetti alle rispettive licenze d'uso ufficiali consultabili su Hugging Face.
