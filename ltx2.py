DEFAULT_CLIPS   = 1

def prompts(nome_file):
    global DEFAULT_CLIPS
    nomefile = os.path.basename(nome_file).lower().replace(" ", "")

    print(f"Nome File {nomefile}")

    if "in_piedi" in nomefile:
        promptita = (
            "Due donne si siedono delicatamente su un grande letto matrimoniale, "
            "l'atmosfera è intima e accogliente, luce soffusa, "
            "attenzione ai dettagli nell'espressione dei volti e nella cura dei vestiti."
        )
        nameout      = "in_piedi"
        numero_clips = 1
    elif "sedute" in nomefile:
        promptita = (
            "Due donne si accarezzano teneramente e si baciano sulle labbra, "
            "scena romantica e passionale su un letto, sguardi emozionati e gesti affettuosi, "
            "luce naturale, atmosfera calda e coinvolgente."
        )
        nameout      = "sedute"
        numero_clips = DEFAULT_CLIPS
    elif "close_up_kiss" in nomefile or "closeup_kiss" in nomefile:
        promptita = (
            "Primo piano dei volti e delle labbra di due donne mentre si baciano "
            "appassionatamente alla francese con la lingua, "
            "dettagli realistici ed emozionanti, sfondo sfocato per enfatizzare "
            "l'intensità del bacio, luci morbide e colori caldi."
        )
        nameout      = "close_up_kiss"
        numero_clips = DEFAULT_CLIPS
    elif "kiss" in nomefile:
        promptita = (
            "Due donne si baciano appassionatamente alla francese, scena romantica "
            "ed intensa di passione, ambientazione delicata, "
            "sensazione di intimità e rispetto tra le protagoniste."
        )
        nameout      = "kiss"
        numero_clips = DEFAULT_CLIPS

    elif "gambe_aperte" in nomefile:
        promptita = (
            "una donna tatuata con capelli neri sdraiata sulla schiena, gambe sollevate alte e spalancate in aria in posizione butterfly, "
            "mani che tirano le cosce aperte, primo piano estremo su figa e ano dilatati e aperti, vagina gaping, dettagli espliciti e bagnati, "
            "luce calda da camera da letto, realistico"
        )
        nameout = 'gambeAperte'
        numero_clips = DEFAULT_CLIPS

    elif "dildo_anal_2" in nomefile:
        promptita = (
            "una donna accovacciata o in ginocchio su un letto, "
            "penetrazione anale profonda e intensa con un grosso dildo, "
            "muove ritmicamente il bacino su e giù facendo entrare ed uscire il dildo dall'ano, "
            "ano ben dilatato e aperto durante il movimento, dettagli estremi e realistici, "
            "espressione di piacere intenso, umori brillanti, luce calda da camera da letto"
            "messa a fuoco su dildo nel ano e messa a fuoco sul viso"

        )
        nameout = 'dildo_anal'
        numero_clips = DEFAULT_CLIPS
    else:
        promptita    = "Scena non riconosciuta, descrizione generica."
        nameout      = "video_generico"
        numero_clips = DEFAULT_CLIPS

    print(f"Prompt ITA: {promptita}")
    prompt_eng = G(source='it', target='en').translate(promptita)
    print(f"Prompt EN:  {prompt_eng}")
    return prompt_eng, nameout, numero_clips

# ========================= CONFIG =========================
MODEL_PATH      = "rootonchair/LTX-2-19b-distilled"
UPSAMPLER_PATH  = "Lightricks/LTX-2"          # ha la cartella latent_upsampler
path_lora2      = "./modelLTX2/loraLTX2/povnsfw-v3-complete.safetensors"




import torch
import argparse
import os
import numpy as np
from diffusers import LTX2ConditionPipeline, FlowMatchEulerDiscreteScheduler
from diffusers.pipelines.ltx2.pipeline_ltx2_condition import LTX2VideoCondition
from diffusers.pipelines.ltx2.utils import DISTILLED_SIGMA_VALUES
from diffusers.pipelines.ltx2.export_utils import encode_video
from diffusers.pipelines.ltx2.latent_upsampler import LTX2LatentUpsamplerModel
from diffusers.pipelines.ltx2 import LTX2LatentUpsamplePipeline
from PIL import Image
from deep_translator import GoogleTranslator as G
from tqdm import tqdm

