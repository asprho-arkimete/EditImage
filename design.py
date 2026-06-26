import tkinter as tk
import time
from tkinter import colorchooser, filedialog, HORIZONTAL, ttk
from PIL import Image, ImageTk, ImageGrab
from numpy import insert
import tkinterdnd2
import os

# ── stato globale ──────────────────────────────────────────────
modo = 'nessuno'
last_x, last_y = None, None
last_time = None
img_tk = None
file = ''
file_save = './out_image/design.jpg'
background_frame = 'red'
color_pennelo = 'pink'

# ── finestra ───────────────────────────────────────────────────
window = tkinterdnd2.Tk()
window.title("Design")
window.state('zoomed')
window.config(background='gray')

# frame_main contiene tutto — canvas + pannello destra
frame_main = tk.Frame(window, bg='gray')
frame_main.pack(side='top', anchor='nw')

# ── frame canvas (colonna 0 di frame_main) ────────────────────
framecanvas = tk.Frame(frame_main, bg='gray')
framecanvas.grid(row=0, column=0, sticky='nw')

canvas = tk.Canvas(framecanvas, width=900, height=900, bg=background_frame)
canvas.grid(row=0, column=0)

# frame steps/lora — sotto la canvas
frame_t = tk.Frame(frame_main, bg='gray')
frame_t.grid(row=1, column=0, sticky='w')

ls = tk.Label(frame_t, text='steps: 8', bg='gray', fg='white')
ls.grid(row=0, column=0, padx=5, pady=2)

def up_ls(val):
    ls.config(text=f'steps: {val}')

steps = tk.Scale(frame_t, from_=1, to=50, orient=HORIZONTAL, command=up_ls, bg='gray', fg='white')
steps.set(8)
steps.grid(row=0, column=1, pady=2)

l_lora = tk.Label(frame_t, text='Lora:', bg='gray', fg='white')
l_lora.grid(row=0, column=2, padx=5, pady=2)

combo_lora = ttk.Combobox(frame_t, width=20)
combo_lora.grid(row=0, column=3, padx=5, pady=2)

def loadlora(event=None):
    models = ['nolora'] + [os.path.basename(m) for m in os.listdir('./lora')]
    combo_lora['values'] = models

def select(event=None):
    t = text.get('1.0', tk.END).strip()
    text.delete('1.0', tk.END)                        # sintassi corretta per Text
    text.insert('1.0', combo_lora.get().split('.')[0] + ', ' + t)  # sintassi corretta per Text

combo_lora.bind('<ButtonPress-1>', loadlora)   # ricarica lora quando si apre il menu
combo_lora.bind('<<ComboboxSelected>>', select)  # era <<Comboselect>> — inesistente
loadlora()

# ── pannello bottoni (colonna 1 di frame_main) ────────────────
frame_button = tk.Frame(frame_main, bg='gray')
frame_button.grid(row=0, column=1, sticky='n', padx=5, pady=5)
frame_button.columnconfigure(0, weight=0)
frame_button.columnconfigure(1, weight=0)

# ── funzioni ───────────────────────────────────────────────────
def cambiacolore():
    global background_frame
    colore = colorchooser.askcolor(color=background_frame, title="Scegli colore")
    if colore[1] is not None:
        background_frame = colore[1]
        colore_sfondo.config(bg=background_frame)
        canvas.config(bg=background_frame)


def cambiacolore_pennelo():
    global color_pennelo
    colore = colorchooser.askcolor(color=color_pennelo, title="Scegli colore")
    if colore[1] is not None:
        color_pennelo = colore[1]
        colore_pennelo.config(bg=color_pennelo)

def set_modo(nuovo_modo):
    global modo
    modo = nuovo_modo
    attiva_disegno.config(bg='green' if modo == 'disegna' else 'red')
    attiva_gomma.config(bg='green' if modo == 'gomma' else 'red')

# row 0: label Sfondo / Pennello
tk.Label(frame_button, text='Sfondo', bg='gray', fg='white').grid(row=0, column=0, sticky='w')
tk.Label(frame_button, text='Pennello', bg='gray', fg='white').grid(row=0, column=1, sticky='w', padx=(10,0))

# row 1: anteprima colori
colore_sfondo = tk.Canvas(frame_button, width=30, height=30, bg=background_frame, cursor='hand2')
colore_sfondo.grid(row=1, column=0, pady=5, sticky='w')
colore_sfondo.bind('<Button-1>', lambda e: cambiacolore())

