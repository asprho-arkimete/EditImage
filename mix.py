from logging import exception
from mailbox import Message
import os
import re
import tkinter as tk
from tkinter import YES, Scrollbar, ttk, filedialog as fd

from rich.table import Column
from tkinterdnd2 import TkinterDnD
from PIL import Image, ImageTk
import torch
from diffusers import Flux2KleinPipeline
from deep_translator import GoogleTranslator
from optimum.quanto import freeze, qfloat8, quantize
from safetensors import safe_open
from tqdm.std import tqdm


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

_TAGS = (
    " #path1:C:/percorso/immagine1.jpg"
    " #path2:C:/percorso/immagine2.jpg"
    " #path3:C:/percorso/immagine3.jpg"
    " #path4:C:/percorso/immagine4.jpg"
)

def make_prompt(testo: str) -> str:
    return testo + _TAGS


_COERENZA1 = "Mantieni sempre massima coerenza del soggetto nel image 1, del viso, capigliatura, occhi e fisico"
_COERENZA2 = "Mantieni sempre massima coerenza del soggetto nel image 2, del viso, capigliatura, occhi e fisico"
_COERENZA  = "Mantieni sempre massima coerenza del soggetto nel image 1 e del soggetto nel image 2, dei visi, capigliatura, occhi e fisico"