# ========================= ARGOMENTI =======================
parser = argparse.ArgumentParser(description="LTX2 Video Generation")
parser.add_argument("--files",    type=str, required=True, help="Lista file immagine separati da |")
parser.add_argument("--prompts",  type=str, required=True, help="Lista prompt separati da |")
parser.add_argument("--nameout",  type=str, required=True, help="Lista nomi output separati da |")
parser.add_argument("--clips",    type=str, required=True, help="Lista numero clips separati da |")
parser.add_argument("--audio",    type=int, default=0,     help="Flag audio: 1=attivo, 0=disattivo")
parser.add_argument("--upscale",  type=int, default=0,     help="Flag upscale: 1=attivo, 0=disattivo")
args = parser.parse_args()

# ========================= PARSING LISTE ===================
lista_files   = args.files.split("|")
lista_prompts = args.prompts.split("|")
lista_nameout = args.nameout.split("|")
lista_clips   = [int(c) for c in args.clips.split("|")]
WITH_AUDIO    = bool(args.audio)
Upscale_flag  = bool(args.upscale)

# Verifica coerenza liste
assert len(lista_files) == len(lista_prompts) == len(lista_nameout) == len(lista_clips), \
    "Errore: le liste passate hanno lunghezze diverse!"

print(f"=== Parametri ricevuti ===")
print(f"Audio:   {WITH_AUDIO}")
print(f"Upscale: {Upscale_flag}")
for i in range(len(lista_files)):
    print(f"[{i}] {lista_files[i]} | {lista_nameout[i]} | clips={lista_clips[i]}")
    print(f"     Prompt: {lista_prompts[i][:60]}...")

# ========================= CONFIGURAZIONE ==================
device          = "cuda"
width           = 768
height          = 512
random_seed     = 42
generator       = torch.Generator(device).manual_seed(random_seed)
NEGATIVE_PROMPT = "worst quality, inconsistent motion, blurry, jittery, distorted"

# ========================= PIPELINE =======================
print("\nCaricamento pipeline...")
pipe = LTX2ConditionPipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16
)
pipe.load_lora_weights(path_lora2, adapter_name="lora1")
pipe.set_adapters(["lora1"], adapter_weights=[1.0])
pipe.enable_sequential_cpu_offload(device=device)
pipe.vae.enable_tiling()
print("Pipeline pronta!")

# ========================= LATENT UPSAMPLER ===============
if Upscale_flag:
    print("Caricamento latent upsampler...")
    latent_upsampler = LTX2LatentUpsamplerModel.from_pretrained(
        UPSAMPLER_PATH,
        subfolder="latent_upsampler",
        torch_dtype=torch.bfloat16,
    )
    upsample_pipe = LTX2LatentUpsamplePipeline(vae=pipe.vae, latent_upsampler=latent_upsampler)
    upsample_pipe.enable_model_cpu_offload(device=device)
    print("Upsampler pronto!")

os.makedirs("videos", exist_ok=True)

# ========================= FUNZIONI =======================
def prepare_image(img: Image.Image, target: int = 256) -> Image.Image:
    w, h = img.size
    if w < h:
        new_w, new_h = target, int(h * target / w)
    else:
        new_w, new_h = int(w * target / h), target
    return img.resize((new_w, new_h), Image.LANCZOS)

def decode_latent_to_numpy(video_latent: torch.Tensor) -> np.ndarray:
    with torch.no_grad():
        decoded = pipe.vae.decode(
            (video_latent / pipe.vae.config.scaling_factor).to(torch.bfloat16),
            return_dict=False,
        )[0]
    decoded = (decoded / 2 + 0.5).clamp(0, 1)
    decoded = decoded[0].permute(1, 2, 3, 0).float().cpu().numpy()
    return decoded

def extract_last_frame(video_latent: torch.Tensor) -> Image.Image:
    with torch.no_grad():
        decoded = pipe.vae.decode(
            (video_latent / pipe.vae.config.scaling_factor).to(torch.bfloat16),
            return_dict=False,
        )[0]
    last_frame = decoded[0, :, -1, :, :]
    last_frame = (last_frame / 2 + 0.5).clamp(0, 1)
    last_frame = last_frame.permute(1, 2, 0).float().cpu().numpy()
    last_frame = (last_frame * 255).astype(np.uint8)
    return Image.fromarray(last_frame)