colore_pennelo = tk.Canvas(frame_button, width=30, height=30, bg=color_pennelo, cursor='hand2')
colore_pennelo.grid(row=1, column=1, pady=5, sticky='w', padx=(10,0))
colore_pennelo.bind('<Button-1>', lambda e: cambiacolore_pennelo())

# row 2: Disegna
attiva_disegno = tk.Button(frame_button, text='Disegna', command=lambda: set_modo('disegna'), bg='red')
attiva_disegno.grid(row=2, column=0, pady=5, sticky='w')

# row 3: Gomma
attiva_gomma = tk.Button(frame_button, text='Gomma', command=lambda: set_modo('gomma'), bg='red')
attiva_gomma.grid(row=3, column=0, pady=5, sticky='w')

# row 4: label Dimensione / Pressione
tk.Label(frame_button, text='Dimensione', bg='gray', fg='white').grid(row=4, column=0, sticky='w')
tk.Label(frame_button, text='Pressione', bg='gray', fg='white').grid(row=4, column=1, sticky='w', padx=(10,0))

# row 5: slider Dimensione / Pressione
dimensione_pennello = tk.Scale(frame_button, from_=50, to=1, orient='vertical', bg='gray', fg='white')
dimensione_pennello.set(20)
dimensione_pennello.grid(row=5, column=0, pady=5, sticky='w')

sensibilita_pressione = tk.Scale(frame_button, from_=100, to=1, orient='vertical', bg='gray', fg='white')
sensibilita_pressione.set(40)
sensibilita_pressione.grid(row=5, column=1, pady=5, sticky='w', padx=(10,0))

# row 6: Save
def saveimage():
    global file, file_save
    if not file:
        print("Nessuna immagine caricata nel canvas.")
        return
    x = canvas.winfo_rootx()
    y = canvas.winfo_rooty()
    target_w = canvas.winfo_width()
    target_h = canvas.winfo_height()
    img_orig = Image.open(file).convert('RGB')
    w, h = img_orig.size
    scala = min(target_w / w, target_h / h)
    img_w = int(w * scala)
    img_h = int(h * scala)
    offset_x = (target_w - img_w) // 2
    offset_y = (target_h - img_h) // 2
    min_x = x + offset_x
    min_y = y + offset_y
    max_x = min_x + img_w
    max_y = min_y + img_h
    img = ImageGrab.grab(bbox=(min_x, min_y, max_x, max_y)).convert('RGB')
    os.makedirs('./out_image', exist_ok=True)
    img.save(file_save, quality=100)
    print(f"Salvato: {file_save}")

def scegli_percorso():
    global file_save
    percorso = filedialog.asksaveasfilename(
        defaultextension='.jpg',
        filetypes=[('JPEG', '*.jpg'), ('PNG', '*.png'), ('Tutti i file', '*.*')]
    )
    if percorso:
        file_save = percorso
        saveimage()

button_save = tk.Button(frame_button, text='Save', command=saveimage)
button_save.grid(row=6, column=0, pady=5, sticky='w')

# row 7: Save As
button_saveAs = tk.Button(frame_button, text='Save As', command=scegli_percorso)
button_saveAs.grid(row=7, column=0, pady=5, sticky='w')


from diffusers import Flux2KleinPipeline
from deep_translator import GoogleTranslator as G
from optimum.quanto import freeze, qfloat8, quantize
import torch

def Flux2():
    global text, combo_lora, steps, file_save
    print("Avvio generazione FLUX.2 klein...")
    device = "cuda"
    dtype = torch.bfloat16

    pipe = Flux2KleinPipeline.from_pretrained("black-forest-labs/FLUX.2-klein-9B", torch_dtype=dtype)

    # lora — solo se non è 'nolora'
    lora_sel = combo_lora.get()  # era combo_lora senza .get()
    if lora_sel and lora_sel != 'nolora':
        pipe.load_lora_weights(f"./lora/{lora_sel}", adapter_name='lora1')
        pipe.set_adapters('lora1', adapter_weights=0.8)

    # quantizzazione
    print("Quantizzazione transformer...")
    quantize(pipe.transformer, weights=qfloat8)
    freeze(pipe.transformer)

    if hasattr(pipe, "text_encoder") and pipe.text_encoder is not None:
        print("Quantizzazione text encoder...")
        quantize(pipe.text_encoder, weights=qfloat8)
        freeze(pipe.text_encoder)

    # ottimizzazioni memoria
    pipe.enable_model_cpu_offload()  # rimosso il duplicato
    pipe.vae.enable_slicing()

    # traduzione prompt
    prompt_eng = G(source='it', target='en').translate(text.get('1.0', tk.END).strip())
    print(f"Prompt: {prompt_eng}")

    # immagine di riferimento dal file salvato
    img = Image.open(file_save).convert('RGB')
    w, h = img.size
    target = 512
    if w >= h:
        h = (target * h) // w
        w = target
    else:
        w = (target * w) // h
        h = target
    img = img.resize((w, h), Image.BICUBIC)

    image = pipe(
        prompt=prompt_eng,
        image=img,
        height=1024,
        width=1024,
        guidance_scale=1.0,
        num_inference_steps=steps.get(),  # era hardcoded 8
        generator=torch.Generator(device=device).manual_seed(0)
    ).images[0]

    # salvataggio con nome progressivo
    path_out = "out_image/realist_disegn.jpg"
    if os.path.exists(path_out):
        k = 1
        while os.path.exists(f"out_image/realist_disegn{k}.jpg"):
            k += 1
        path_out = f"out_image/realist_disegn{k}.jpg"

    os.makedirs('out_image', exist_ok=True)
    image.save(path_out)
    print(f"Salvato: {path_out}")