CHECKBOX_CONFIG_RAW = [
    # create 3 views + face: consistent character
    {
        "label": "Consistent 3viste+face",
        "prompt": make_prompt(f"""
Immagine fotorealistica, collage griglia 2x2, formato quadrato 1:1.
Quattro pannelli che mostrano la STESSA donna identica in ogni pannello,
stesso viso, stessi capelli, stesso corpo, stesso outfit in tutti i pannelli.

PANNELLO IN ALTO A SINISTRA: primo piano frontale del viso, testa e spalle.
PANNELLO IN ALTO A DESTRA: figura intera frontale dalla testa ai piedi, braccia lungo i fianchi.
PANNELLO IN BASSO A SINISTRA: figura intera vista laterale destra, dalla testa ai piedi.
PANNELLO IN BASSO A DESTRA: figura intera vista da dietro di spalle, dalla testa ai piedi.

Sfondo bianco neutro in tutti i pannelli, luce studio morbida.
Massima coerenza del personaggio in tutti e 4 i pannelli: stesso viso, stessi capelli, stessi occhi, stesso corpo, stesso outfit.
Fotorealistico, messa a fuoco nitida, alta risoluzione, stile scheda di riferimento personaggio.

#lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label": "Consistent2 3viste+face",
        "prompt": make_prompt(f"""
Immagine fotorealistica, collage griglia 2x2, formato quadrato 1:1.
Quattro pannelli che mostrano la STESSA donna identica in ogni pannello,
stesso viso, stessi capelli, stesso corpo, stesso outfit in tutti i pannelli.

PANNELLO IN ALTO A SINISTRA: primo piano frontale del viso, testa e spalle.
PANNELLO IN ALTO A DESTRA: figura intera frontale dalla testa ai piedi, braccia lungo i fianchi.
PANNELLO IN BASSO A SINISTRA: figura intera vista laterale destra, dalla testa ai piedi.
PANNELLO IN BASSO A DESTRA: figura intera vista da dietro di spalle, dalla testa ai piedi.

Sfondo bianco neutro in tutti i pannelli, luce studio morbida.
Massima coerenza del personaggio in tutti e 4 i pannelli: stesso viso, stessi capelli, stessi occhi, stesso corpo, stesso outfit.
Fotorealistico, messa a fuoco nitida, alta risoluzione, stile scheda di riferimento personaggio.

#lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label": "Consistent3 3viste+face",
        "prompt": make_prompt(f"""
Immagine fotorealistica, collage griglia 2x2, formato quadrato 1:1.
Quattro pannelli che mostrano la STESSA donna identica in ogni pannello,
stesso viso, stessi capelli, stesso corpo, stesso outfit in tutti i pannelli.

PANNELLO IN ALTO A SINISTRA: primo piano frontale del viso, testa e spalle.
PANNELLO IN ALTO A DESTRA: figura intera frontale dalla testa ai piedi, braccia lungo i fianchi.
PANNELLO IN BASSO A SINISTRA: figura intera vista laterale destra, dalla testa ai piedi.
PANNELLO IN BASSO A DESTRA: figura intera vista da dietro di spalle, dalla testa ai piedi.

Sfondo bianco neutro in tutti i pannelli, luce studio morbida.
Massima coerenza del personaggio in tutti e 4 i pannelli: stesso viso, stessi capelli, stessi occhi, stesso corpo, stesso outfit.
Fotorealistico, messa a fuoco nitida, alta risoluzione, stile scheda di riferimento personaggio.

#lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 2,
    },
    {
        "label": "Consistent4 3viste+face",
        "prompt": make_prompt(f"""
Immagine fotorealistica, collage griglia 2x2, formato quadrato 1:1.
Quattro pannelli che mostrano la STESSA donna identica in ogni pannello,
stesso viso, stessi capelli, stesso corpo, stesso outfit in tutti i pannelli.

PANNELLO IN ALTO A SINISTRA: primo piano frontale del viso, testa e spalle.
PANNELLO IN ALTO A DESTRA: figura intera frontale dalla testa ai piedi, braccia lungo i fianchi.
PANNELLO IN BASSO A SINISTRA: figura intera vista laterale destra, dalla testa ai piedi.
PANNELLO IN BASSO A DESTRA: figura intera vista da dietro di spalle, dalla testa ai piedi.

Sfondo bianco neutro in tutti i pannelli, luce studio morbida.
Massima coerenza del personaggio in tutti e 4 i pannelli: stesso viso, stessi capelli, stessi occhi, stesso corpo, stesso outfit.
Fotorealistico, messa a fuoco nitida, alta risoluzione, stile scheda di riferimento personaggio.

#lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 3,
    },
    # ==================== POSE PRIMARIE ====================
    {
        "label":  "in piedi",
        "prompt": make_prompt(f"""due ragazze in piedi in camera da letto; {_COERENZA} 
#lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 0,
    },

    {
        "label":  "sedute",
        "prompt": make_prompt(f"due ragazze sedute sul letto; {_COERENZA} #lora1:nome_file_lora #lora2:nome_file_lora"),
        "column": 1,
    },
    {
        "label":  "kiss",
        "prompt": make_prompt(f"due ragazze che si baciano alla francese sedute sul letto; {_COERENZA} #lora1:nome_file_lora #lora2:nome_file_lora"),
        "column": 2,
    },
    {
        "label":  "close up kiss",
        "prompt": make_prompt(f"close up kiss, primo piano bacio di due ragazze sedute sul letto; {_COERENZA} #lora1:nome_file_lora #lora2:nome_file_lora"),
        "column": 3,
    },

    # ==================== RIMUOVI VESTITI ====================
    {
        "label":  "rimuovi vestiti 1",
        "prompt": make_prompt(f"""clothesonoffv2, Rimuovi completamente i vestiti, 
rimuovi il vestito, rimuovi la maglia, la giacca, rimuovi la gonna, rimuovi i pantaloni, 
una ragazza totalmente nuda, seno piccolo nudo naturale, capezzoli dettagliati, 
visuale frontale del pube con pochi peli naturali,visuale frontale dettagli genitali femminili;
{_COERENZA1} #lora1:clothesonoffv2 #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "rimuovi vestiti 2",
        "prompt": make_prompt(f"""clothesonoffv2, Rimuovi completamente i vestiti, 
rimuovi il vestito, rimuovi la maglia, la giacca, rimuovi la gonna, rimuovi i pantaloni, 
una ragazza totalmente nuda, seno piccolo nudo naturale, capezzoli dettagliati, 
visuale frontale del pube con pochi peli naturali,visuale frontale dettagli genitali femminili;
{_COERENZA1} #lora1:clothesonoffv2 #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label":  "rimuovi vestiti 3",
        "prompt": make_prompt(f"""clothesonoffv2, Rimuovi completamente i vestiti, 
rimuovi il vestito, rimuovi la maglia, la giacca, rimuovi la gonna, rimuovi i pantaloni, 
una ragazza totalmente nuda, seno piccolo nudo naturale, capezzoli dettagliati, 
visuale frontale del pube con pochi peli naturali,visuale frontale dettagli genitali femminili;
{_COERENZA1} #lora1:clothesonoffv2 #lora2:nome_file_lora"""),
        "column": 2,
    },
    {
        "label":  "rimuovi vestiti 4",
        "prompt": make_prompt(f"""clothesonoffv2, Rimuovi completamente i vestiti, 
rimuovi il vestito, rimuovi la maglia, la giacca, rimuovi la gonna, rimuovi i pantaloni, 
una ragazza totalmente nuda, seno piccolo nudo naturale, capezzoli dettagliati, 
visuale frontale del pube con pochi peli naturali,visuale frontale dettagli genitali femminili;
{_COERENZA1} #lora1:clothesonoffv2 #lora2:nome_file_lora"""),
        "column": 3,
    },
    # rimuovi vestiti in consistent
    {
        "label": "Consistent4 3viste+face NUDE",
        "prompt": make_prompt(f"""
clothesonoffv2, rimozione completa dei vestiti, nudo integrale, rimozione totale di giacca, top, pantaloni e scarponi,
Immagine fotorealistica, collage griglia 2x2, formato quadrato 1:1.
Quattro pannelli che mostrano la STESSA donna identica in ogni pannello,
stesso viso, stessi capelli lunghi biondi, stesso corpo, stessa altezza.
PANNELLO IN ALTO A SINISTRA: primo piano frontale del viso, testa e spalle, espressione neutra, sguardo diretto.
PANNELLO IN ALTO A DESTRA: figura intera frontale nuda dalla testa ai piedi, braccia rilassate lungo i fianchi, 
gambe leggermente divaricate, seni naturali con capezzoli dettagliati, pube con peli naturali radi chiari, vulva dettagliata visibile.
PANNELLO IN BASSO A SINISTRA: figura intera vista laterale destra nuda, dalla testa ai piedi, posa eretta naturale, braccia lungo il corpo.
PANNELLO IN BASSO A DESTRA: figura intera vista da dietro nuda, dalla testa ai piedi, braccia lungo i fianchi, glutei e schiena dettagliati.

Sfondo bianco puro in tutti i pannelli, illuminazione studio morbida e uniforme.
Massima coerenza del personaggio: identica faccia e corporatura in tutti i pannelli.
Completamente nuda, anatomia realistica femminile, dettagli estremi della pelle, fotorealistico, altissima qualità, 8k {_COERENZA1} 
#lora1:clothesonoffv2 #lora2:nome_file_lora"""),
    "column": 0,
    },
    # perfect teen
    {
        "label":  "perfect teen",
        "prompt": make_prompt(f"""thighgap_k9b, Servizio fotografico in studio di una ragazza identica al image 1, snella e sensuale, in nudo integrale.
(totalmente nuda,seno nudo naturale, capezzoli, pube pochi peli), dettagli genitali feminili,Thighgap; 
{_COERENZA1}
#lora1:thighgap_k9b #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "close up perfect pussy teen",
        "prompt": make_prompt(f"""Foto amatoriale spontanea:(primo piano solo della parte:(inferiore del corpo di una giovane ragazza magra nuda)).
(pube pochi peli), dettagli genitali femminili. 
testa e seno fuori inquadratura.
Ha un tatuaggio sopra il bacino, sulla destra, con la scritta “Nome Ragazza”. 
{_COERENZA1}
#lora1:thighgap_k9b #lora2:nome_file_lora"""),
        "column": 1,
    },

    # ==================== POSE NSFW ====================
    {
        "label":  "gambe aperte",
        "prompt": make_prompt(f"""spread_legs_beta1, ragazza fotorealistica di 28 anni, stesso volto del riferimento, completamente nuda, 
distesa supina sul materasso, gambe estremamente divaricate e sollevate in area, ginocchia piegate, piedi visibili in telecamera,mani che tirano i glutei per aprire al massimo,
seno naturale morbido, capezzoli realistici, leggera peluria pubica brunetta,(figa estremamente dilatata),(grandi labbra della varina estremamente dilatate),
(piccole la della vagina estremamente dilatate),vulva aperta e bagnata,canale vaginale aperto con interno visibile,clitoride visibile, 
ano estremamente dilatato, enorme apertura anale rilassata, bordo analo stirato al massimo, profondità rettale visibile, 
pelle iperrealistica con texture dettagliata, lucida di succhi, foto raw 8k, qualità massima, dettaglio anatomico estremo, realismo fotografico crudo
{_COERENZA1} #lora1:spread_legs_beta1 #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label": "dildo Anal",
        "prompt": make_prompt(f"""anus_insertion_v1,Fotografia di una donna dell' image 1, 
totalmente nuda, capelli lunghi neri, con seno naturale, capezzoli realistici visibili. 
distesa su un letto matrimoniale con le gambe (alzate in area e divaricate), mentre guarda verso la fotocamera. 
Dall'ano spunta l'oggetto del image 2 di riferimento. Sullo sfondo si vede una parete bianca. 
L'inquadratura è frontale e riprende il suo corpo per intero e il viso.
poca peluria pubica castana naturale, vulva bagnata estremamente dettagliata, grandi labbra carnose, 
piccole labbra lunghe divaricate, profonda apertura vaginale, fluidi vaginali luccicanti, clitoride gonfio,
dettagli Anali:(Ano estremamente dilatato, Apertura anale visibile,righe intorno al Ano).  
texture pelle iperrealistica:del Ano,del corpo e del viso).
Occhi luminosi, labbra carnose con rossetto rosso.
foto grezza 8k, massima qualità, photorealistic, raw photo.
Mantieni massima coerenza del oggetto nella image 2
{_COERENZA1} #lora1:anus_insertion_v1 #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label": "dildo Anal 2",
        "prompt": make_prompt(f"""anus_insertion_v1,Fotografia della donna del image 1,completamente nuda, 
seno grande naturale, capezzoli realistici visibili, capelli lunghi biondi, accovacciata sul pavimento di una camera da letto con le gambe divaricate, pube rasato,dettagli genitali femminili, 
di fronte alla fotocamera e con lo sguardo rivolto verso l'obiettivo. L'oggetto del image 2 di riferimento è posizionato sul pavimento. Lei è accovacciata sull'oggetto. 
L'oggetto del image 2 è inserito nel suo ano.
Dilatazione ano estrema.
L'inquadratura è frontale. Lo sfondo mostra Una parete Bianca.
Mantieni Massima coerenza del oggetto nel image 2 di riferimento
{_COERENZA1} #lora1:anus_insertion_v1 #lora2:nome_file_lora"""),
        "column": 2,
    },
    {
        "label":  "posa pecora",
        "prompt": make_prompt(f"""PornMaster_innie_pussy_flux-2-klein-9b_V1, ripresa da dietro, volto di profilo visibile e coerente con image 1, 
inquadratura da dietro che mette in risalto ano estremamente e figa estremamente dilatata, grandi e piccole labbra divaricate, 
a quattro zampe sul pavimento, con gambe divaricate, completamente nuda, seno naturale, coerenza viso e capelli
 {_COERENZA1} #lora1:PornMaster_innie_pussy_flux-2-klein-9b_V1 #lora2:nome_file_lora"""),
        "column": 3,
    },

    # ==================== Allattamento ====================
    {
        "label":  "Allat ragazzo",
        "prompt": make_prompt(f"""klein_snofs_v1_3_converted, Allattamento, la donna del image 1 è totalmente nuda, seno nudo naturale, capezzoli visibili, pancia magra, ed è seduta sul letto con il busto e il seno di profilo e allatta il ragazzo del image 2.
Il ragazzo del image 2 è anch'esso totalmente nudo, pettorali visibili, e posa la bocca aperta sul seno della donna del image 1 e lecca con la lingua il suo capezzolo.
Mantieni massima coerenza del viso, capelli, occhi e seno della donna nel image 1;
Mantieni massima coerenza del viso, occhi e capelli del ragazzo nel image 2
#lora1:klein_snofs_v1_3_converted #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "Allat donna",
        "prompt": make_prompt(f"""kissing_with_extra_klein9b_v2_epoch, Primo piano ravvicinato di due donne nude in un momento intimo.
La donna del image 1 ha capelli lunghi castano scuro, occhi nocciola e carnagione chiara. È inclinata in avanti con la bocca leggermente aperta e guarda verso la fotocamera.
La donna del image 2 con capelli lunghi biondi si avvicina dal basso, il viso premuto contro il seno della donna in piedi, succhia il capezzolo.
Le mani della donna castana poggiano sul proprio ventre con unghie smaltate rosa chiaro.
Lo sfondo è una semplice parete verde tenue che mantiene il focus sui loro corpi.
Mantieni massima coerenza del viso, capelli, occhi e seno della donna image 1;
Mantieni massima coerenza del viso, occhi e capelli della donna image 2
#lora1:kissing_with_extra_klein9b_v2_epoch #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label":  "Allat donna2",
        "prompt": make_prompt(f"""kissing_with_extra_klein9b_v2_epoch, Primo piano ravvicinato di due donne nude in un momento intimo.
La donna del image 1 ha capelli lunghi biondi, occhi azzurri e carnagione chiara. È inclinata in avanti con la bocca leggermente aperta e guarda verso la fotocamera.
La donna del image 2 con capelli lunghi castano scuro e occhi nocciola si avvicina dal basso, il viso premuto contro il seno della donna in piedi, succhia il capezzolo.
Le mani della donna bionda poggiano sul proprio ventre con unghie smaltate rosa chiaro.
Lo sfondo è una semplice parete verde tenue che mantiene il focus sui loro corpi.
Mantieni massima coerenza del viso, capelli, occhi e seno della donna image 1;
Mantieni massima coerenza del viso, occhi e capelli della donna image 2
#lora1:kissing_with_extra_klein9b_v2_epoch #lora2:nome_file_lora"""),
        "column": 2,
    },

    # ==================== PRELIMINARI ====================
    {
        "label":  "pompino POV",
        "prompt": make_prompt(f"""POV_blowjobV1_A,Un'inquadratura in prima persona di una ragazza dalle labbra rosse mentre fa un pompino, 
ripresa dal punto di vista dell'uomo, luce naturale da finestra, stile spontaneo
{_COERENZA1} #lora1:POV_blowjobV1_A #lora2:nome_file_lora"""),
        "column": 0,
    },

     {
        "label":  "pompino_laterale",
        "prompt": make_prompt(f"""blowjob_klein_v1_side,Si tratta di una fotografia ad alta risoluzione che ritrae una scena esplicita per adulti. 
L'immagine mostra la ragazza del image 1, nuda con lunghi capelli, pelle chiara e un seno  naturale. È in ginocchio su un pavimento e 
sta praticando sesso orale a un uomo nudo in piedi. Il pene eretto dell'uomo è ben visibile nella sua bocca, mentre la mano di lui è appoggiata delicatamente 
sulla sua testa. La ragazza guarda l'uomo con uno sguardo concentrato. Sono visibili la parte inferiore del busto e le gambe dell'uomo, che mostrano una corporatura 
muscolosa e una carnagione chiara. Sullo sfondo c'è un letto con un piumone a motivi circolari in bianco e nero. La stanza ha un pavimento in legno massello e una 
palette di colori neutri.
{_COERENZA1} #lora1:blowjob_klein_v1_side #lora2:nome_file_lora"""),
        "column": 1,
    },

    {
        "label":  "close_up_pomp_late",
        "prompt": make_prompt(f"""blowjob_klein_v1_side,La fotografia ritrae un primo piano esplicito della ragazza del image 1, 
con lunghi capelli,mentre pratica sesso orale a un uomo. 
È inginocchiata e guarda verso l'alto l'uomo, con la bocca avvolta attorno al suo pene eretto. 
La ragazza ha un seno naturale, con areole e capezzoli rosa. totalmente nuda, 
La parte inferiore del busto e il pene dell'uomo sono visibili, 
ma il suo volto è fuori dall'inquadratura. Sullo sfondo si vede un letto matrimoniale e una parete bianca e una pianta in vaso verde con foglie simili a felci.
{_COERENZA1} #lora1:blowjob_klein_v1_side #lora2:nome_file_lora"""),
        "column": 2,
    },

    {
        "label":  "pomp_rovescio",
        "prompt": make_prompt(f"""FK_mountedfellatio,la ragazza del image 1 e un uomo. 
Sesso orale profondo, primo piano di sesso orale, gola profonda estrema; 
inquadratura dal basso: la ragazza totalmente nuda, ha la testa reclinata all’indietro e l’uomo le penetra profondamente la bocca con il suo pene di grandi dimensioni dall’alto. 
L’uomo è in piedi sopra la ragazza e sono visibili solo il suo sedere, le cosce e i testicoli. Il volto della ragazza è visibile solo in parte, 
essendo parzialmente coperto dal pene di grandi dimensioni che ha in bocca e dai testicoli dell’uomo. 
Questa fotografia raffigura una scena esplicita per adulti. 
La ragazza sta praticando sesso orale profondo a un uomo in piedi, 
il cui grosso pene eretto è visibile nella sua bocca. La parte inferiore del busto e le gambe dell'uomo sono parzialmente visibili. 
L'uomo le sta afferrando la testa.Lei è sdraiata contro un letto matrimoniale.
Seno nudo Naturale, capezzoli realistici.
{_COERENZA1} #lora1:FK_mountedfellatio #lora2:nome_file_lora"""),
        "column": 3,
    },

    {
        "label":  "Blowbang",
        "prompt": make_prompt(f"""blowbang_klein_v1,Foto molto esplicita, ripresa da vicino e dall'alto, di una donna del image 1 coinvolta in un rapporto sessuale di 
gruppo con più uomini. Attorno alla sua testa sono visibili diversi peni in erezione, con tonalità di pelle diverse, dal chiaro allo scuro. I corpi degli uomini 
sono per lo più fuori dall'inquadratura, ma sono visibili le loro parti pubiche e le loro mani.
{_COERENZA1} #lora1:blowbang_klein_v1 #lora2:nome_file_lora"""),
        "column": 0,
    },

    {
        "label":  "Blowbang sperma",
        "prompt": make_prompt(f"""blowbang_klein_v1,Una ragazza di 16 anni come image 1 con il viso ricoperto di sperma,totalmente nuda, seno nudo naturale,capezzoli, 
lei è circondata da diversi peni in erezione. 
L'illuminazione è intensa e uniforme, e mette in risalto il carattere esplicito della scena. 
L'inquadratura è dall'alto e cattura in dettaglio l'espressione del viso della donna e i genitali che la circondano.
{_COERENZA1} #lora1:blowbang_klein_v1 #lora2:nome_file_lora"""),
        "column": 1,
    },
    
    {
        "label":  "Sperma in Bocca",
        "prompt": make_prompt(f"""FK_cuminmouth8, la ragazza nel image 1.totalmente nuda, seno nudo naturale,capezzoli, ha la bocca aperta ed è piena di sperma. 
Ha dello sperma in bocca. Migliora le ombre e l'illuminazione,
{_COERENZA1} #lora1:FK_cuminmouth8 #lora2:nome_file_lora"""),
        "column": 2,
    },

    {
        "label":  "Close_upSpermaInBocca",
        "prompt": make_prompt(f"""FK_cuminmouth8, close up del viso della ragazza nel image 1 totalmante nuda,seno nudo naturale ,capezzoli, ha la bocca estremamente aperta ed è piena di sperma. 
Ha dello sperma in bocca. Migliora le ombre e l'illuminazione,
{_COERENZA1} #lora1:FK_cuminmouth8 #lora2:nome_file_lora"""),
        "column": 3,
    },
    
    {
        "label":  "pene_sperma",
        "prompt": make_prompt(f"""FK_bukkakenew2, la ragazza del image 1 di profilo,vista meta busto, completamente nuda, Seno nudo Naturale visibile, capezzoli visibili.
ha la bocca estremamente aperta, piena di molto sperma e un solo grande pene di fronte alla sua bocca.
Il pene è grande e erretto, vicino alla bocca della ragazza, fuori dalla bocca.
   {_COERENZA1}
#lora1:FK_bukkakenew2 #lora2:nome_file_lora"""),
        "column": 0,
    },

    # ==================== CUNNILINGUS ====================
    {
        "label":  "man_lickpussy 1",
        "prompt": make_prompt(f"""pussy_licking_klein_v1, Un uomo sta praticando sesso orale a una donna. La donna image 1 di riferimento ha le gambe divaricate, 
lasciando scoperta la vulva. Nella foto si intravede parzialmente il busto dell'uomo, con la testa posizionata tra le cosce della donna. 
Lei è totalmente nuda, lui è totalmente nudo. I suoi capelli biondi poggiano contro una parete bianca dietro di lei. Lui ha i capelli corti castano scuro e 
la barba incolta sul viso. Sono distesi su un letto matrimoniale con coperta bianca, con una morbida luce naturale che filtra attraverso le tende trasparenti 
sullo sfondo.
{_COERENZA1}
#lora1:pussy_licking_klein_v1 #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "lbs_lickpussyAB1",
        "prompt": make_prompt(f"""pussy_licking_klein_v1, Due donne in una scena intima, in cui una delle due sta praticando sesso orale all'altra. 
La donna  del image 1 che riceve il sesso orale ha le gambe divaricate, con la vulva completamente esposta. 
La donna del image 2 che pratica il sesso orale ha la testa posizionata tra le sue cosce, il viso affondato nella sua vagina, con la parte superiore del busto e seno visibile. 
La donna del image 1 che riceve il sesso orale ha i capelli biondi appoggiati contro una parete bianca ed è completamente nuda. seno grande,capezzoli visibili. 
La donna del image 2 che pratica sesso orale ha i capelli lunghi e rossi, un viso molto femminile, seno nudo naturale ed è completamente nuda. 
Sono sdraiate su un letto Matrimoniale , mentre una morbida luce naturale filtra attraverso le tende trasparenti sullo sfondo.
Mantieni massima coerenza del del image 1 del viso femminile, i capelli, gli occhi e il fisico
Mantieni massima coerenza del del image 2 del viso femminile, i capelli, gli occhi e il fisico
#lora1:pussy_licking_klein_v1 #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label":  "lbs_lickpussyBA1",
        "prompt": make_prompt(f"""pussy_licking_klein_v1, Due donne completamente nude sdraiate su un letto matrimoniale in una scena di sesso orale.
La donna con i capelli lunghi rossi del image 2 è sdraiata sulla schiena con la testa appoggiata contro una parete bianca, 
le gambe divaricate e la vulva completamente esposta, seno grande con capezzoli visibili, riceve sesso orale.
La donna con i capelli lunghi biondi del image 1 è sdraiata sul ventre con la testa posizionata tra le cosce della donna rossa, 
il viso affondato nella sua vagina, seno nudo naturale visibile, pratica sesso orale con la lingua.
Una morbida luce naturale filtra attraverso le tende trasparenti sullo sfondo.
Mantieni massima coerenza del viso femminile, i capelli, gli occhi e il fisico del image 1;
Mantieni massima coerenza del viso femminile, i capelli, gli occhi e il fisico del image 2
#lora1:pussy_licking_klein_v1 #lora2:nome_file_lora"""),
        "column": 2,
    },

    # ==================== CUNNILINGUS 2 ====================
    {
        "label":  "man_lickpussy_69",
        "prompt": make_prompt(f"""69lesbo, Una fotografia fotorealistica ad alta risoluzione, 
scattata da un'angolazione obliqua, primo piano intimo ed esplicito di sesso orale tra uomo e donna nudi su un letto matrimoniale. 
L'uomo del image 1 è sotto, sdraiato supino, occhi chiusi dal piacere, lingua protesa mentre lecca profondamente la vulva della donna sopra. 
La donna è sopra: gambe divaricate con ginocchia piegate, mani che afferrano e spalancano le sue natiche, vulva completamente esposta e presentata. 
Dettagli iperrealistici della vulva bagnata, saliva visibile, illuminazione sensuale.
{_COERENZA2}
#lora1:69lesbo #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "lsb_lickpussy_69_AB",
        "prompt": make_prompt(f"""69lesbo, fotografia fotorealistica ad alta risoluzione, angolazione obliqua, primo piano intimo ed esplicito di una scena di sesso orale 69 tra due donne nude su un letto,
donna sopra: la donna del image 1, ha capelli(lunghi lisci colore neri) è totalmente nuda, con le  gambe largamente divaricate, ginocchia piegate, mani che afferrano e spalancano le sue natiche, vulva completamente esposta e presentata alla ragazza sotto,
donna del image 2 una ragazza di 24 anni , capelli lunghi lisci colore biondi , occhi azzurri,completamente nuda è sotto, sdraiata supina, occhi aperti dal piacere, bocca aperta, lingua protesa e allungata che lecca profondamente la vagina della ragazza sopra, cunnilingus intenso, saliva visibile,
dettagli iperrealistici della vulva bagnata, genitali dettagliati, illuminazione sensuale calda,
Mantieni esatta coerenza del corpo e capelli del soggetto nel image 1;
Mantieni esatta coerenza del viso, occhi , capelli e fisico del soggetto nel image 2
#lora1:69lesbo #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label":  "lsb_lickpussy_69_BA",
        "prompt": make_prompt(f"""69lesbo, fotografia fotorealistica ad alta risoluzione, angolazione obliqua, primo piano intimo ed esplicito di una scena di sesso orale 69 tra due donne nude su un letto,
donna sopra: la donna del image 1, ha capelli(lunghi lisci colore neri) è totalmente nuda, con le  gambe largamente divaricate, ginocchia piegate, mani che afferrano e spalancano le sue natiche, vulva completamente esposta e presentata alla ragazza sotto,
donna del image 2 una ragazza di 24 anni , capelli lunghi lisci colore biondi , occhi azzurri,completamente nuda è sotto, sdraiata supina, occhi aperti dal piacere, bocca aperta, lingua protesa e allungata che lecca profondamente la vagina della ragazza sopra, cunnilingus intenso, saliva visibile,
dettagli iperrealistici della vulva bagnata, genitali dettagliati, illuminazione sensuale calda,
Mantieni esatta coerenza del corpo e capelli del soggetto nel image 1;
Mantieni esatta coerenza del viso, occhi , capelli e fisico del soggetto nel image 2
#lora1:69lesbo #lora2:nome_file_lora"""),
        "column": 2,
    },
        # ==================== ASS ====================
    {
        "label":  "Ass side",
        "prompt": make_prompt(f"""F.2K_Pose_Presenting_ass_and_pussy_sideways_epoch_32, la ragazza del image 1 (una bella sedicenne) è sdraiata su un fianco, 
completamente nuda, con un cuscino. Guarda lo spettatore. Ha le mani dietro le gambe. Si intravede la vulva chiusa. La fessura vaginale. 
Il sedere è rivolto a sinistra. Le gambe sono rivolte a destra.{_COERENZA1}
#lora1:F.2K_Pose_Presenting_ass_and_pussy_sideways_epoch_32 #lora2:nome_file_lora"""),
        "column": 0,
    },

    {
        "label":  "Ass side 2",
        "prompt": make_prompt(f"""F.2K_Pose_Presenting_ass_and_pussy_sideways_epoch_32,la ragazza del image 1 (una bella sedicenne) mostra il sedere e la figa di profilo.
La sua pelle brilla al sole mentre è distesa su un lettino da spiaggia. All’ombra di un grande ombrellone è completamente nuda, con un cuscino sotto la testa, 
una mano sul sedere e le natiche divaricate. In primo piano il sedere. Guarda lo spettatore. Il sedere è a destra. Le gambe sono a sinistra. 
Ambientazione da spiaggia. {_COERENZA1}
#lora1:F.2K_Pose_Presenting_ass_and_pussy_sideways_epoch_32 #lora2:nome_file_lora"""),
        "column": 1,
    },
{
    "label": "side rimming",
    "prompt": make_prompt(f"""klein_snofs_v1_4_converted, femaleasshole, 
scena erotica realistica di rimming lesbo,

ragazza del image 1 (senegalese con treccine): primo piano estremo sul suo sedere grande e sodo, glutei separati, ano roseo dettagliato e realistico, pelle liscia con texture naturale.

ragazza del image 2 (bionda): profilo viso molto vicino, bocca spalancata, lingua lunga, bagnata e flessibile che lecca profondamente l'ano, saliva lucida visibile.

perfect female anatomy, highly detailed realistic anus, natural puckered asshole, wet glossy skin, detailed tongue, saliva strings, correct proportions, sharp focus, no deformities, no artifacts.
{_COERENZA}
#lora1:klein_snofs_v1_4_converted #lora2:femaleasshole-f2-klein-9b-musubituner"""),
    "column": 0,
},
{
    "label": "side rimming 2",
    "prompt": make_prompt(f"""klein_snofs_v1_4_converted, femaleasshole, 
scena erotica realistica di rimming lesbo,

ragazza del image 1 (bionda): primo piano estremo sul suo sedere grande e sodo, glutei separati, ano roseo dettagliato e realistico, pelle liscia con texture naturale.

ragazza del image 2 (senegalese con treccine): profilo viso molto vicino, bocca spalancata, lingua lunga, bagnata e flessibile che lecca profondamente l'ano, saliva lucida visibile.

perfect female anatomy, highly detailed realistic anus, natural puckered asshole, wet glossy skin, detailed tongue, saliva strings, correct proportions, sharp focus, no deformities, no artifacts.
{_COERENZA}
#lora1:klein_snofs_v1_4_converted #lora2:femaleasshole-f2-klein-9b-musubituner"""),
    "column": 1,
},

{
    "label": "Fisting lesbo",
    "prompt": make_prompt(f"""F.2 K 9B - NSFW - Vaginal Fisting_epoch_29,Screenshot nitidissimo tratto da un documentario. 
Una donna identica al image 1, (a sinistra, seduta su un materasso matrimoniale, sui vent’anni, protesa in avanti verso la vulva dell’altra donna identica al image 2, 
con camice bianco da dottoressa e pantaloni neri,dalla pelle abbronzata e luccicante, concentrata sulla vulva dell’altra donna, 
mentre le infila il braccio destro, bagnato e luccicante, nella vagina) sta inserendo il braccio nella sua vagina, penetrazione vaginale. 
La donna a destra (seduta, che guarda l'altra donna con gli occhi spalancati, le gambe divaricate, la bocca chiusa, sorridente) 
è reclinata all'indietro mentre le sue braccia sostengono la sua posizione. 2 donne, capezzoli, nude, seni, capelli castani, gambe divaricate, figa, 
calda illuminazione naturale drammatica, ambientazione camera da letto matrimoniale, messa a fuoco nitida sulla vagina, figa, clitoride, bokeh. 
Le donne mantengono il contatto visivo.
{_COERENZA}
#lora1:F.2 K 9B - NSFW - Vaginal Fisting_epoch_29 #lora2:nome_file_lora"""),
    "column": 2,
},

{
    "label": "Fisting Anal lsb",
    "prompt": make_prompt(f"""F.2 K 9B - NSFW - Vaginal Fisting_epoch_29,Screenshot nitidissimo tratto da un documentario. 
Una donna identica al image 1, (a sinistra, seduta su un materasso matrimoniale, sui vent’anni, protesa in avanti verso ano dell’altra donna identica al image 2, 
con camice bianco da dottoressa e pantaloni neri,dalla pelle abbronzata e luccicante, concentrata sul ano dell’altra donna, 
mentre le infila il braccio destro, bagnato e luccicante, nel ano estremamente dilatato) sta inserendo il braccio nel ano, penetrazione anale. 
La donna a destra (seduta, che guarda l'altra donna con gli occhi spalancati, le gambe divaricate e sollevate in area, la bocca chiusa, sorridente) 
è reclinata all'indietro mentre le sue braccia sostengono la sua posizione. 2 donne, capezzoli, nude, seni, capelli, gambe divaricate e alzate in area, figa aperta,
dettagli genitali femminili, dettagli ano estremamente dilatato. 
calda illuminazione naturale drammatica, ambientazione camera da letto matrimoniale, messa a fuoco nitida sulla vagina, figa, clitoride, bokeh. 
Le donne mantengono il contatto visivo.
{_COERENZA}
#lora1:F.2 K 9B - NSFW - Vaginal Fisting_epoch_29 #lora2:nome_file_lora"""),
    "column": 3,
},
    # ==================== KAMASUTRA ====================
    {
        "label":  "Missionaria",
        "prompt": make_prompt(f"""FK_missionary,posizione del missionario, rapporto vaginale, 
penetrazione vaginale, punto di vista in prima persona, la ragazza nell'image 1 è totalmente nuda, sdraiata sulla schiena con le gambe divaricate su un letto matrimoniale. 
Seno nudo Naturale,capezzoli,
Un uomo la sta penetrando nella vagina. Sta facendo sesso vaginale con l'uomo nella posizione del missionario. Guarda verso la telecamera. 
L'uomo è fuori campo.{_COERENZA1}
#lora1:FK_missionary #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "lei sopra",
        "prompt": make_prompt(f"""pov_squatting_sex_f2k9b_000002500,Inquadratura dal basso: la ragazza del image 1 è accovacciata sul busto di un uomo sdraiata 
sul letto matrimoniale, il pene eretto dell'uomo le penetra la vagina; lei si china e guarda verso la telecamera, avvicinando il viso all'obiettivo, e appoggia 
entrambe le braccia a terra per sostenere il proprio peso. Una la ragazza con capelli lunghi,pelle chiara, totalmente nuda,seno naturale nudo, capezzoli visibili,
pube con pochi peli,dettagli genitali femminili. 
Ha un'espressione scioccata sul viso, la bocca aperta. Lo sfondo mostra una camera da letto con letto matrimoniale. {_COERENZA1} 
#lora1:pov_squatting_sex_f2k9b_000002500 #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label":  "lei sopra 2",
        "prompt": make_prompt(f"""klein-fnelson-13epoc-k3nk,FU11N31S0N: la ragazza del image 1 si gode una penetrazione vaginale con le gambe spalancate. 
L'uomo le infila profondamente il pene nella vagina della ragazza, assumendo una posizione a “full nelson”. Le sue espressioni facciali tradiscono piacere, mentre emette gemiti di 
godimento. I suoi movimenti sono ritmici e vigorosi, e denotano un notevole sforzo. Una scena intensa ed esplicita.
sfondo camera da letto matrimoniale.
Il volto del uomo non è visibile.{_COERENZA1}
#lora1:klein-fnelson-13epoc-k3nk #lora2:nome_file_lora"""),
        "column": 2,
    },
    {
        "label":  "Anal lei sopra",
        "prompt": make_prompt(f"""klein-fnelson-13epoc-k3nk,FU11N31S0N: A woman of image 1 enjoys an anal penetration with her legs spread wide apart. 
The man thrusts his veiny penis deeply into her, creating a full nelson position. Her facial expressions indicate pleasure, making sounds of enjoyment. 
His movements are rhythmic and forceful, exerting significant effort. This intense and explicit scene.
sfondo camera da letto.
{_COERENZA1}
#lora1:klein-fnelson-13epoc-k3nk #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "Anal lei sopra 2",
        "prompt": make_prompt(f"""full_nelson_anal_v1_f2k9b_000003100,Posizione “Full Nelson”: la donna del image 1, è distesa sopra un uomo nudo; 
lui le infila le braccia sotto le ginocchia, unisce le mani dietro il collo della donna e la penetra nell'ano con il pene eretto. Lei tiene le gambe sollevate, 
si stringe i glutei con entrambe le mani e guarda verso la telecamera. Inquadratura dall'alto. Una donna caucasica è totalmente nuda, seno nudo naturale,
capezzoli visibili,capelli  lunghi, fisico snello, pelle sudata, su un letto matrimoniale in camera.
Ha un'espressione di godimento. {_COERENZA1}
#lora1:full_nelson_anal_v1_f2k9b_000003100 #lora2:nome_file_lora"""),
        "column": 1,
    },
    
    {
        "label":  "Anal rovesciata",
        "prompt": make_prompt(f"""FK_piledriver,L'immagine, ripresa dall'alto, mostra la donna e un solo uomo. 
La donna del image 1 totalmente nuda si trova nella posizione sessuale del “piledriver”. È distesa a testa in giù con le gambe e i glutei sollevati. 
Un uomo è in piedi sopra di lei e il suo pene sta visibilmente penetrandole l'ano. È visibile solo la parte inferiore del corpo dell'uomo; 
il suo volto è fuori dall'inquadratura. Si tratta di una fotografia che ritrae una scena sessuale 
tra un uomo e una donna. La donna è distesa sulla schiena con le gambe divaricate. L'uomo è posizionato sopra di lei, con il pene eretto parzialmente inserito nel 
suo ano. Le sue mani le stringono le cosce per tenerla ferma. L'espressione della donna denota un leggero disagio mentre guarda l'uomo.
seno nudo naturale, capezzoli. {_COERENZA1}
#lora1:FK_piledriver #lora2:nome_file_lora"""),
        "column": 2,
    },
    
    {
        "label":  "Anal pecora",
        "prompt": make_prompt(f"""FK_bulldoganalsexfinal,L'immagine mostra la ragazza del image 1 e un uomo in camera da letto. 
La ragazza è a quattro zampe su un letto matrimoniale con la testa china. È di spalle allo spettatore e il suo viso è parzialmente visibile di profilo. 
Il suo sedere è rivolto verso lo spettatore, con l'ano e la vagina esposti. Il punto focale dell'immagine è la penetrazione dell'ano da parte dell'uomo. 
Lui sembra trovarsi in piedi sopra di lei. Le gambe della ragazza sono divaricate all'altezza delle cosce. Lui la sta penetrando nell'ano con il suo pene di 
grandi dimensioni. I suoi testicoli e il suo sedere sono visibili. L'intera parte superiore del corpo dell'uomo è fuori dall'inquadratura. 
Il suo volto non è visibile. Una fotografia di una scena sessuale. La ragazza è a quattro zampe. L'uomo con le gambe muscolose è dietro di lei e la penetra 
analmente con il suo pene eretto e non circonciso. La vagina della donna è visibile e la sua espressione denota piacere. Le gambe e i genitali dell'uomo sono in 
primo piano, mentre il viso e la parte superiore del corpo della donna sono sullo sfondo.
location camera da letto. {_COERENZA1}
#lora1:FK_bulldoganalsexfinal #lora2:nome_file_lora"""),
        "column": 3,
    },

    {
        "label":  "Doggystyle anal",
        "prompt": make_prompt(f"""FK_spitroastanal,L'immagine mostra una donna e due uomini. La ragazza del image 1 è a quattro zampe e sta praticando sesso orale a 
uno degli uomini. L'altro uomo la sta penetrando nell'ano da dietro. Sesso a tre con una donna e due uomini. Sesso a tre con una donna e due uomini. Sesso a 
pecorina. Sesso anale, sesso orale e gola profonda. L'attenzione è concentrata sulla donna, posizionata su una panca. È a quattro zampe, con la schiena inarcata 
e la testa girata a destra. La donna sta praticando sesso orale a un uomo nudo sulla destra, il cui pene eretto è nella sua bocca. I corpi degli uomini sono 
visibili, mentre i loro volti sono fuori campo. Allo stesso tempo, un altro uomo nudo la penetra nell'ano da dietro. Il suo pene è visibile mentre entra nel suo 
ano. La telecamera è focalizzata sul suo ano e le sue natiche sono in primo piano. Il corpo della ragazza è girato di spalle alla telecamera. 
Mantieni il suo abbigliamento, l'acconciatura e l'ambientazione. La gonna è sollevata e il tanga è tirato da parte, lasciando scoperto l'ano.
{_COERENZA1}
#lora1:FK_spitroastanal #lora2:nome_file_lora"""),
        "column": 0,
    },

    {
        "label":  "Side Anal",
        "prompt": make_prompt(f"""FK_analonside,L'immagine mostra una ragazza e un uomo. ragazza identica al image 1, totalmente nuda,
è sdraiata su un fianco con le gambe chiuse. seno naturale nudo, capezzoli, Ha la vagina e l'ano esposti.
L'uomo la penetra nell'ano con il suo pene di grandi dimensioni. L'attenzione è focalizzata sulla penetrazione dell'ano, 
sulle sue cosce e sul sedere. Una fotografia di una scena sessuale. Una donna giace su un letto bianco; un uomo nudo con il pene eretto è posizionato alla sua 
sinistra, con il pene che le penetra l'ano. La mano destra della donna è sulla sua coscia destra, mentre la mano sinistra è sul letto. 
L'uomo ha un pene gigantesco. È caucasico. La parte superiore del corpo dell'uomo è fuori dall'inquadratura e il suo volto non è visibile.
{_COERENZA1}
#lora1:FK_analonside #lora2:nome_file_lora"""),
        "column": 1,
    },

    {
        "label":  "DP Frontale",
        "prompt": make_prompt(f"""F.2K_Pose_ Double_penetration_frontal_epoch_21,doppia penetrazione, frontale, pene inserito nella sua vagina, 
pene inserito nel suo ano, 1 ragazza, più ragazzi, trio mmf, 2 ragazzi, sesso, trio, pene, sesso di gruppo, capezzoli, etero, vaginale, anale, 
doppia penetrazione, completamente nudi, nudi, più peni, testicoli, realistico, seni, occhi aperti, eccitati.
scenario camera da letto matrimoniale, con pareti rosa, stanno usando un letto mattrimoniale con lenzuola bianche, 
un uomo è sdraiato in basso a sinistra, mentre la donna è protesa verso sinistra sopra di lui. 
A destra, accanto a lei, l'altro uomo sta spingendo il suo pene dentro la sua vagina. 
La donna del image 1 sta allargando entrambe le gambe piegate.
{_COERENZA1}
#lora1:F.2K_Pose_ Double_penetration_frontal_epoch_21 #lora2:nome_file_lora"""),
        "column": 2,
    },
    
    {
        "label":  "DP cowgirl",
        "prompt": make_prompt(f"""FK_cowgirldoublepenetration, L'immagine mostra una ragazza e due uomini. La ragazza del image 1 è raffigurata di profilo e 
di schiena, seduta sulle ginocchia di uno degli uomini. Quest'uomo è sdraiato sotto di lei e la sta penetrando nella vagina con il pene. 
Il secondo uomo è in piedi accanto alla ragazza e la sta penetrando nell'ano con il pene. L'uomo sdraiato la penetra nella vagina con il pene e l'uomo in piedi 
la penetra nell'ano con il pene. La parte superiore del corpo dell'uomo sdraiato sotto la ragazza è appena visibile, il suo volto non è mostrato nell'immagine. 
La parte superiore del corpo dell'uomo in piedi è fuori dall'inquadratura e il suo volto non è visibile. Il volto della ragazza è leggermente girato di lato, 
mentre guarda indietro verso la fotocamera. L'immagine si concentra principalmente sulla doppia penetrazione del trio. Si tratta di una fotografia ad alta 
risoluzione che raffigura una scena sessuale esplicita che coinvolge tre persone. Il punto focale è la donna. È a quattro zampe su un 
letto matrimoniale con lenzuola bianche, con la schiena inarcata e i glutei sollevati. Dietro di lei, un uomo muscoloso la sta penetrando nell'ano da dietro. 
Il suo pene grande ed eretto sta visibilmente entrando nel suo ano da dietro. Sdraiato sotto di lei, c'è un altro uomo, anch'egli nudo, 
con il pene eretto che le penetra la vagina.
{_COERENZA1}
#lora1:FK_cowgirldoublepenetration #lora2:nome_file_lora"""),
        "column": 3,
    },

        # cum in pussy
    {
        "label":  "sperma figa",   # ← Corretto
        "prompt": make_prompt(f"""spread_legs_beta1,fotorealistica,ragazza di 16 anni identica al image 1, massima coerenza del viso, capelli, occhi, 
    sdraiata supina sul letto, gambe sollevate e divaricate in aria, mani che tengono le cosce aperte, 
    seni naturali nudi, capezzoli dettagliati, fisico snello e magro,
    inquadratura ravvicinata sulla vagina estremamente dilatata, 
    messa a fuoco: (sul viso e sulla figa),
    interno della figa completamente riempito di sperma spesso, vulva stracolma di sborra bianca che cola abbondantemente verso l'ano, 
    clitoride gonfio e visibile,
    pube con pochi peli castani sottili, 
    grandi labbra della figa molto aperte e tirate verso l'esterno, piccole labbra estremamente divaricate e tirate, dettagliate e bagnate, 
    sperma bianco traslucido che riempie la vagina e cola verso l'ano,
    ano estremamente dilatato con rughe realistiche e texture dettagliata della pelle,
    alta risoluzione, photorealistic, pelle realistica, illuminazione morbida, dettagli estremi
    {_COERENZA1}
    #lora1:spread_legs_beta1 #lora2:nome_file_lora"""),
        "column": 0,
    },

        # close up - cum in pussy
    {
        "label":  "close up-sperma figa",    
        "prompt": make_prompt(f"""spread_legs_beta1,fotorealistica, close up messa a fuoco sulla figa della ragazza,corpo  identico al image 1,solo corpo,
    viso e testa fuori inqudratura.
    lei è sdraiata supina sul letto, gambe sollevate e divaricate in aria, mani che tengono le cosce aperte, 
    seni naturali nudi, capezzoli dettagliati, fisico snello e magro,
    inquadratura ravvicinata sulla vagina estremamente dilatata, 
    messa a fuoco: (sulla figa),
    interno della figa completamente riempito di sperma spesso, vulva stracolma di sborra bianca che cola abbondantemente verso l'ano, 
    clitoride gonfio e visibile,
    pube con pochi peli castani sottili, 
    grandi labbra della figa molto aperte e tirate verso l'esterno, piccole labbra estremamente divaricate e tirate, dettagliate e bagnate, 
    sperma bianco traslucido che riempie la vagina e cola verso l'ano,
    ano estremamente dilatato con rughe realistiche e texture dettagliata della pelle,
    alta risoluzione, photorealistic, pelle realistica, illuminazione morbida, dettagli estremi
    {_COERENZA1}
    #lora1:spread_legs_beta1 #lora2:nome_file_lora"""),
        "column": 1,
    },

    # Addition sperma
    {
        "label":  "aggiungi sperma",    
        "prompt": make_prompt(f"""PornMaster_cum_flux-2-klein-9b_V1,
Aggiungi tanto//poco cum sulla faccia
Aggiungi tanto//poco cum sul seno
Aggiungi tanto//poco cum sulle mani
Aggiungi tanto//poco cum sulla figa,interno vulva
Aggiungi tanto//poco cum sull' ano
Aggiungi tanto//poco cum sui piedi
alta risoluzione, photorealistic, pelle realistica, illuminazione morbida, dettagli estremi
{_COERENZA1} #lora1:PornMaster_cum_flux-2-klein-9b_V1 #lora2:nome_file_lora"""),
        "column": 2,
    },

    # Convert woman in woman Trans
    {
        "label":  "Convert_Woman_to_TransWo",   # ← Corretto
        "prompt": make_prompt(f"""clothesonoffv2,Klein9BGeneralPenis-v1-5BETA,rimuovi completamente i vestiti, rimuovi completamente la maglietta nera,rimuovi completamente i pantaloni neri,
    la femboy del image 1 è in piedi completamante nuda, seno naturale, capezzoli, dettagli genitali maschili, grande pene erretto,glande.
    {_COERENZA1}
    #lora1:clothesonoffv2 #lora2:Klein9BGeneralPenis-v1-5BETA"""),
        "column": 0,
    },

    # transferpose (Maching_Pose)
    {
        "label":  "transf_pose Maching1",
        "prompt": make_prompt(f"""Transfer the pose from the mannequin in image 1 to the girl in image 2.
The girl must be upside down performing a handstand.
Maintain exact coherence with image 2: face, hairstyle, eyes, and body.
#lora1:Maching_Pose_9B_Rank256 #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "transf_pose Maching2",
        "prompt": make_prompt(f"""Transfer the pose from the mannequin in image 1 to the girl in image 2.
The girl must be upside down performing a handstand.
Maintain exact coherence with image 2: face, hairstyle, eyes, and body.
#lora1:Maching_Pose_9B_Rank256 #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label":  "transf_pose Maching3",
        "prompt": make_prompt(f"""Transfer the pose from the mannequin in image 1 to the girl in image 2.
The girl must be upside down performing a handstand.
Maintain exact coherence with image 2: face, hairstyle, eyes, and body.
#lora1:Maching_Pose_9B_Rank256 #lora2:nome_file_lora"""),
        "column": 2,
    },
    {
        "label":  "transf_pose Maching4",
        "prompt": make_prompt(f"""Transfer the pose from the mannequin in image 1 to the girl in image 2.
The girl must be upside down performing a handstand.
Maintain exact coherence with image 2: face, hairstyle, eyes, and body.
#lora1:Maching_Pose_9B_Rank256 #lora2:nome_file_lora"""),
        "column": 3,
    },

    # ==================== PERSONALIZZABILI ====================
    {
        "label":  "costum 1",
        "prompt": make_prompt(f"inserisci il tuo prompt qui;{_COERENZA1} #lora1:nome_file_lora #lora2:nome_file_lora"),
        "column": 0,
    },
    {
        "label":  "costum 2",
        "prompt": make_prompt(f"inserisci il tuo prompt qui;{_COERENZA1} #lora1:nome_file_lora #lora2:nome_file_lora"),
        "column": 1,
    },
    {
        "label":  "costum 3",
        "prompt": make_prompt(f"inserisci il tuo prompt qui;{_COERENZA1} #lora1:nome_file_lora #lora2:nome_file_lora"),
        "column": 2,
    },
    {
        "label":  "costum 4",
        "prompt": make_prompt(f"inserisci il tuo prompt qui;{_COERENZA1} #lora1:nome_file_lora #lora2:nome_file_lora"),
        "column": 3,
    },

    # ==================== TRASFORMA SCHIZZO DEL DISEGNO IN FOTOREALISRMO ====================
    {
        "label":  "transform skz 1",
        "prompt": make_prompt(f"""trasforma lo schizzo del disegno rosa in ....,
trasforma lo schizzo del disegno verde in ....,
trasforma lo schizzo del disegno blue in ....;
{_COERENZA1}
 #lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 0,
    },
    {
        "label":  "transform skz 2",
        "prompt": make_prompt(f"""trasforma lo schizzo del disegno rosa in ....,
trasforma lo schizzo del disegno verde in ....,
trasforma lo schizzo del disegno blue in ....;
{_COERENZA1}
 #lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 1,
    },
    {
        "label":  "transform skz 3",
        "prompt": make_prompt(f"""trasforma lo schizzo del disegno rosa in ....,
trasforma lo schizzo del disegno verde in ....,
trasforma lo schizzo del disegno blue in ....;
{_COERENZA1}
 #lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 2,
    },
    {
        "label":  "transform skz 4",
        "prompt": make_prompt(f"""trasforma lo schizzo del disegno rosa in ....,
trasforma lo schizzo del disegno verde in ....,
trasforma lo schizzo del disegno blue in ....;
{_COERENZA1}
 #lora1:nome_file_lora #lora2:nome_file_lora"""),
        "column": 3,
    },
]

# ── calcola row automaticamente ──────────────────────────────────────────────
row = -1
for item in CHECKBOX_CONFIG_RAW:
    if item["column"] == 0:
        row += 1
    item["grid"] = {"row": row, "column": item.pop("column")}

CHECKBOX_CONFIG = CHECKBOX_CONFIG_RAW

# ═══════════════════════════════════════════════════════════════════════════════
# FINESTRA PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

window = TkinterDnD.Tk()
window.title("Image Edit Mix 4B 9B")
window.geometry("1228x900")
window.config(bg='gray')
window.resizable(False, False)

# Frame contenitore riga superiore (canvas + checkbox)
frame_top = tk.Frame(window, bg='gray')
frame_top.grid(row=0, column=0, columnspan=2, sticky='nw')
frame_top.config(background='gray')

# Frame canvas immagini
frame_canvas = tk.Frame(frame_top)
frame_canvas.grid(row=0, column=0, sticky='nw')
frame_canvas.config(background='gray')


# ═══════════════════════════════════════════════════════════════════════════════
# CANVAS DRAG & DROP
# ═══════════════════════════════════════════════════════════════════════════════

def drag_drop(event):
    """Gestisce il drag and drop e salva il path nell'attributo del canvas."""
    path = event.data
    if not path:
        return

    path = path.strip('{}')

    try:
        img = Image.open(path)
    except Exception as e:
        print(f"Errore apertura immagine: {e}")
        return

    canvas   = event.widget
    canvas_w = int(canvas['width'])
    canvas_h = int(canvas['height'])
    img_w, img_h = img.size

    if img_w >= img_h:
        to_w = canvas_w
        to_h = int(canvas_w * img_h / img_w)
    else:
        to_h = canvas_h
        to_w = int(canvas_h * img_w / img_h)

    img    = img.resize((to_w, to_h), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)

    canvas.delete("all")
    canvas.create_image(canvas_w // 2, canvas_h // 2, anchor='center', image=img_tk)
    canvas.image          = img_tk   # evita garbage collection
    canvas.image_path     = path
    canvas.original_image = img

    return path


canvas_infos = [
    (0, 0, 'red',    'inserisci immagine 1'),
    (0, 1, 'violet', 'inserisci immagine 2'),
    (1, 0, 'cyan',   'inserisci immagine 3'),
    (1, 1, 'orange', 'inserisci immagine 4'),
]

canvases = []
for idx, (r, c, color, label) in enumerate(canvas_infos):
    canvas = tk.Canvas(frame_canvas, width=256, height=256, bg=color)
    canvas.grid(row=r, column=c)
    canvas.create_text(128, 128, text=label)
    canvas.drop_target_register('DND_Files')
    canvas.dnd_bind('<<Drop>>', drag_drop)
    canvas.image_index = idx
    canvases.append(canvas)


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT BOX PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

text = tk.Text(frame_canvas, width=62, height=10)
text.grid(row=2, column=0, columnspan=2, sticky='nw', pady=5)

def set_prompt(prompt):
    """Imposta il prompt nella text box."""
    text.delete("1.0", tk.END)
    text.insert("1.0", prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKBOX — generate automaticamente da CHECKBOX_CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

frame_check   = tk.Frame(frame_top, bg='lightgray')
frame_check.grid(row=0, column=1, sticky='n')

checked_order = []
active_idx    = None
prompts_state = [item["prompt"] for item in CHECKBOX_CONFIG]

# Aggiungi variabile tkinter a ogni voce del config
for item in CHECKBOX_CONFIG:
    item["var"] = tk.IntVar(value=0)

def on_check(which):
    global active_idx

    # Salva il prompt corrente prima di cambiare
    if active_idx is not None:
        prompts_state[active_idx] = text.get("1.0", "end-1c")

    if CHECKBOX_CONFIG[which]["var"].get() == 1:
        if which in checked_order:
            checked_order.remove(which)
        checked_order.append(which)
        active_idx = which
        set_prompt(prompts_state[which])
    else:
        if which in checked_order:
            checked_order.remove(which)
        if checked_order:
            last       = checked_order[-1]
            active_idx = last
            set_prompt(prompts_state[last])
        else:
            active_idx = None
            text.delete("1.0", tk.END)

# Creazione checkbox dal config
for idx, item in enumerate(CHECKBOX_CONFIG):
    cb = tk.Checkbutton(
        frame_check,
        text=item["label"],
        variable=item["var"],
        command=lambda i=idx: on_check(i),   # i=idx evita closure bug
    )
    cb.grid(padx=5, pady=5, sticky='w', **item["grid"])
    item["widget"] = cb


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME STRUMENTI
# ═══════════════════════════════════════════════════════════════════════════════

strumenti = tk.Frame(window, bg='darkgray')
strumenti.grid(row=2, column=0, sticky='w')


def get_lora_version(filepath):
    try:
        with safe_open(filepath, framework="pt", device="cpu") as f:
            keys = list(f.keys())

            for key in keys:
                tensor = f.get_tensor(key)
                shape = tensor.shape

                # Salta tensori scalari o 1D senza info utili
                if len(shape) < 1:
                    continue

                if any(x in key.lower() for x in ["double_blocks", "single_blocks", "img_attn", "txt_attn", "mlp"]):

                    dim = max(shape) if len(shape) > 1 else shape[0]

                    if dim == 3072 or (len(shape) > 1 and shape[-1] == 3072):
                        return "4B"
                    elif dim == 4096 or (len(shape) > 1 and shape[-1] == 4096):
                        return "9B"

                    if dim > 2000 and dim < 3200:
                        return "4B"
                    elif dim > 3800:
                        return "9B"

    except Exception as e:
        print(f"Errore analisi LoRA {filepath}: {e}")

    return "Unknown"


def load_lora(event=None):
    models_4b = []
    models_9b = []
    unknown = []

    for l in os.listdir("lora"):
        if not l.endswith(".safetensors"):
            continue
            
        name = os.path.splitext(l)[0]
        version = get_lora_version(f"lora/{l}")
        
        if version == "4B":
            models_4b.append(name)
        elif version == "9B":
            models_9b.append(name)
        else:
            unknown.append(name)

    model_lora['values'] = (
        ["── LoRA 4B ──────────────────"] +
        (models_4b if models_4b else ["  (nessuno)"]) +
        ["── LoRA 9B ──────────────────"] +
        (models_9b if models_9b else ["  (nessuno)"]) +
        ["── Unknown / Non rilevati ──"] +
        (unknown if unknown else ["  (nessuno)"])
    )

def select_lora(event=None):
    selected = model_lora.get()
    if selected.startswith("──") or selected.startswith("  ("):
        return

    contenuto = text.get('1.0', tk.END).rstrip('\n')

    # ── Sostituisce TUTTI i placeholder lora1 se presenti ───────────────────
    if "lora1:nome_file_lora" in contenuto:
        nuovo = selected + ',' + contenuto.replace("lora1:nome_file_lora", f"lora1:{selected}")

    # ── Placeholder lora2 ────────────────────────────────────────────────────
    elif "lora2:nome_file_lora" in contenuto:
        # aggiunge selected in testa dopo i nomi già presenti
        nuovo = selected + ',' + contenuto.replace("lora2:nome_file_lora", f"lora2:{selected}")

    # ── Nessun placeholder: inserisce nel primo slot libero ─────────────────
    elif "#lora1:" not in contenuto:
        nuovo = selected + ',' + contenuto + f" #lora1:{selected}"

    elif "#lora2:" not in contenuto:
        nuovo = selected + ',' + contenuto + f" #lora2:{selected}"

    else:
        # Entrambe già occupate: sovrascrive lora2
        nuovo = selected + ',' + re.sub(r'#lora2:\S+', f'#lora2:{selected}', contenuto)

    nuovo = re.sub(r'#{2,}', '#', nuovo)
    text.delete('1.0', tk.END)
    text.insert('1.0', nuovo)

# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE PROMPT — carica immagine e inserisce path nel prompt
# ═══════════════════════════════════════════════════════════════════════════════

def load_image_prompt():
    path = fd.askopenfilename()
    if not path:
        return

    contenuto         = text.get("1.0", tk.END)
    placeholder_trovato = False

    for i in range(1, 5):
        placeholder = f"#path{i}:C:/percorso/immagine{i}.jpg"
        if placeholder in contenuto:
            nuovo = contenuto.replace(placeholder, f"#path{i}:{path}")
            text.delete("1.0", tk.END)
            text.insert("1.0", nuovo.rstrip('\n'))
            placeholder_trovato = True
            break

    if not placeholder_trovato:
        for i in range(1, 5):
            if f"#path{i}:" not in contenuto:
                nuovo = contenuto.rstrip('\n') + f" #path{i}:{path}"
                text.delete("1.0", tk.END)
                text.insert("1.0", nuovo)
                break


# ═══════════════════════════════════════════════════════════════════════════════
# GENERAZIONE IMMAGINE
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# VARIABILI GLOBALI
# ═══════════════════════════════════════════════════════════════════════════════

old_lora  = None
old_lora2 = None
pipe      = None


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD LORA SMART — gestisce LoRA standard e LoKr
# ═══════════════════════════════════════════════════════════════════════════════

def load_lora_smart(pipe, lora_path, adapter_name='lora1', weight=0.8):
    from safetensors.torch import load_file, save_file
    import tempfile, os, torch

    state = load_file(lora_path)
    keys  = list(state.keys())
    is_lokr = any('lokr_w1' in k for k in keys)

    if not is_lokr:
        pipe.load_lora_weights(lora_path, adapter_name=adapter_name)
        pipe.set_adapters(adapter_name, adapter_weights=weight)
        print(f"✅ LoRA standard caricata [{adapter_name}]")
        return

    print(f"🔄 Formato LoKr rilevato per [{adapter_name}], conversione in corso...")
    converted = {}

    layer_keys = set()
    for k in keys:
        if 'lokr_w1' in k:
            layer_keys.add(k.replace('.lokr_w1', ''))

    for layer in layer_keys:
        w1 = state.get(f"{layer}.lokr_w1")
        w2 = state.get(f"{layer}.lokr_w2")
        if w1 is None or w2 is None:
            continue
        try:
            w_full = torch.kron(w1.float(), w2.float())
            U, S, Vh = torch.linalg.svd(w_full, full_matrices=False)
            rank   = min(32, S.shape[0])
            S_sqrt = torch.sqrt(S[:rank])
            lora_B = (U[:, :rank] * S_sqrt).T
            lora_A = Vh[:rank, :] * S_sqrt.unsqueeze(1)
            converted[f"{layer}.lora_A.weight"] = lora_A.bfloat16()
            converted[f"{layer}.lora_B.weight"] = lora_B.bfloat16()
        except Exception as e:
            print(f"⚠️ SVD fallita per {layer}: {e}")
            continue

    if not converted:
        print(f"❌ Nessun layer convertito per [{adapter_name}]")
        return

    with tempfile.NamedTemporaryFile(suffix='.safetensors', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        save_file(converted, tmp_path)
        pipe.load_lora_weights(tmp_path, adapter_name=adapter_name)
        pipe.set_adapters(adapter_name, adapter_weights=weight)
        print(f"✅ LoKr convertita e caricata [{adapter_name}] ({len(converted)//2} layer)")
    finally:
        os.unlink(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════════
# FLUX2 — generazione immagine con supporto doppia LoRA
# ═══════════════════════════════════════════════════════════════════════════════
stop=False
def flux2():
    global old_lora, old_lora2, pipe, active_idx, stop,stop_generate,window
    stop = False
    stop_generate.config(bg='green')
    window.update_idletasks()
    if active_idx is not None:
        prompts_state[active_idx] = text.get("1.0", "end-1c")
 
    try:
        default_images = [
            c.original_image.copy()
            for c in canvases if hasattr(c, 'original_image')
        ]
        if not default_images:
            print("ℹ️ Nessuna immagine nelle canvas, verrà usato solo il prompt o i path.")
    except Exception as e:
        print(f"ℹ️ Errore lettura canvas: {e} → si procede con path del prompt")
        default_images = []
 
    device    = "cuda"
    dtype     = torch.bfloat16
    width, height = map(int, risoluzione.get().split('x'))
    num_steps = steps.get()
    print(f"Model: {model.get()}")
 
    # ── Filtra solo i keyframes selezionati PRIMA del loop ──────────────────
    selected = [
        (item, prompt_it)
        for item, prompt_it in zip(CHECKBOX_CONFIG, prompts_state)
        if item["var"].get() == 1
    ]

    for i, (item, prompt_it) in enumerate(tqdm(selected, desc='Keyframes selezionati', unit='img')):
        if item["var"].get() != 1:
            continue
 
        lora_name        = None
        lora_name2       = None          # ← seconda LoRA
        reference_images = default_images.copy()
 
        parts        = prompt_it.split('#')
        prompt_testo = parts[0].strip()
 
        for part in parts[1:]:
            part = part.strip()
 
            # ── LoRA 1 ──────────────────────────────────────────────────────
            if part.startswith('lora1:'):
                valore          = part[len('lora1:'):].strip().strip(',')
                lora_path_check = os.path.join("lora", f"{valore}.safetensors")
                if valore and os.path.exists(lora_path_check):
                    lora_name = valore
                else:
                    print(f"ℹ️ LoRA1 '{valore}' non trovato, ignorato")
 
            # ── LoRA 2 ──────────────────────────────────────────────────────
            elif part.startswith('lora2:'):
                valore          = part[len('lora2:'):].strip().strip(',')
                lora_path_check = os.path.join("lora", f"{valore}.safetensors")
                if valore and os.path.exists(lora_path_check):
                    lora_name2 = valore
                else:
                    print(f"ℹ️ LoRA2 '{valore}' non trovato, ignorato")
 
            # ── Path immagini ────────────────────────────────────────────────
            elif any(part.startswith(f'path{n}:') for n in range(1, 5)):
                path = part.split(':', 1)[1].strip()
                if path and os.path.exists(path):
                    if reference_images is default_images:
                        reference_images = []
                    reference_images.append(Image.open(path).convert('RGB'))
                    print(f"ℹ️ Path '{path}' immagine trovata e aggiunta al contenitore")
                else:
                    print(f"ℹ️ Path '{path}' non trovato, ignorato")
 
        # Fallback lora1 dal combobox se non specificata nel prompt
        if lora_name is None:
            lora_name = model_lora.get() or None
            if lora_name and (lora_name.startswith("──") or lora_name.startswith("  (")):
                lora_name = None

        # ── Ricarica modello se pipe assente o LoRA cambiate ────────────────
        if pipe is None or lora_name != old_lora or lora_name2 != old_lora2:
            print("Caricamento modello...")

            path_model = (
                "black-forest-labs/FLUX.2-klein-4B"
                if model.get() == 'Flux2K_4B'
                else "black-forest-labs/FLUX.2-klein-9B"
            )

            pipe = Flux2KleinPipeline.from_pretrained(
                path_model,
                low_cpu_mem_usage=False,
                torch_dtype=dtype,
            )

            active_adapters = []
            active_weights  = []

            # Carica LoRA 1
            if lora_name:
                lora_path = os.path.join("lora", f"{lora_name}.safetensors")
                try:
                    print(f"Caricamento LoRA1: {lora_name}")
                    load_lora_smart(pipe, lora_path, adapter_name='lora1', weight=0.8)
                    active_adapters.append('lora1')
                    active_weights.append(0.8)
                except Exception as e:
                    print(f"❌ LoRA1 fallita del tutto: {e}")

            # Carica LoRA 2
            if lora_name2:
                lora_path2 = os.path.join("lora", f"{lora_name2}.safetensors")
                try:
                    print(f"Caricamento LoRA2: {lora_name2}")
                    load_lora_smart(pipe, lora_path2, adapter_name='lora2', weight=0.6)
                    active_adapters.append('lora2')
                    active_weights.append(0.6)
                except Exception as e:
                    print(f"❌ LoRA2 fallita del tutto: {e}")

            # ── Fuse + unload adapter prima della quantizzazione ─────────────
            if len(active_adapters) > 1:
                pipe.set_adapters(active_adapters, adapter_weights=active_weights)
                print(f"✅ Adapter combinati: {active_adapters} con pesi {active_weights}")
                try:
                    pipe.fuse_lora(adapter_names=active_adapters, lora_scale=1.0)
                    pipe.unload_lora_weights()
                    print("✅ LoRA fuse completato, adapter rimossi")
                except Exception as e:
                    print(f"⚠️ fuse_lora fallito ({e}), si procede senza fuse")

            elif len(active_adapters) == 1:
                pipe.set_adapters(active_adapters[0], adapter_weights=active_weights[0])
                try:
                    pipe.fuse_lora(lora_scale=active_weights[0])
                    pipe.unload_lora_weights()
                    print("✅ LoRA fuse completato")
                except Exception as e:
                    print(f"⚠️ fuse_lora fallito ({e}), si procede senza fuse")

            # ── Quantizzazione ───────────────────────────────────────────────
            print("Quantizzazione transformer...")
            quantize(pipe.transformer, weights=qfloat8)
            freeze(pipe.transformer)

            if hasattr(pipe, 'text_encoder') and pipe.text_encoder is not None:
                print("Quantizzazione text encoder...")
                quantize(pipe.text_encoder, weights=qfloat8)
                freeze(pipe.text_encoder)

            # ── Ottimizzazioni memoria ───────────────────────────────────────
            print("Ottimizzazioni memoria...")
            pipe.enable_model_cpu_offload()
            pipe.enable_attention_slicing()
            pipe.vae.enable_slicing()
            pipe.vae.enable_tiling()
            
        # ── Generazione ─────────────────────────────────────────────────────
        # ⛔ Check stop PRIMA di generare
        if stop:
            print("⛔ Generazione interrotta dall'utente")
            break

        try:
            prompt_en = GoogleTranslator(source='it', target='en').translate(prompt_testo)
            image_input = None
            if reference_images:
                image_input = reference_images[0] if len(reference_images) == 1 else reference_images

            print(f"Prompt ITA:   {prompt_testo}")
            print(f"Prompt ENG:   {prompt_en}")
            print(f"Ref images:   {len(reference_images)}")
            print(f"LoRA1 attivo: {lora_name  or 'nessuno'}")
            print(f"LoRA2 attivo: {lora_name2 or 'nessuno'}")

            pipe_kwargs = {
                "prompt":              prompt_en,
                "height":              height,
                "width":               width,
                "guidance_scale":      1.0,
                "num_inference_steps": num_steps,
                "generator":           torch.Generator(device=device).manual_seed(42),
            }

            if image_input is not None:
                pipe_kwargs["image"] = image_input

            output = pipe(**pipe_kwargs).images[0]

            label = item["label"].replace(" ", "_")

            # ── Nome immagine di input ───────────────────────────────────────
            img_name = ""
            for part in parts[1:]:
                part_s = part.strip()
                if any(part_s.startswith(f'path{n}:') for n in range(1, 5)):
                    path_val = part_s.split(':', 1)[1].strip()
                    if path_val and os.path.exists(path_val):
                        img_name = os.path.splitext(os.path.basename(path_val))[0]
                        break

            # fallback: prima canvas con image_path
            if not img_name:
                if reference_images and canvases and hasattr(canvases[0], 'image_path'):
                    img_name = os.path.splitext(os.path.basename(canvases[0].image_path))[0]

            # ── Costruzione nome file ────────────────────────────────────────
            lora_part  = lora_name  if lora_name  else ""
            lora_part2 = lora_name2 if lora_name2 else ""

            name_parts = [p for p in [label, img_name, lora_part, lora_part2] if p]
            base_name  = ",".join(name_parts)

            dir_out = "out_image"
            os.makedirs(dir_out, exist_ok=True)

            # ── Anti-sovrascrittura con contatore ────────────────────────────
            out_name = os.path.join(dir_out, f"{base_name}.jpg")
            if os.path.exists(out_name):
                counter = 1
                while os.path.exists(os.path.join(dir_out, f"{base_name}_{counter}.jpg")):
                    counter += 1
                out_name = os.path.join(dir_out, f"{base_name}_{counter}.jpg")

            output.save(out_name)
            print(f"✅ Immagine salvata: {out_name}")

        except Exception as e:
            print(f"❌ Errore generazione {i+1}: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET STRUMENTI
# ═══════════════════════════════════════════════════════════════════════════════
import threading as t
# Con questo:
def avvia_flux2():
    global stop
    stop = False  # reset stop ad ogni nuova generazione
    t.Thread(target=flux2, daemon=True).start()

genera = tk.Button(strumenti, text='Genera Immagine', bg='light blue', command=avvia_flux2)
genera.grid(row=1, column=0, padx=10, pady=10)

tk.Label(strumenti, text='Steps').grid(row=0, column=1, padx=10, pady=5)
steps = tk.Scale(strumenti, from_=1, to=50, resolution=1, orient='horizontal')
steps.set(8)
steps.grid(row=1, column=1)

risoluzioni = ['512x512', '768x768', '1024x1024', '1280x720', '1920x1080', '2048x1080']
tk.Label(strumenti, text='Risoluzione').grid(row=0, column=2, padx=10, pady=5)
risoluzione = ttk.Combobox(strumenti, values=risoluzioni)
risoluzione.set('1024x1024')
risoluzione.grid(row=1, column=2)

tk.Label(strumenti, text='Model').grid(row=0, column=3, padx=10, pady=5)
model = ttk.Combobox(strumenti, values=['Flux2K_4B', 'Flux2K_9B'])
model.set('Flux2K_9B')
model.grid(row=1, column=3)

tk.Label(strumenti, text='Lora').grid(row=0, column=4, padx=10, pady=5)
model_lora = ttk.Combobox(strumenti, values=[])
model_lora.grid(row=1, column=4)
model_lora.bind('<Button-1>', load_lora)
model_lora.bind('<<ComboboxSelected>>', select_lora)
load_lora()

image_prompt = tk.Button(strumenti, text='Image Prompt', bg='light yellow', command=load_image_prompt)
image_prompt.grid(row=1, column=5, padx=10, pady=10)
#interrompi generazione immagini nel ciclo for con tasto k
def on_key():
    global stop,stop_generate,window
    if stop == False:
        stop=True
    print(f"⛔ Stop richiesto {stop}")
    stop_generate.config(bg='red')
    window.update_idletasks()

stop_generate = tk.Button(strumenti, text='Stop generate',bg='green',command=on_key)
stop_generate.grid(row=1, column=6, padx=5)

def f_design():
    t.Thread(target=lambda: os.system("python design.py"), daemon=True).start()

Design = tk.Button(strumenti, text='Design', bg='cyan', command=f_design)
Design.grid(row=1, column=7, padx=5)

new_form_list = None

import tkinter as tk

def f_list():
    import os
    global new_form_list
    print("Lista fotogrammi chiave")
    new_form_list = tk.Toplevel()
    new_form_list.title("Lista Frames")
    new_form_list.geometry("480x750")
    new_form_list.config(background='gray')
    new_form_list.resizable(False, False)
    new_form_list.lift()

    new_form_list.grid_columnconfigure(0, weight=1)
    new_form_list.grid_columnconfigure(1, weight=0)

    # ── RIGA 0: Frame lista + spinbox + scrollbar ──────────────────────────
    frame_superiore = tk.Frame(new_form_list, background='gray')
    frame_superiore.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=(5, 0))

    frame_lista = tk.Frame(frame_superiore, background='gray')
    frame_lista.grid(row=0, column=0, sticky="nw")

    frame_contatori = tk.Frame(frame_superiore, background='gray')
    frame_contatori.grid(row=0, column=1, sticky="nse")

    scrollbar_y = tk.Scrollbar(frame_superiore, orient="vertical")
    scrollbar_y.grid(row=0, column=2, sticky="ns")

    lista_keyframe = tk.Listbox(
        frame_lista, width=35, height=30,
        yscrollcommand=scrollbar_y.set,
        selectmode=tk.SINGLE
    )
    lista_keyframe.grid(row=0, column=0, sticky="nsw")
    scrollbar_y.config(command=lista_keyframe.yview)

    contatori_clips = {}

    lista_keyframe.delete(0, tk.END)
    path_dir = "./out_image"
    try:
        files = sorted(os.listdir(path_dir))
        for key in files:
            if key.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                basefile = os.path.basename(key)
                lista_keyframe.insert(tk.END, basefile)
                new_contatore = tk.Spinbox(frame_contatori, from_=1, to=3, width=5)
                contatori_clips[basefile] = new_contatore
    except FileNotFoundError:
        lista_keyframe.insert(tk.END, "Nessun file trovato.")
    
    def aggiorna_spinbox_posizioni():
        """Ridisegna tutti gli spinbox in base all'ordine attuale della listbox."""
        for bf, spinbox in contatori_clips.items():
            spinbox.grid_forget()
        for i in range(lista_keyframe.size()):
            bf = lista_keyframe.get(i)
            if bf in contatori_clips:
                contatori_clips[bf].grid(row=i, column=0, padx=2, pady=1, sticky="ew")

    # Posiziona subito gli spinbox all'avvio
    aggiorna_spinbox_posizioni()

    # ── RIGA 1: Textbox separata, sotto la listbox ─────────────────────────
    frame_testo = tk.Frame(new_form_list, background='gray')
    frame_testo.grid(row=1, column=0, sticky="ew", padx=5, pady=(6, 5))

    text = tk.Text(frame_testo, width=42, height=7)
    text.grid(row=0, column=0, sticky="w")

    # ── Prompt map: chiave = nameout, valore = prompt default ─────────────
    prompt_map = {
        "Allat_donna": (
            "due donne bellissime in una scena erotica di allattamento lesbico, una donna mora alta in piedi con seni grandi e pieni, l'altra donna bionda in ginocchio che le succhia avidamente il capezzolo, "
            "lingua che lecca ritmicamente e succhia il capezzolo con passione, bocca aperta e lingua visibile, "
            "espressione di intenso piacere sul viso della donna in piedi, occhi semi-chiusi, bocca socchiusa, "
            "donna bionda con espressione estatica e sottomessa, "
            "umori brillanti sulla pelle, saliva visibile, capezzoli turgidi e lucidi, "
            "luce calda e intima da camera da letto, atmosfera sensuale, "
            "close-up sul viso e sul seno, messa a fuoco anche sul dildo inserito nell'ano della donna in piedi, "
            "dettagli realistici, pelle lucida, qualità ultra dettagliata, 8k"
        ),

        "close_up_pomp_late": (
            "close-up laterale di pompino, bellissima donna bionda con lunghi capelli mossi e trucco elegante, "
            "in ginocchio che succhia un grosso cazzo spesso e venoso da lato, "
            "testa leggermente inclinata all'indietro, bocca aperta con labbra carnose avvolte intorno al glande, "
            "lingua visibile che lecca sotto l'asta, sguardo sensuale verso l'alto verso l'uomo, "
            "espressione sottomessa e arrapata, seni grandi e naturali in primo piano, "
            "donna completamente nuda dalla vita in su, uomo muscoloso parzialmente visibile, "
            "camera da letto luminosa con lenzuola bianche e pianta sullo sfondo, luce naturale morbida, "
            "dettagli realistici di saliva lucida sul cazzo e sulle labbra, vene pronunciate, pelle liscia, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "pompino_laterale": (
            "scena erotica di pompino laterale, una bellissima donna mora con capelli lunghi in ginocchio che fa un pompino a un uomo muscoloso in piedi, "
            "vista di profilo e tre quarti, la donna ha la bocca aperta e la lingua fuori mentre lecca e succhia un grosso cazzo spesso e venoso, "
            "espressione sensuale e sottomessa della donna, sguardo verso l'alto verso l'uomo, "
            "mano dell'uomo che tiene la testa della donna, "
            "donna completamente nuda con seni grandi e naturali, corpo tonico, "
            "uomo atletico e muscoloso, addominali definiti, peli pubici visibili, "
            "posizione in camera da letto, luce calda e morbida, atmosfera intima, "
            "dettagli realistici di saliva sulla bocca e sul cazzo lucido, vene pronunciate, "
            "qualità fotorealistica, pelle dettagliata, 8k, masterpiece, sharp focus"
        ),

        "pompino_POV": (
            "POV blowjob, bellissima donna raffinata con rossetto rosso brillante che fa un pompino lento e sensuale, "
            "labbra perfette avvolte intorno al cazzo, occhi che guardano in alto con desiderio, "
            "espressione provocante, capelli scuri raccolti, orecchini eleganti, camicetta bianca in pizzo trasparente, "
            "luce calda naturale da finestra, saliva lucida sulle labbra, atmosfera intima ed erotica, fotorealistico"
        ),

        "pomp_rovescio": (
            "bella donna sdraiata supina che fa un pompino rovescio a un uomo sopra di lei, posizione mounted fellatio, "
            "testa rovesciata all'indietro, bocca spalancata che accoglie un grosso cazzo, lingua visibile, "
            "sguardo sensuale verso l'alto, seni prosperosi con body di catene argentate, luce morbida e calda, "
            "saliva lucida, atmosfera intima e dominante, fotorealistico, dettagli ultra realistici, 8k"
        ),

        "Doggystyle_anal": (
            "scena erotica di spitroast con penetrazione anale, bellissima donna mora con lingerie nera sexy a quattro zampe su una panca di legno, "
            "un uomo muscoloso la penetra profondamente nel culo da dietro con un grosso cazzo, "
            "mentre un altro uomo davanti a lei le infila il cazzo in bocca, pompino profondo, "
            "espressione di piacere intenso, bocca spalancata intorno al cazzo, mano che tiene l'asta, "
            "culo rotondo e sodo, ano dilatato intorno al cazzo, schiena inarcata, "
            "dettagli realistici di doppia penetrazione (anale + orale), saliva che cola, umori lucidi, "
            "atmosfera intensa e perversa, luce chiara di studio, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "Anal_lei_sopra_2": (
            "scena erotica intensa di anal cowgirl / full nelson anal, splendida bionda nuda con seni grandi seduta sopra un uomo, "
            "gambe spalancate e sollevate alte tenute dalle mani forti dell'uomo, "
            "grosso cazzo che penetra profondamente nel suo culo, figa visibile sopra il cazzo, "
            "espressione di piacere estremo e sorriso arrapato, bocca aperta, sguardo verso la camera, "
            "corpo lucido di sudore, dettagli estremi di dilatazione anale, vene sul cazzo, ano stretto intorno all'asta, "
            "atmosfera calda e selvaggia di camera da letto, fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "Anal_lei_sopra": (
            "scena erotica di penetrazione anale con donna sopra, bellissima donna bionda con capelli lunghi e lingerie bianca di pizzo, "
            "accovacciata sopra un uomo muscoloso che la tiene con forza per le gambe alzate in posizione full nelson, "
            "grosso cazzo spesso che penetra profondamente nel suo buco del culo dilatato, "
            "espressione di intenso piacere e sforzo, occhi socchiusi, bocca spalancata in un gemito, viso arrossato, "
            "gambe tese e sollevate in alto, mani dell'uomo che stringono forte le sue cosce, "
            "dettagli realistici di ano dilatato intorno al cazzo, umori lucidi, pelle sudata, "
            "camera da letto intima con luce calda, fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "DP_Frontale": (
            "scena erotica di doppia penetrazione frontale (vaginale + anale), bellissima donna bionda nuda sdraiata tra due uomini muscolosi, "
            "un uomo sotto di lei la penetra nella figa mentre l'altro uomo la penetra nel culo contemporaneamente, "
            "gambe della donna spalancate e sollevate, doppia penetrazione profonda visibile, "
            "espressione di piacere intenso e sopraffatto sul viso di lei, bocca aperta, occhi spalancati, "
            "uomini che la tengono forte per le cosce e i fianchi, corpi sudati e tesi, "
            "dettagli ultra realistici di figa e ano dilatati intorno ai due grossi cazzi, umori lucidi che colano, "
            "atmosfera sensuale e intensa, luce calda drammatica, sfondo surreale con nuvole e cielo, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "DP_cowgirl": (
            "scena erotica di doppia penetrazione in cowgirl, bellissima donna bionda nuda a cavalcioni su un uomo sdraiato, "
            "mentre un secondo uomo muscoloso la penetra nel culo da dietro, "
            "posizione DP cowgirl con doppia penetrazione (vaginale + anale) profonda, "
            "donna con espressione di piacere estremo, bocca aperta, sguardo verso la camera, "
            "uomo sotto che le tiene i fianchi, uomo dietro che la scopa con forza, "
            "seni grandi che ballano, corpo sudato e lucido, dettagli estremi di figa e ano dilatati intorno ai cazzi, "
            "umori brillanti, vene sui cazzi, atmosfera selvaggia di camera da letto, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "lsb_lickpussy_69": (
            "scena erotica lesbica in posizione 69, due bellissime donne nude sul letto, "
            "una donna sdraiata sulla schiena mentre l'altra è sopra di lei a testa in giù, "
            "entrambe si leccano la figa con passione reciproca, "
            "lingua visibile che lecca il clitoride e penetra tra le labbra bagnate, bocca aperta sulla vulva, "
            "espressioni di intenso piacere, una con lingua fuori e sguardo eccitato, l'altra con viso affondato tra le cosce, "
            "mani che afferrano i glutei e le cosce dell'altra, corpi intrecciati sensualmente, "
            "fighe rasate e lucide di saliva e umori, dettagli bagnati e brillanti, "
            "atmosfera intima di camera da letto con lenzuola bianche, luce calda e morbida, "
            "corpi tonici, seni grandi, capelli lunghi (una bionda e una mora), "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "Blowbang_sperma": (
            "scena blowbang con bukkake finale, bellissima ragazza con capelli castani (leggermente più corti e arruffati) completamente ricoperta di sperma, "
            "faccia, occhi, guance, naso, mento, collo e seni grandi inondati di sperma denso e bianco che cola abbondantemente, "
            "espressione sottomessa ma arrapata, occhi aperti che guardano verso la camera, bocca semiaperta con residui di cum, "
            "diversi cazzi ancora duri puntati verso di lei da tutte le direzioni, alcuni che toccano il viso e i seni sporchi di sperma, "
            "mani maschili visibili, atmosfera di gangbang estremo dopo il bukkake, "
            "sperma denso e lucido con fili e gocce che colano sul corpo, jeans abbassati, "
            "dettagli ultra realistici di texture dello sperma, pelle bagnata e lucida, vene sui cazzi, fotorealistico, 8k, masterpiece, sharp focus"
        ),

        "Blowbang": (
            "scena blowbang intensa durante l'atto, bellissima ragazza con capelli castani lunghi al centro di un gruppo di uomini, "
            "vista dall'alto, circondata da molti cazzi duri e grossi di diverse etnie che puntano verso il suo viso e bocca, "
            "bocca spalancata con lingua fuori, espressione sottomessa ed eccitata, occhi semi-chiusi o rivolti verso l'alto, "
            "alcuni cazzi che sfregano sulle guance, labbra e fronte, mani maschili che le tengono la testa e i capelli, "
            "donna con top nero di pizzo sexy, seni parzialmente scoperti, atmosfera di gangbang perversa e intensa, "
            "luce drammatica calda dall'alto, dettagli realistici di vene, saliva sulla lingua e sulle labbra, pelle lucida, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "side_rimming": (
            "rimming estremo e profondo, bellissima bionda che infila la lingua dentro il buco del culo dilatato di una donna, "
            "lingua visibile che penetra nel canale anale aperto, lecca e scava all'interno, "
            "saliva densa che cola copiosamente dall'ano sulla lingua e sul mento, "
            "espressione da troia affamata, bocca spalancata, culo grosso premuto contro il viso, "
            "dettagli ultra realistici di ano contratto e bagnato, texture della lingua e saliva viscosa, "
            "luce calda, fotorealistico, 8k"
        ),

        "Ass_side": (
            "scena erotica di presentazione del culo da lato, bellissima donna mora con capelli lunghi sdraiata di lato sul letto, "
            "guarda indietro verso la camera con espressione seducente e provocante, "
            "con le mani separa bene i glutei sodi e rotondi, "
            "una gamba alzata e piegata verso l'alto per mostrare meglio, "
            "dilata con le dita la figa rasata e il buco del culo ben visibile, "
            "close-up sul sedere, figa e ano esposti in dettaglio, "
            "pelle liscia e lucida, umori brillanti sulle labbra della figa, "
            "indossa solo un top nero sexy, corpo tonico e sensuale, "
            "luce morbida e calda di studio, atmosfera molto erotica, "
            "dettagli ultra realistici di texture della pelle, ano e figa dilatati, fotorealistico, 8k, masterpiece, sharp focus"
        ),

        "lei_sopra_2": (
            "scena erotica intensa di donna sopra in cowgirl, bellissima donna mora con lingerie nera di pizzo che cavalca con passione, "
            "gambe alzate e spalancate tenute dalle mani dell'uomo, figa che prende profondamente il grosso cazzo, "
            "espressione di piacere estremo, occhi stretti e bocca spalancata in un gemito, viso arrossato, "
            "uomo che le tiene forte le cosce e i glutei, penetrazione profonda visibile, "
            "seni grandi compressi nel top di pizzo, atmosfera calda e selvaggia di camera da letto, "
            "dettagli realistici di umori lucidi, vene sul cazzo, pelle sudata, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "lei_sopra": (
            "scena erotica di penetrazione con donna sopra in posizione cowgirl squat, bellissima donna mora con lunghi capelli che cavalca un uomo sdraiato sul letto, "
            "è accovacciata sopra di lui con le gambe piegate, figa che ingoia profondamente un grosso cazzo spesso, "
            "espressione di piacere intenso e sorpresa, occhi spalancati che guardano verso la camera, bocca aperta, "
            "seni grandi nudi che ballano, mani appoggiate sul letto, corpo tonico e sudato, "
            "vista dal basso verso l'alto, dettagli realistici di penetrazione profonda, labbra della figa tese intorno al cazzo, "
            "camera da letto intima con lenzuola bianche, luce calda, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "Anal_pecora": (
            "scena erotica di penetrazione anale a quattro zampe, bellissima donna mora con capelli lunghi in posizione doggy style sul letto, "
            "uomo muscoloso dietro di lei che la penetra profondamente nel culo con un grosso cazzo spesso e venoso, "
            "culo rotondo e sodo alzato, schiena inarcata, ano dilatato intorno all'asta del cazzo, "
            "espressione di piacere intenso sul viso di lei, bocca aperta in un gemito, occhi socchiusi, "
            "mani dell'uomo che stringono i fianchi o i glutei di lei, "
            "dettagli realistici di penetrazione anale profonda, ano stretto e lucido, umori e saliva visibili, "
            "camera da letto intima con lenzuola bianche, luce calda e morbida, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "Anal_rovesciata": (
            "scena erotica estrema di penetrazione anale rovesciata / piledriver, bellissima donna con capelli scuri sdraiata sulla schiena con le gambe alzate e piegate sopra la testa, "
            "uomo sopra di lei che la penetra profondamente nel culo, posizione molto profonda e intensa, "
            "ano dilatato che accoglie tutto il grosso cazzo, figa visibile sopra, "
            "espressione di piacere estremo e sottomissione sul viso di lei, bocca aperta, sguardo verso l'alto, "
            "uomo che le tiene le gambe e i glutei, corpo della donna piegato in due, "
            "dettagli ultra realistici di dilatazione anale profonda, vene sul cazzo, pelle sudata e lucida, "
            "atmosfera perversa e intensa di camera da letto, luce calda, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "Side_Anal": (
            "scena erotica di penetrazione anale laterale, bellissima donna mora con capelli lunghi sdraiata di lato sul letto, "
            "uomo muscoloso dietro di lei che la penetra nel culo con un grosso cazzo spesso, "
            "posizione spooning anal, una gamba leggermente alzata, "
            "donna che guarda indietro verso la camera con espressione sensuale e arrapata, "
            "mano con unghie rosse appoggiata sul letto, seni grandi nudi in vista, "
            "dettagli realistici di ano dilatato intorno al cazzo, penetrazione profonda, pelle lucida, "
            "camera da letto intima con lenzuola bianche, luce calda e morbida, "
            "fotorealistico, ultra dettagliato, 8k, masterpiece, sharp focus"
        ),

        "Fisting_lesbo": (
            "fisting vaginale intenso, bellissima dottoressa con camice bianco che spinge tutta la mano dentro la figa dilatata di una paziente nuda sul letto, "
            "vagina spalancata che accoglie il pugno, polso profondo dentro, espressione di piacere estremo sul viso della donna fisted, occhi rivolti all'insù, "
            "figa gonfia e bagnatissima, umori che colano, seni grandi nudi, corpo lucido di sudore, "
            "dettagli estremi di dilatazione, texture della pelle e mano dentro la fica, luce calda da camera da letto, fotorealistico, 8k"
        ),

        "Missionaria": (
            "missionary intenso, splendida bionda nuda sdraiata sul letto con gambe larghe e piegate, "
            "grosso cazzo che la scopa profondamente in figa, close-up sulla penetrazione, "
            "figa bagnata e dilatata che stringe l'asta, espressione arrapata con bocca aperta, "
            "seni che ballano, mano sul ventre, corpo sudato, dettagli estremi di vene del cazzo e umori, "
            "luce calda da camera da letto, fotorealistico, 8k"
        ),

        "sperma_figa": (
            "creampie intenso con sperma che sgocciola dalla figa, close-up estremo sulla vagina aperta di una bellissima donna nuda con gambe spalancate, "
            "abbondante sperma denso e bianco che cola copiosamente fuori dalla figa gonfia, fili viscosi che pendono e gocciolano sulle lenzuola, "
            "mani con unghie curate che tengono le cosce aperte per esporre il creampie, "
            "dettagli estremi di texture dello sperma, labbra vaginali bagnate e ano visibile, pelle lucida, "
            "espressione arrapata sul viso, fotorealistico, 8k, ultra dettagliato"
        ),

        "Sperma_in_Bocca": (
            "close-up di ragazza che mastica e gioca con una grossa quantità di sperma in bocca, bocca aperta, lingua che mescola il cum, "
            "sta per ingoiare, gola gonfia, espressione intensa e arrapata, cum che cola ovunque su viso, mento e tette, "
            "unghie rosse brillanti, capelli castani spettinati, lingerie nera di pizzo, dettagli estremi di sperma viscoso e fili, 8k, ultra realistico"
        ),

        "lbs_lickpussy": (
            "sensuale scena lesbica di cunnilingus, bellissima donna sdraiata che riceve una leccata di figa appassionata da un'altra donna, "
            "lingua lenta e profonda, espressione di puro piacere, atmosfera intima e romantica, luce soffusa, dettagli realistici, 8k"
        ),

        "close_up_kiss": (
            "Primo piano dei volti e delle labbra di due donne mentre si baciano "
            "appassionatamente alla francese con la lingua, "
            "dettagli realistici ed emozionanti, sfondo sfocato per enfatizzare "
            "l'intensità del bacio, luci morbide e colori caldi."
        ),

        "gambe_aperte": (
            "una donna tatuata con capelli neri sdraiata sulla schiena, gambe sollevate alte e spalancate in aria in posizione butterfly, "
            "mani che tirano le cosce aperte, primo piano estremo su figa e ano dilatati e aperti, vagina gaping, dettagli espliciti e bagnati, "
            "luce calda da camera da letto, realistico"
        ),

        "dildo Anal 2": (
            "una donna accovacciata o in ginocchio su un letto, "
            "penetrazione anale profonda e intensa con un grosso dildo, "
            "muove ritmicamente il bacino su e giù facendo entrare ed uscire il dildo dall'ano, "
            "ano ben dilatato e aperto durante il movimento, dettagli estremi e realistici, "
            "espressione di piacere intenso, umori brillanti, luce calda da camera da letto, "
            "messa a fuoco su dildo nel ano e messa a fuoco sul viso"
        ),

        "dildo Anal": (
            "una ragazza distesa sul letto con le gambe divaricate e alzate in area "
            "un grosso oggetto nero inserito nel ano che si muove avanti e indietro, "
            "muove ritmicamente su e giù facendo entrare ed uscire il dildo dall'ano, "
            "ano ben dilatato e aperto durante il movimento, dettagli estremi e realistici, "
            "espressione di piacere intenso, umori brillanti, luce calda da camera da letto, "
            "messa a fuoco su dildo nel ano e messa a fuoco sul viso"
        ),

        "posa_pecora": (
            "una ragazza di spalle ,sedere in primo piano, a carponi che separa i gludei con le mani e dilata ano "
            "dilatazione e chiusura ano, "
            "muove ritmicamente della dilatazione anale"
            "ano ben dilatato e aperto durante il movimento, dettagli estremi e realistici, "
            "espressione di piacere intenso, umori brillanti, luce calda da camera da letto, "
            "messa a fuoco su dildo nel ano e messa a fuoco sul viso"
        ),

        "sedute": (
            "Due donne si accarezzano teneramente e si baciano sulle labbra, "
            "scena romantica e passionale su un letto, sguardi emozionati e gesti affettuosi, "
            "luce naturale, atmosfera calda e coinvolgente."
        ),

        "in_piedi": (
            "Due donne si siedono delicatamente su un grande letto matrimoniale, "
            "l'atmosfera è intima e accogliente, luce soffusa, "
            "attenzione ai dettagli nell'espressione dei volti e nella cura dei vestiti."
        ),

        "kiss": (
            "Due donne si baciano appassionatamente alla francese, scena romantica "
            "ed intensa di passione, ambientazione delicata, "
            "sensazione di intimità e rispetto tra le protagoniste."
        ),

        "Woman_to_TransWo": (
            "donna trans bionda sexy nuda che si masturba intensamente, mano destra che stringe forte il suo grosso cazzo eretto e lo pompa, "
            "movimento di masturbazione visibile, pollice che accarezza il glande, "
            "espressione di piacere, bocca aperta, seni grandi che ballano leggermente, "
            "cazzo spesso e venoso lucido di liquido preseminale, dettagli estremi di mano e pene, "
            "corpo femminile attraente, vita stretta, fianchi larghi, fotorealistico, 8k"
        ),
    }

    prompts_correnti  = {}   # {basefile: testo_prompt corrente/modificato}
    nameout_correnti  = {}   # {basefile: chiave trovata in prompt_map}
    elemento_corrente = {"basefile": None}

    def get_prompt_default(nomefile):
        """Cerca la chiave nel nome file in modo case-insensitive e più flessibile."""
        nomefile_lower = nomefile.lower().replace(" ", "_").replace("-", "_")
        
        for chiave, testo in prompt_map.items():
            chiave_lower = chiave.lower()
            if chiave_lower in nomefile_lower or chiave_lower.replace("_", "") in nomefile_lower:
                return testo, chiave
        
        # Fallback
        return "Scena non riconosciuta, descrizione generica.", "video_generico"

    def salva_testo_corrente():
        """Salva il testo della textbox nel dizionario prima di cambiare elemento."""
        bf = elemento_corrente["basefile"]
        if bf is not None:
            prompts_correnti[bf] = text.get('1.0', tk.END).rstrip('\n')

    def vedi_prompt(event):
        sel = lista_keyframe.curselection()
        if not sel:
            return

        basefile = lista_keyframe.get(sel[0])
        nomefile = basefile.lower().replace(" ", "")

        # Salva il testo corrente prima di cambiare elemento
        salva_testo_corrente()

        # Se prima volta su questo file, inizializza dal default
        if basefile not in prompts_correnti:
            prompt_def, nameout_def    = get_prompt_default(nomefile)
            prompts_correnti[basefile] = prompt_def
            nameout_correnti[basefile] = nameout_def

        elemento_corrente["basefile"] = basefile

        # Leggi numero clips dallo spinbox
        numero_clips = 1
        if basefile in contatori_clips:
            try:
                numero_clips = int(contatori_clips[basefile].get())
            except ValueError:
                numero_clips = 1

        print(f"File: {nomefile} | NameOut: {nameout_correnti[basefile]} | Clips: {numero_clips}")

        text.delete('1.0', tk.END)
        text.insert('1.0', prompts_correnti[basefile])

    lista_keyframe.bind('<<ListboxSelect>>', vedi_prompt)

    # ── Variabili checkbox ─────────────────────────────────────────────────
    var_audio   = tk.IntVar(value=0)
    var_upscale = tk.IntVar(value=0)

    # ── Genera Video ───────────────────────────────────────────────────────
    def f_genera_video():
        salva_testo_corrente()

        WITH_AUDIO   = bool(var_audio.get())
        Upscale_flag = bool(var_upscale.get())

        lista_files   = [lista_keyframe.get(i) for i in range(lista_keyframe.size())]
        lista_prompts = []
        lista_nameout = []
        lista_clips   = []

        for bf in lista_files:
            nomefile = bf.lower().replace(" ", "")
            if bf in prompts_correnti:
                prompt  = prompts_correnti[bf]
                nameout = nameout_correnti.get(bf, "video_generico")
            else:
                prompt, nameout = get_prompt_default(nomefile)
            clips = 1
            if bf in contatori_clips:
                try:
                    clips = int(contatori_clips[bf].get())
                except ValueError:
                    clips = 1
            lista_prompts.append(prompt)
            lista_nameout.append(nameout)
            lista_clips.append(str(clips))

        files_arg   = "|".join(lista_files)
        prompts_arg = "|".join(lista_prompts)
        nameout_arg = "|".join(lista_nameout)
        clips_arg   = "|".join(lista_clips)

        cmd = (
            f'python ltx2.py '
            f'--files "{files_arg}" '
            f'--prompts "{prompts_arg}" '
            f'--nameout "{nameout_arg}" '
            f'--clips "{clips_arg}" '
            f'--audio {1 if WITH_AUDIO else 0} '
            f'--upscale {1 if Upscale_flag else 0}'
        )
        print(f"Comando: {cmd}")
        os.system(cmd)

    # ── COLONNA 1: Bottoni ─────────────────────────────────────────────────
    frame_b = tk.Frame(new_form_list, background='gray')
    frame_b.grid(row=0, column=1, padx=8, pady=5, sticky="n")

    def f_su():
        sel = lista_keyframe.curselection()
        if not sel or sel[0] == 0:
            return
        index = sel[0]
        value = lista_keyframe.get(index)
        lista_keyframe.delete(index)
        lista_keyframe.insert(index - 1, value)
        lista_keyframe.selection_set(index - 1)
        lista_keyframe.see(index - 1)
        aggiorna_spinbox_posizioni()   # ← ricalcola tutto

    def f_giu():
        sel = lista_keyframe.curselection()
        if not sel or sel[0] == lista_keyframe.size() - 1:
            return
        index = sel[0]
        value = lista_keyframe.get(index)
        lista_keyframe.delete(index)
        lista_keyframe.insert(index + 1, value)
        lista_keyframe.selection_set(index + 1)
        lista_keyframe.see(index + 1)
        aggiorna_spinbox_posizioni()   # ← ricalcola tutto

    def f_elimina():
        sel = lista_keyframe.curselection()
        if not sel:
            return
        index = sel[0]
        value = lista_keyframe.get(index)
        lista_keyframe.delete(index)
        if value in contatori_clips:
            contatori_clips[value].destroy()
            del contatori_clips[value]
        if value in prompts_correnti:
            del prompts_correnti[value]
        if value in nameout_correnti:
            del nameout_correnti[value]
        if elemento_corrente["basefile"] == value:
            elemento_corrente["basefile"] = None
            text.delete('1.0', tk.END)
        aggiorna_spinbox_posizioni()   # ← ricalcola tutto

    tk.Button(frame_b, text='Su',            width=10, command=f_su).grid(row=0, column=0, columnspan=2, pady=3)
    tk.Button(frame_b, text='Elimina',       width=10, command=f_elimina).grid(row=1, column=0, columnspan=2, pady=3)
    tk.Button(frame_b, text='Giu',           width=10, command=f_giu).grid(row=2, column=0, columnspan=2, pady=3)
    tk.Button(frame_b, text='Genera Videos', width=10, command=f_genera_video).grid(row=3, column=0, columnspan=2, pady=3)
    tk.Checkbutton(frame_b, text='Audio',   variable=var_audio,   bg='gray').grid(row=4, column=0, pady=3)
    tk.Checkbutton(frame_b, text='Upscale', variable=var_upscale, bg='gray').grid(row=4, column=1, pady=3)


list_key = tk.Button(strumenti, text='Lista begin Frames\nVideo', bg='violet', command=f_list)
list_key.grid(row=1, column=8, padx=5)

import tkinter as tk
from tkinter import filedialog
import subprocess
import os

def form_estraiaudio():
    new_form_audio = tk.Toplevel()
    new_form_audio.geometry("340x700")
    new_form_audio.resizable(False, False)
    new_form_audio.title("Estrai Audio/Video")

    video_path  = tk.StringVar()
    durata_sec  = [0]      # durata reale del video in secondi
    processo    = [None]

    # ── Titolo ───────────────────────────────────────────
    tk.Label(new_form_audio, text="Estrai Audio/Video",
             font=("Arial", 12, "bold")).pack(pady=(12, 4))

    # ── Carica video ─────────────────────────────────────
    def carica_video():
        path = filedialog.askopenfilename(
            title="Seleziona un video",
            filetypes=[("File MP4", "*.mp4"), ("Tutti i file", "*.*")]
        )
        if not path:
            return
        video_path.set(path)
        lbl_path.config(text=os.path.basename(path), fg="black")

        # Legge durata con ffprobe
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True
            )
            dur = float(result.stdout.strip())
        except Exception:
            dur = 600.0   # fallback 10 min se ffprobe non è disponibile

        durata_sec[0] = dur
        slider_inizio.config(to=dur)
        slider_fine.config(to=dur)
        slider_inizio.set(0)
        slider_fine.set(dur)
        aggiorna_labels()

        btn_play.config(state="normal")
        btn_stop.config(state="normal")
        btn_estrai_audio.config(state="normal")
        btn_estrai_video.config(state="normal")

    tk.Button(
        new_form_audio, text="📂  Carica video MP4",
        bg="fuchsia", fg="white", font=("Arial", 10, "bold"),
        width=24, command=carica_video
    ).pack(pady=(8, 2))

    lbl_path = tk.Label(new_form_audio, text="Nessun file selezionato",
                        fg="gray", font=("Arial", 8), wraplength=300)
    lbl_path.pack(pady=(0, 6))

    # ── Display video ─────────────────────────────────────
    canvas = tk.Canvas(new_form_audio, width=300, height=180,
                       bg="black", relief="sunken", bd=2)
    canvas.pack(pady=(0, 4))
    play_icon = canvas.create_text(150, 90, text="▶", fill="#555555",
                                   font=("Arial", 42))

    lbl_tempo = tk.Label(new_form_audio, text="00:00 / 00:00",
                         font=("Courier", 9), fg="#333333")
    lbl_tempo.pack()

    # ── Play / Stop ───────────────────────────────────────
    frame_ctrl = tk.Frame(new_form_audio)
    frame_ctrl.pack(pady=4)

    def apri_player():
        path = video_path.get()
        if not path:
            return
        if processo[0] and processo[0].poll() is None:
            processo[0].terminate()
        if os.name == "nt":
            processo[0] = subprocess.Popen(["start", "", path], shell=True)
        elif hasattr(os, "uname") and os.uname().sysname == "Darwin":
            processo[0] = subprocess.Popen(["open", path])
        else:
            for player in ["mpv", "vlc", "xdg-open"]:
                try:
                    processo[0] = subprocess.Popen([player, path])
                    break
                except FileNotFoundError:
                    continue
        canvas.itemconfig(play_icon, text="⏸", fill="#00cc44")
        lbl_tempo.config(text="▶ riproduzione in corso...")

    def ferma_player():
        if processo[0] and processo[0].poll() is None:
            processo[0].terminate()
        canvas.itemconfig(play_icon, text="▶", fill="#555555")
        lbl_tempo.config(text="00:00 / 00:00")

    btn_play = tk.Button(frame_ctrl, text="▶  Play", width=10,
                         bg="#222222", fg="white", font=("Arial", 10, "bold"),
                         state="disabled", command=apri_player)
    btn_play.grid(row=0, column=0, padx=6)

    btn_stop = tk.Button(frame_ctrl, text="■  Stop", width=10,
                         bg="#222222", fg="white", font=("Arial", 10, "bold"),
                         state="disabled", command=ferma_player)
    btn_stop.grid(row=0, column=1, padx=6)

    # ── Separatore ────────────────────────────────────────
    tk.Frame(new_form_audio, height=1, bg="#cccccc").pack(fill="x", padx=10, pady=8)

    # ══════════════════════════════════════════════════════
    # ── TIMELINE CON SEGNAPOSTO INIZIO / FINE ─────────────
    # ══════════════════════════════════════════════════════
    tk.Label(new_form_audio, text="Intervallo di estrazione",
             font=("Arial", 10, "bold")).pack()

    # ── Helper: secondi → "MM:SS" ─────────────────────────
    def fmt(sec):
        sec = int(sec)
        return f"{sec // 60:02d}-{sec % 60:02d}"

    # ── Barra visuale della selezione ─────────────────────
    canvas_tl = tk.Canvas(new_form_audio, width=300, height=28,
                          bg="#222222", relief="flat", bd=0,
                          highlightthickness=0)
    canvas_tl.pack(padx=20, pady=(6, 2))

    bar_x0, bar_x1, bar_y = 10, 290, 14   # coordinate barra

    # Sfondo grigio scuro
    canvas_tl.create_rectangle(bar_x0, bar_y - 4, bar_x1, bar_y + 4,
                                fill="#555555", outline="")
    # Zona selezionata (verde)
    rett_sel = canvas_tl.create_rectangle(bar_x0, bar_y - 4, bar_x1, bar_y + 4,
                                          fill="#00cc44", outline="")
    # Marcatori inizio (verde chiaro) e fine (arancio)
    mark_ini = canvas_tl.create_rectangle(bar_x0 - 3, bar_y - 9,
                                          bar_x0 + 3, bar_y + 9,
                                          fill="#00ee66", outline="white", width=1)
    mark_fin = canvas_tl.create_rectangle(bar_x1 - 3, bar_y - 9,
                                          bar_x1 + 3, bar_y + 9,
                                          fill="#ff8800", outline="white", width=1)

    def aggiorna_barra():
        dur = durata_sec[0] if durata_sec[0] > 0 else 1
        ini = slider_inizio.get()
        fin = slider_fine.get()
        lx = bar_x0 + (ini / dur) * (bar_x1 - bar_x0)
        rx = bar_x0 + (fin / dur) * (bar_x1 - bar_x0)
        canvas_tl.coords(rett_sel, lx, bar_y - 4, rx, bar_y + 4)
        canvas_tl.coords(mark_ini, lx - 3, bar_y - 9, lx + 3, bar_y + 9)
        canvas_tl.coords(mark_fin, rx - 3, bar_y - 9, rx + 3, bar_y + 9)

    # ── Slider INIZIO ─────────────────────────────────────
    frame_ini = tk.Frame(new_form_audio)
    frame_ini.pack(fill="x", padx=20, pady=(4, 0))

    tk.Label(frame_ini, text="🟢 Inizio:", font=("Arial", 9, "bold"),
             fg="#007733", width=8, anchor="w").pack(side="left")
    lbl_ini_val = tk.Label(frame_ini, text="00:00", font=("Courier", 9),
                           fg="#007733", width=7)
    lbl_ini_val.pack(side="right")

    slider_inizio = tk.Scale(
        new_form_audio, from_=0, to=600, orient="horizontal",
        length=300, showvalue=False, resolution=1,
        troughcolor="#004411", bg=new_form_audio.cget("bg"),
        highlightthickness=0, sliderlength=14, width=8,
        command=lambda v: aggiorna_labels()
    )
    slider_inizio.pack(padx=20)

    # ── Slider FINE ───────────────────────────────────────
    frame_fin = tk.Frame(new_form_audio)
    frame_fin.pack(fill="x", padx=20, pady=(4, 0))

    tk.Label(frame_fin, text="🟠 Fine:", font=("Arial", 9, "bold"),
             fg="#cc5500", width=8, anchor="w").pack(side="left")
    lbl_fin_val = tk.Label(frame_fin, text="00:00", font=("Courier", 9),
                           fg="#cc5500", width=7)
    lbl_fin_val.pack(side="right")

    slider_fine = tk.Scale(
        new_form_audio, from_=0, to=600, orient="horizontal",
        length=300, showvalue=False, resolution=1,
        troughcolor="#663300", bg=new_form_audio.cget("bg"),
        highlightthickness=0, sliderlength=14, width=8,
        command=lambda v: aggiorna_labels()
    )
    slider_fine.pack(padx=20)
    slider_fine.set(600)

    # Durata selezione
    lbl_durata_sel = tk.Label(new_form_audio, text="Durata selezione: 00:00",
                              font=("Arial", 8), fg="#555555")
    lbl_durata_sel.pack(pady=(2, 0))

    # ── Aggiorna tutte le label e la barra ────────────────
    def aggiorna_labels(*_):
        ini = slider_inizio.get()
        fin = slider_fine.get()
        # Forza: inizio non può superare fine
        if ini > fin:
            slider_inizio.set(fin)
            ini = fin
        lbl_ini_val.config(text=fmt(ini))
        lbl_fin_val.config(text=fmt(fin))
        delta = max(0, fin - ini)
        lbl_durata_sel.config(text=f"Durata selezione: {fmt(delta)}")
        aggiorna_barra()

    aggiorna_labels()

    # ── Bottoni manuale MM:SS ─────────────────────────────
    frame_man = tk.Frame(new_form_audio)
    frame_man.pack(pady=(6, 0))

    def set_manuale(slider, entry_m, entry_s):
        try:
            m = int(entry_m.get())
            s = int(entry_s.get())
            slider.set(m * 60 + s)
            aggiorna_labels()
        except ValueError:
            pass

    # Inizio manuale
    tk.Label(frame_man, text="Inizio:", font=("Arial", 8)).grid(row=0, column=0, padx=2)
    e_ini_m = tk.Entry(frame_man, width=3, font=("Courier", 9))
    e_ini_m.insert(0, "00")
    e_ini_m.grid(row=0, column=1)
    tk.Label(frame_man, text="m", font=("Arial", 8)).grid(row=0, column=2)
    e_ini_s = tk.Entry(frame_man, width=3, font=("Courier", 9))
    e_ini_s.insert(0, "00")
    e_ini_s.grid(row=0, column=3)
    tk.Label(frame_man, text="s", font=("Arial", 8)).grid(row=0, column=4)
    tk.Button(frame_man, text="✔", font=("Arial", 8), width=2,
              command=lambda: set_manuale(slider_inizio, e_ini_m, e_ini_s)
              ).grid(row=0, column=5, padx=4)

    # Fine manuale
    tk.Label(frame_man, text="Fine:", font=("Arial", 8)).grid(row=1, column=0, padx=2, pady=2)
    e_fin_m = tk.Entry(frame_man, width=3, font=("Courier", 9))
    e_fin_m.insert(0, "10")
    e_fin_m.grid(row=1, column=1)
    tk.Label(frame_man, text="m", font=("Arial", 8)).grid(row=1, column=2)
    e_fin_s = tk.Entry(frame_man, width=3, font=("Courier", 9))
    e_fin_s.insert(0, "00")
    e_fin_s.grid(row=1, column=3)
    tk.Label(frame_man, text="s", font=("Arial", 8)).grid(row=1, column=4)
    tk.Button(frame_man, text="✔", font=("Arial", 8), width=2,
              command=lambda: set_manuale(slider_fine, e_fin_m, e_fin_s)
              ).grid(row=1, column=5, padx=4)

    # ── Separatore ────────────────────────────────────────
    tk.Frame(new_form_audio, height=1, bg="#cccccc").pack(fill="x", padx=10, pady=8)

    # ── Estrazione ────────────────────────────────────────
    tk.Label(new_form_audio, text="Estrazione", font=("Arial", 10, "bold")).pack()

    def estrai(solo_audio: bool):
        path = video_path.get()
        if not path:
            return
        ini  = int(slider_inizio.get())
        fin  = int(slider_fine.get())
        dur  = fin - ini
        if dur <= 0:
            tk.messagebox.showwarning("Attenzione", "L'intervallo è vuoto!")
            return

        base = os.path.splitext(os.path.basename(path))[0]
        if solo_audio:
            out = get_unique_path("./", f"{base}_{fmt(ini)}-{fmt(fin)}", "audio", ext=".mp3")
            cmd = ["ffmpeg", "-ss", str(ini), "-i", path,
                   "-t", str(dur), "-vn", "-acodec", "mp3", out]
        else:
            out = get_unique_path("videos", f"{base}_{fmt(ini)}-{fmt(fin)}", "novideo", ext=".mp4")
            cmd = ["ffmpeg", "-ss", str(ini), "-i", path,
                   "-t", str(dur), "-an", "-c:v", "copy", out]

        try:
            subprocess.Popen(cmd)
            tk.messagebox.showinfo("Avviato", f"Estrazione avviata:\n{out}")
        except FileNotFoundError:
            tk.messagebox.showerror("Errore", "ffmpeg non trovato!\nInstallalo e riprova.")

    btn_estrai_audio = tk.Button(
        new_form_audio, text="🎵  Estrai Audio (MP3)",
        bg="#4a90d9", fg="white", width=24, font=("Arial", 9),
        state="disabled", command=lambda: estrai(solo_audio=True)
    )
    btn_estrai_audio.pack(pady=3)

    btn_estrai_video = tk.Button(
        new_form_audio, text="🎬  Estrai Video (no audio)",
        bg="#4a90d9", fg="white", width=24, font=("Arial", 9),
        state="disabled", command=lambda: estrai(solo_audio=False)
    )
    btn_estrai_video.pack(pady=3)

    # ── Chiusura pulita ───────────────────────────────────
    def on_close():
        ferma_player()
        new_form_audio.destroy()

    new_form_audio.protocol("WM_DELETE_WINDOW", on_close)


# ── Helper path univoco con estensione ────────────────────
def get_unique_path(folder: str, basename: str, suffix: str, ext: str = ".mp4") -> str:
    os.makedirs(folder, exist_ok=True)
    candidate = os.path.join(folder, f"{basename}_{suffix}{ext}")
    if not os.path.exists(candidate):
        return candidate
    idx = 2
    while True:
        candidate = os.path.join(folder, f"{basename}_{suffix}_{idx}{ext}")
        if not os.path.exists(candidate):
            return candidate
        idx += 1


estrai_audio_video = tk.Button(strumenti, text='Estrai\nAudio/Video',
                                bg='fuchsia', command=form_estraiaudio)
estrai_audio_video.grid(row=1, column=9, padx=5)

import threading as t
path_audio = None

def render_window():
    render_form = tk.Toplevel()
    render_form.title("Rendering")
    render_form.geometry("900x600")
    render_form.resizable(False, False)
    render_form.config(bg='gray')

    frame = tk.Canvas(render_form, width=512, height=512, bg='red', highlightthickness=0)
    frame.grid(row=0, column=0)

    lab_scale = tk.Label(render_form, text="frame 0")
    lab_scale.grid(row=1, column=0)

    def on_scale_change(val):
        lab_scale.config(text=f"frame {int(float(val))}")

    scale_var = tk.DoubleVar()
    scale_frame = ttk.Scale(
        render_form, from_=0, to=1000,
        orient="horizontal", variable=scale_var, command=on_scale_change
    )
    scale_frame.grid(row=2, column=0, sticky="ew")

    frame_lista_bottoni = tk.Frame(render_form, bg='gray')
    frame_lista_bottoni.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(20, 0))

    lista_video = tk.Listbox(frame_lista_bottoni, width=30, height=20)
    lista_video.grid(row=0, column=0, rowspan=4, sticky="ns")

    scroll_y = tk.Scrollbar(frame_lista_bottoni, orient="vertical", command=lista_video.yview)
    scroll_y.grid(row=0, column=1, rowspan=4, sticky="ns")

    scroll_x = tk.Scrollbar(frame_lista_bottoni, orient="horizontal", command=lista_video.xview)
    scroll_x.grid(row=4, column=0, sticky="ew")

    lista_video.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    import os

    def load_video():
        lista_video.delete(0, tk.END)
        for v in os.listdir("./videos"):
            if v.endswith((".mp4", ".mkv", ".mov", ".avi")):
                lista_video.insert(tk.END, v.rsplit('.', 1)[0])

    load_video()

    def sposta_su():
        sel = lista_video.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        val = lista_video.get(idx)
        lista_video.delete(idx)
        lista_video.insert(idx - 1, val)
        lista_video.selection_set(idx - 1)
        lista_video.activate(idx - 1)

    def sposta_giu():
        sel = lista_video.curselection()
        if not sel or sel[0] == lista_video.size() - 1:
            return
        idx = sel[0]
        val = lista_video.get(idx)
        lista_video.delete(idx)
        lista_video.insert(idx + 1, val)
        lista_video.selection_set(idx + 1)
        lista_video.activate(idx + 1)

    def aggiorna_lista():
        load_video()

    def elimina_elemento():
        sel = lista_video.curselection()
        if not sel:
            return
        lista_video.delete(sel[0])

    frame_elementi = tk.Frame(frame_lista_bottoni, bg='gray')
    frame_elementi.grid(row=0, column=2, rowspan=4, sticky="ns", padx=(8, 0))

    tk.Button(frame_elementi, text='SU', width=8, command=sposta_su).pack(pady=(5, 2))
    tk.Button(frame_elementi, text='GIU', width=8, command=sposta_giu).pack(pady=2)
    tk.Button(frame_elementi, text='Aggiorna', width=8, command=aggiorna_lista).pack(pady=(12, 2))
    tk.Button(frame_elementi, text='Elimina', width=8, command=elimina_elemento).pack(pady=2)

    def f_audio():
        global path_audio
        path_audio = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a"), ("All Files", "*.*")]
        )
        print(f"File Audio selezionato: {path_audio}")

    tk.Button(frame_elementi, text='Seleziona audio', command=f_audio).pack(pady=2)

    def f_rendering():
        from tkinter import messagebox
        risposta = messagebox.askyesno("Conferma", "Hai sistemato l'ordine dei video?")
        if risposta:
            video_paths = []
            for i in range(lista_video.size()):
                nome_video = lista_video.get(i)
                for ext in [".mp4", ".mkv", ".mov", ".avi"]:
                    candidate = os.path.join("videos", nome_video + ext)
                    if os.path.exists(candidate):
                        video_paths.append(candidate)
                        break
                else:
                    print(f"File video non trovato per: {nome_video}")

            # ✅ Formato corretto per ffmpeg concat
            with open("lista.txt", "w", encoding="utf-8") as f:
                for path in video_paths:
                    path_norm = path.replace("\\", "/")
                    f.write(f"file '{path_norm}'\n")

            out = "filmatorenderizzato.mp4"
            audio_part = f'-i "{path_audio}"' if path_audio else ""
            os.system(f'ffmpeg -f concat -safe 0 -i lista.txt {audio_part} -c:v copy -c:a aac "{out}"')
            messagebox.showinfo("Rendering", f"Rendering completato: {out}")

    tk.Button(frame_elementi, text='Rendering_video', command=f_rendering).pack(pady=2)

    # ✅ NIENTE mainloop() qui — Toplevel usa già il loop della finestra principale

def f_form_render():
    render_window()  # ✅ Chiamata diretta, niente thread

Rendering = tk.Button(strumenti, text='Rendering', bg='light green', command=f_form_render)
Rendering.grid(row=2, column=9, padx=5)


# ═══════════════════════════════════════════════════════════════════════════════
# AVVIO
# ═══════════════════════════════════════════════════════════════════════════════


 
window.mainloop()

