# ========================= MAIN LOOP ======================
frame_rate = 24

# Calcola le clips totali per la progress bar
numero_video_totali = sum(lista_clips)
print(f"Video totali da generare: {numero_video_totali}")

video_counter = 0  # indice video globale per eventuale progress tracking

# ========================= UTILITY =======================
def get_unique_path(folder: str, basename: str, suffix: str) -> str:
    """Restituisce un path univoco: se 'basename_suffix.mp4' esiste,
    prova 'basename_suffix_2.mp4', '_3', ecc."""
    candidate = os.path.join(folder, f"{basename}_{suffix}.mp4")
    if not os.path.exists(candidate):
        return candidate
    idx = 2
    while True:
        candidate = os.path.join(folder, f"{basename}_{suffix}_{idx}.mp4")
        if not os.path.exists(candidate):
            return candidate
        idx += 1

for idx in tqdm(range(len(lista_files)), desc='Keyframes Totali'):
    image_path   = f"./out_image/{lista_files[idx]}"
    PROMPT       = lista_prompts[idx]
    nameout      = lista_nameout[idx]
    numero_clips = lista_clips[idx]

    print(f"\n{'='*50}")
    print(f"Immagine : {image_path}")
    print(f"NameOut  : {nameout}")
    print(f"Clips    : {numero_clips}")
    print(f"Prompt   : {PROMPT[:80]}...")

    prompt_eng = G(source='it', target='en').translate(PROMPT)
    print(f"Prompt eng: {prompt_eng}")

    current_image = prepare_image(Image.open(image_path).convert("RGB"))

    for c in tqdm(range(numero_clips), desc=f'Clips [{nameout}]', leave=False):
        video_counter += 1
        print(f"\n--- Clip {c + 1}/{numero_clips} ({nameout}) | Totale: {video_counter}/{numero_video_totali} ---")

        conditions = [
            LTX2VideoCondition(frames=current_image, index=0, strength=1.0)
        ]

        # ========================= STAGE 1 ================
        video_latent, audio_latent = pipe(
            conditions=conditions,
            prompt=prompt_eng,          # usa il prompt tradotto
            negative_prompt=NEGATIVE_PROMPT,
            width=width,
            height=height,
            num_frames=80,
            frame_rate=frame_rate,
            num_inference_steps=8,
            sigmas=DISTILLED_SIGMA_VALUES,
            guidance_scale=4.0,
            generator=generator,
            output_type="latent",
            return_dict=False,
        )

        # ========================= SALVATAGGIO LOW ========
        output_path_low = get_unique_path("videos", nameout, f"{c + 1}_low")
        video_s1_np = decode_latent_to_numpy(video_latent)
        if WITH_AUDIO:
            encode_video(
                video_s1_np,
                fps=frame_rate,
                audio=audio_latent[0].float().cpu(),
                audio_sample_rate=pipe.vocoder.config.output_sampling_rate,
                output_path=output_path_low,
            )
        else:
            encode_video(video_s1_np, fps=frame_rate, audio=None, audio_sample_rate=None, output_path=output_path_low)
        print(f"Stage 1 salvato → {output_path_low}")

        # ========================= UPSCALE ================
        if Upscale_flag:
            print("Upsampling latent...")
            upscaled_video = upsample_pipe(
                latents=video_latent,
                output_type="np",
                return_dict=False,
            )[0]
            output_path_high = get_unique_path("videos", nameout, f"{c + 1}_high")
            if WITH_AUDIO:
                encode_video(
                    upscaled_video[0],
                    fps=frame_rate,
                    audio=audio_latent[0].float().cpu(),
                    audio_sample_rate=pipe.vocoder.config.output_sampling_rate,
                    output_path=output_path_high,
                )
            else:
                encode_video(upscaled_video[0], fps=frame_rate, audio=None, audio_sample_rate=None, output_path=output_path_high)
            print(f"Clip {c + 1} upscalata → {output_path_high}")

        # ========================= PROSSIMO FRAME =========
        if c < numero_clips - 1:
            print("Estrazione ultimo frame per clip successiva...")
            current_image = extract_last_frame(video_latent)

        pipe.set_adapters(["lora1"], adapter_weights=[1.0])

print(f"\n✅ Tutte le clip generate! ({numero_video_totali} video totali)")