Gen_flux2 = tk.Button(frame_button, text='Genera FLUX.2', command=Flux2)
Gen_flux2.grid(row=8, column=0, pady=5, sticky='w')

# row 9: textarea prompt
text = tk.Text(frame_button, width=90, height=15)
text.grid(row=9, column=0, columnspan=2, pady=2, sticky='w')
prompt_define = """trasforma lo schizzo del disegno rosa nel seno nudo naturale.
trasforma lo schizzo arancione nelle areole mammarie del seno nudo.
trasforma lo schizzo marrone sul seno nei capezzoli del seno.
trasforma lo schizzo rosa in basso nel pube con grandi labbra della vagina semi dilatate.
trasforma lo schizzo nero in una striscia di peli del pube.
trasforma lo schizzo marrone in basso nelle piccole labbra della vagina semi dilatate.

La ragazza dell'immagine 1 è totalmente nuda, posa in piedi, seno naturale, capezzoli,
pube con striscia di peli curati, dettagli genitali femminili realistici: (grandi labbra della vagina semi dilatate, piccole labbra della vagina semi dilatate, clitoride)

rimuovi tutti gli schizzi del disegno dalla fotografia.
Mantieni massima coerenza del soggetto nell'immagine 1: viso, capigliatura, occhi."""

text.insert("1.0", prompt_define)

# ── disegno ────────────────────────────────────────────────────
def disegna(event):
    global last_x, last_y, last_time
    if modo == 'nessuno':
        return
    now = time.time()
    x, y = event.x, event.y
    dim = dimensione_pennello.get()
    pressione = sensibilita_pressione.get()
    if last_x is not None and last_time is not None:
        if modo == 'disegna':
            dt = now - last_time
            dist = ((x - last_x)**2 + (y - last_y)**2) ** 0.5
            velocita = dist / (dt + 0.001)
            fattore_pressione = pressione / 50.0
            spessore = max(1, min(dim, int(dim - velocita / (15 * fattore_pressione) + 2)))
            canvas.create_line(last_x, last_y, x, y,
                               fill=color_pennelo,
                               width=spessore,
                               capstyle=tk.ROUND,
                               smooth=True)
        elif modo == 'gomma':
            canvas.create_rectangle(
                x - dim, y - dim, x + dim, y + dim,
                fill=background_frame, outline=background_frame
            )
    last_x, last_y = x, y
    last_time = now

def reset_pos(event):
    global last_x, last_y, last_time
    last_x, last_y, last_time = None, None, None

def applica_image(event):
    global img_tk, file
    file = event.data.strip('{}')
    img = Image.open(file).convert('RGB')
    w, h = img.size
    target_w = canvas.winfo_width()
    target_h = canvas.winfo_height()
    scala = min(target_w / w, target_h / h)
    w = int(w * scala)
    h = int(h * scala)
    img = img.resize((w, h), Image.BICUBIC)
    img_tk = ImageTk.PhotoImage(img)
    canvas.delete('hint')
    canvas.create_image(target_w // 2, target_h // 2, image=img_tk, anchor='center')

canvas.bind('<B1-Motion>', disegna)
canvas.bind('<ButtonRelease-1>', reset_pos)

canvas.drop_target_register('DND_Files')
canvas.dnd_bind('<<Drop>>', applica_image)

canvas.create_rectangle(200, 430, 700, 470, fill='black', outline='', tags='hint')
canvas.create_text(450, 450, text="Trascina qui un'immagine", fill='white',
                   font=('Arial', 16, 'bold'), anchor='center', tags='hint')

window.mainloop()