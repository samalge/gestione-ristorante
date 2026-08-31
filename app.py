import streamlit as st
from datetime import datetime, time
import json
import os

st.set_page_config(page_title="Bordshantering Restaurang", layout="wide")
st.title("Centralen: Telefonbokning")

DB_FILE = "stato_bord.json"

def ottieni_turni_del_giorno(data_selezionata):
    # Controlla il giorno della settimana (0=Lunedì, 6=Domenica)
    giorno_settimana = data_selezionata.weekday()
    
    if giorno_settimana == 6:  # DOMENICA: Apre alle 12:00
        return {
            "Lunch - Turno 1 (12:00 - 13:30)": {"inizio": time(12, 0), "fine": time(13, 30)},
            "Lunch - Turno 2 (13:30 - 15:00)": {"inizio": time(13, 30), "fine": time(15, 0)},
            "Cena - Turno 1 (19:00 - 20:30)": {"inizio": time(19, 0), "fine": time(20, 30)},
            "Cena - Turno 2 (20:30 - 22:00)": {"inizio": time(20, 30), "fine": time(22, 0)},
            "Cena - Turno 3 (22:00 - 23:30)": {"inizio": time(22, 0), "fine": time(23, 30)}
        }
    else:  # DA MARTEDÌ A SABATO: Apre alle 11:00
        return {
            "Lunch - Turno 1 (11:00 - 12:30)": {"inizio": time(11, 0), "fine": time(12, 30)},
            "Lunch - Turno 2 (12:30 - 14:00)": {"inizio": time(12, 30), "fine": time(14, 0)},
            "Cena - Turno 1 (19:00 - 20:30)": {"inizio": time(19, 0), "fine": time(20, 30)},
            "Cena - Turno 2 (20:30 - 22:00)": {"inizio": time(20, 30), "fine": time(22, 0)},
            "Cena - Turno 3 (22:00 - 23:30)": {"inizio": time(22, 0), "fine": time(23, 30)}
        }

def carica_bord():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                dati = json.load(f)
            
            dati_puliti = {}
            for data_str, turni in dati.items():
                dati_puliti[data_str] = {}
                for turno_nome, tavoli in turni.items():
                    dati_puliti[data_str][turno_nome] = {}
                    for nome, info in tavoli.items():
                        dati_puliti[data_str][turno_nome][nome] = {
                            "stato": info["stato"],
                            "max_cap": info["max_cap"],
                            "cliente": info.get("cliente", ""),
                            "tel": info.get("tel", "")
                        }
            return dati_puliti
        except Exception:
            return {}
    return {}

def salva_bord(dati_totali):
    with open(DB_FILE, "w") as f:
        json.dump(dati_totali, f, indent=4)

dati_generali = carica_bord()

st.header("📆 Välj datum och skift för bokning")
oggi_completo = datetime.now()

col_data, col_turno = st.columns(2)
with col_data:
    data_selezionata = st.date_input("Välj dag:", value=oggi_completo.date())
    data_chiave = data_selezionata.isoformat()

if data_selezionata.strftime("%A") == "Monday":
    st.error("🚨 Det valda datumet är en måndag: restaurangen är STÄNGD.")
    st.stop()

# Carica i turni specifici per la giornata selezionata (Domenica vs Altri giorni)
TURNI = ottieni_turni_del_giorno(data_selezionata)

with col_turno:
    turno_selezionato = st.selectbox("Välj skift:", list(TURNI.keys()))

# Inizializzazione se la data o il turno non esistono nel DB
if data_chiave not in dati_generali:
    dati_generali[data_chiave] = {}

if turno_selezionato not in dati_generali[data_chiave]:
    sala_turno = {f"Bord {i}": {"stato": "Libero", "max_cap": 2, "cliente": "", "tel": ""} for i in range(1, 4)}
    sala_turno.update({f"Bord {i}": {"stato": "Libero", "max_cap": 4, "cliente": "", "tel": ""} for i in range(4, 11)})
    dati_generali[data_chiave][turno_selezionato] = sala_turno
    salva_bord(dati_generali)

bord_attuali = dati_generali[data_chiave][turno_selezionato]

st.header("📌 Registrera ny bokning")
col1, col2, col3 = st.columns(3)

with col1:
    cognome = st.text_input("Kundens efternamn", placeholder="t.ex. Rossi").strip()
with col2:
    telefono = st.text_input("Telefonnummer", placeholder="t.ex. 076123456")
with col3:
    persone = st.number_input("Antal personer", min_value=1, max_value=4, value=2)

bord_disponibili = []
if persone <= 2:
    bord_disponibili = [f"{nome} (2 pers)" for nome, dati in bord_attuali.items() if dati["max_cap"] == 2 and dati["stato"] == "Libero"]
else:
    bord_disponibili = [f"{nome} (4 pers)" for nome, dati in bord_attuali.items() if dati["max_cap"] == 4 and dati["stato"] == "Libero"]

if bord_disponibili:
    bord_scelto_completo = st.selectbox("Välj bord att tilldela:", bord_disponibili)
    bord_scelto = bord_scelto_completo.split(" (")[0]
    
    if st.button("Boka valt bord"):
        if not cognome:
            st.error("⚠️ Vänligen fyll i kundens efternamn innan du sparar.")
        else:
            bord_attuali[bord_scelto] = {
                "stato": "Occupato",
                "max_cap": bord_attuali[bord_scelto]["max_cap"],
                "cliente": cognome,
                "tel": telefono
            }
            dati_generali[data_chiave][turno_selezionato] = bord_attuali
            salva_bord(dati_generali)
            st.success(f"✅ Bokning klar! {bord_scelto} har tilldelats till {cognome} för {turno_selezionato} den {data_selezionata.strftime('%d/%m')}")
            st.rerun()
else:
    if persone <= 2:
        st.warning("⚠️ Alla 2-mansbord är upptagna under detta skift!")
    else:
        st.error("❌ Inga 4-mansbord är tillgängliga under detta skift.")

st.header(f"🪟 Matsalens status: {data_selezionata.strftime('%d/%m/%Y')} - {turno_selezionato}")

for nome, dati in bord_attuali.items():
    col_bord, col_azione = st.columns(2)
    cap_testo = "2 pers" if dati["max_cap"] == 2 else "4 pers"
    
    with col_bord:
        if dati["stato"] == "Libero":
            st.markdown(f"🟢 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | TILLGÄNGLIGT", unsafe_allow_html=True)
        else:
            info_cliente = f"Gäst: {dati.get('cliente', '')} ({dati.get('tel', '')})"
            st.markdown(f"🔴 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | UPPTAGET under detta skift", unsafe_allow_html=True)
            st.write(f"👉 {info_cliente}")
            
    with col_azione:
        if dati["stato"] == "Occupato" and st.button("Frigör bord", key=f"free_{nome}_{turno_selezionato}"):
            bord_attuali[nome] = {"stato": "Libero", "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
            dati_generali[data_chiave][turno_selezionato] = bord_attuali
            salva_bord(dati_generali)
            st.rerun()
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
