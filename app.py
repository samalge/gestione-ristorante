import streamlit as st
from datetime import datetime, time
import json
import os
import copy

st.set_page_config(page_title="Gestione Tavoli Pizzeria", layout="wide")
st.title("Centralino: Prenotazioni Telefoniche")

DB_FILE = "stato_bord.json"

# --- TASTO DI EMERGENZA PER CANCELLARE IL FILE CORROTTO ---
st.sidebar.header("🛠️ Strumenti di Sistema")
if st.sidebar.button("⚠️ RESETTA DATABASE", help="Clicca qui per cancellare le vecchie prenotazioni corrotte e riavviare il sistema pulito"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        st.sidebar.success("✅ Database resettato con successo! Riavvio in corso...")
    else:
        st.sidebar.info("Il database è già vuoto.")
    st.rerun()

def ottieni_turni_del_giorno(data_selezionata):
    giorno_settimana = data_selezionata.weekday() # 0=Lunedì, 4=Venerdì, 5=Sabato, 6=Domenica
    
    if giorno_settimana == 6:  # DOMENICA
        return {
            "Pranzo - Turno 1 (12:00 - 14:00)": {"inizio": time(12, 0), "fine": time(14, 0)},
            "Pranzo - Turno 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Cena - Turno 1 (16:00 - 18:00)": {"inizio": time(16, 0), "fine": time(18, 0)},
            "Cena - Turno 2 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Cena - Turno 3 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)}
        }
    elif giorno_settimana in (4, 5):  # VENERDÌ E SABATO
        return {
            "Pranzo - Turno 1 (11:00 - 13:00)": {"inizio": time(11, 0), "fine": time(13, 0)},
            "Pranzo - Turno 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Cena - Turno 1 (16:00 - 18:00)": {"inizio": time(16, 0), "fine": time(18, 0)},
            "Cena - Turno 2 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Cena - Turno 3 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)},
            "Cena - Turno 4 (21:00 - 23:00)": {"inizio": time(21, 0), "fine": time(23, 0)}
        }
    else:  # MARTEDÌ, MERCOLEDÌ, GIOVEDÌ
        return {
            "Pranzo - Turno 1 (11:00 - 13:00)": {"inizio": time(11, 0), "fine": time(13, 0)},
            "Pranzo - Turno 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Cena - Turno 1 (16:00 - 18:00)": {"inizio": time(16, 0), "fine": time(18, 0)},
            "Cena - Turno 2 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Cena - Turno 3 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)}
        }

def carica_bord():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salva_bord(dati_totali):
    with open(DB_FILE, "w") as f:
        json.dump(dati_totali, f, indent=4)

dati_generali = carica_bord()

st.header("📆 Seleziona Data e Turno")
oggi_completo = datetime.now()

col_data, col_turno = st.columns(2)
with col_data:
    data_selezionata = st.date_input("Scegli il giorno:", value=oggi_completo.date())
    data_chiave = data_selezionata.isoformat()

if data_selezionata.strftime("%A") == "Monday":
    st.error("🚨 La data selezionata è un lunedì: il ristorante è CHIUSO.")
    st.stop()

TURNI = ottieni_turni_del_giorno(data_selezionata)

with col_turno:
    turno_selezionato = st.selectbox("Scegli il turno:", list(TURNI.keys()))

if data_chiave not in dati_generali:
    dati_generali[data_chiave] = {}

for t_nome in TURNI.keys():
    if t_nome not in dati_generali[data_chiave]:
        sala_turno = {f"Bord {i}": {"stato": "Libero", "max_cap": 2, "cliente": "", "tel": "", "note": ""} for i in range(1, 4)}
        sala_turno.update({f"Bord {i}": {"stato": "Libero", "max_cap": 4, "cliente": "", "tel": "", "note": ""} for i in range(4, 11)})
        dati_generali[data_chiave][t_nome] = sala_turno

salva_bord(dati_generali)

bord_attuali = copy.deepcopy(dati_generali[data_chiave][turno_selezionato])
giorno_sett = data_selezionata.weekday()

# CALCOLO DELLE SOVRAPPOSIZIONI (Domenica pranzo & Venerdì/Sabato sera)
tavoli_bloccati_da_sovrapposizione = []
turno_adiacente = None

if giorno_sett == 6:  # Domenica pranzo
    if "Pranzo - Turno 1" in turno_selezionato:
        turno_adiacente = "Pranzo - Turno 2 (13:00 - 15:00)"
    elif "Pranzo - Turno 2" in turno_selezionato:
        turno_adiacente = "Pranzo - Turno 1 (12:00 - 14:00)"
elif giorno_sett in (4, 5):  # Venerdì e Sabato sera
    if "Cena - Turno 3" in turno_selezionato:
        turno_adiacente = "Cena - Turno 4 (21:00 - 23:00)"
    elif "Cena - Turno 4" in turno_selezionato:
        turno_adiacente = "Cena - Turno 3 (20:00 - 22:00)"

if turno_adiacente and turno_adiacente in dati_generali[data_chiave]:
    tavoli_bloccati_da_sovrapposizione = [
        k for k, v in dati_generali[data_chiave][turno_adiacente].items() if v["stato"] == "Occupato"
    ]

st.header("📌 Registra Nuova Prenotazione")
col1, col2, col3 = st.columns(3)

with col1:
    cognome = st.text_input("Cognome Cliente", placeholder="es. Rossi").strip()
with col2:
    telefono = st.text_input("Numero di Telefono", placeholder="es. 347123456")
with col3:
    persone = st.number_input("Numero di Persone", min_value=1, max_value=4, value=2)

st.markdown("**Allergie o Richieste Speciali:**")
col_g, col_l, col_n = st.columns(3)
with col_g:
    glutine = st.checkbox("Intolleranza al Glutine (Senza Glutine)")
with col_l:
    lattosio = st.checkbox("Intolleranza al Lattosio (Senza Lattosio)")
with col_n:
    altre_note = st.text_input("Note aggiuntive (es. Seggiolone)", placeholder="Scrivi qui...")

# Generazione dei tavoli disponibili nel menu a tendina
bord_disponibili = []
for nome, dati in bord_attuali.items():
    if dati["stato"] == "Libero" and nome not in tavoli_bloccati_da_sovrapposizione:
        if persone <= 2 and dati["max_cap"] == 2:
            bord_disponibili.append(f"{nome} (2 pers)")
        elif persone > 2 and dati["max_cap"] == 4:
            bord_disponibili.append(f"{nome} (4 pers)")

if bord_disponibili:
    bord_scelto_completo = st.selectbox("Seleziona tavolo da assegnare:", bord_disponibili)
    # 🔴 CORREZIONE FINALE E RIGIDA: Estrae la stringa del nome tavolo correttamente (es. "Bord 1")
    bord_scelto = bord_scelto_completo.split(" (")[0]
    
    if st.button("Conferma Prenotazione Tavolo"):
        if not cognome:
            st.error("⚠️ Inserisci il cognome del cliente prima di salvare.")
        else:
            lista_note = []
            if glutine: lista_note.append("⚠️ SENZA GLUTINE")
            if lattosio: lista_note.append("⚠️ SENZA LATTOSIO")
            if altre_note.strip(): lista_note.append(altre_note.strip())
            nota_finale = " | ".join(lista_note)
            
            # Scrittura diretta e sicura nel database generale
            dati_generali[data_chiave][turno_selezionato][bord_scelto] = {
                "stato": "Occupato",
                "max_cap": bord_attuali[bord_scelto]["max_cap"],
                "cliente": cognome,
                "tel": telefono,
                "note": nota_finale
            }
            salva_bord(dati_generali)
            st.success(f"✅ Prenotazione completata! Il {bord_scelto} è stato assegnato a {cognome}")
            st.rerun()
else:
    st.warning(f"⚠️ Nessun tavolo disponibile per {persone} persone in questo turno.")

st.header(f"🪟 Stato della Sala: {data_selezionata.strftime('%d/%m/%Y')} - {turno_selezionato}")

for nome, dati in bord_attuali.items():
    col_bord, col_azione = st.columns(2)
    cap_testo = f"{dati['max_cap']} persone max"
    
    with col_bord:
        if nome in tavoli_bloccati_da_sovrapposizione:
            info_altro_turno = dati_generali[data_chiave][turno_adiacente][nome]
            st.markdown(f"🟠 <span style='color: #FF5722; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | BLOCCATO (Prenotato nel turno sovrapposto)", unsafe_allow_html=True)
            st.write(f"👉 Cliente nel turno adiacente: {info_altro_turno['cliente']} ({info_altro_turno['tel']})")
            if info_altro_turno.get("note"):
                st.info(f"📋 **Note:** {info_altro_turno['note']}")
        elif dati["stato"] == "Libero":
            st.markdown(f"🟢 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | DISPONIBILE", unsafe_allow_html=True)
        else:
            st.markdown(f"🔴 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | OCCUPATO", unsafe_allow_html=True)
            st.write(f"👉 Cliente: {dati['cliente']} ({dati['tel']})")
            if dati.get("note"):
                st.warning(f"📋 **Allergie/Note:** {dati['note']}")
            
    with col_azione:
        if nome in tavoli_bloccati_da_sovrapposizione:
            st.write("🔒 *Gestisci la prenotazione dal turno adiacente*")
        elif dati["stato"] == "Occupato" and st.button("Libera Tavolo", key=f"free_{nome}_{turno_selezionato}"):
            dati_generali[data_chiave][turno_selezionato][nome] = {"stato": "Libero", "max_cap": dati["max_cap"], "cliente": "", "tel": "", "note": ""}
            salva_bord(dati_generali)
            st.rerun()
            
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
