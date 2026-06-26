from safetensors.torch import load_file, save_file
import torch
import os
from tqdm import tqdm

# ── Seleziona device ──────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️  Device: {device}" + (f"  ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))

def lokr_to_lora(path_input, path_output):
    print(f"\n🔧 Conversione LoKr→LoRA: {path_input} → {path_output}")
    state = load_file(path_input)

    # Raggruppa per layer
    layers = {}
    for key in tqdm(state, desc='raggruppa per livelli'):
        if key.endswith('.lokr_w1'):
            base = key[:-len('.lokr_w1')]
            layers.setdefault(base, {})['w1'] = state[key]
        elif key.endswith('.lokr_w2'):
            base = key[:-len('.lokr_w2')]
            layers.setdefault(base, {})['w2'] = state[key]
        elif key.endswith('.alpha'):
            base = key[:-len('.alpha')]
            layers.setdefault(base, {})['alpha'] = state[key]

    converted = {}
    for base, parts in tqdm(layers.items(), desc='conversione'):
        # Carica su GPU in float32
        w1 = parts['w1'].to(device=device, dtype=torch.float32)
        w2 = parts['w2'].to(device=device, dtype=torch.float32)

        # Prodotto di Kronecker → matrice piena
        full = torch.kron(w1, w2)

        # SVD troncata a rank 32
        U, S, Vh = torch.linalg.svd(full, full_matrices=False)
        rank = min(32, S.shape[0])
        U  = U[:, :rank]
        S  = S[:rank]
        Vh = Vh[:rank, :]

        # Riporta su CPU in float16 per salvare
        lora_B = (U  * S.sqrt()          ).to(device="cpu", dtype=torch.float16).contiguous()
        lora_A = (Vh * S.sqrt().unsqueeze(1)).to(device="cpu", dtype=torch.float16).contiguous()

        converted[base + '.lora_A.weight'] = lora_A
        converted[base + '.lora_B.weight'] = lora_B

    save_file(converted, path_output)
    print(f"✅ Salvata: {path_output}  ({len(converted)//2} layer convertiti)")


def verifica_compatibilita(path_riferimento, path_convertita, label):
    ref  = load_file(path_riferimento)
    conv = load_file(path_convertita)

    print(f"\n{'='*60}")
    print(f"🔍 Verifica: {label}")
    print(f"{'='*60}")

    errori = 0
    for key in tqdm(sorted(ref.keys()), desc='verifica'):
        s_ref  = tuple(ref[key].shape)
        s_conv = tuple(conv[key].shape) if key in conv else None
        if s_conv is None:
            print(f"  ❌ Mancante: {key}")
            errori += 1
        elif s_ref != s_conv:
            print(f"  ❌ {key}: ref{s_ref} vs conv{s_conv}")
            errori += 1

    if errori == 0:
        print("  ✅ PERFETTAMENTE COMPATIBILE!")
    else:
        print(f"  ⚠️ {errori} errori di shape")


# ── Converti ──────────────────────────────────────────────────────────────────
path_input  = "./lora/klein_snofs_v1_4.safetensors"
path_output = "./lora/klein_snofs_v1_4_converted.safetensors"

lokr_to_lora(path_input, path_output)

# ── Verifica ──────────────────────────────────────────────────────────────────
verifica_compatibilita(
    "./lora/FK_missionary.safetensors",
    path_output,
    os.path.basename(path_input).split('.')[0]
)