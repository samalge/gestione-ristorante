import streamlit as st
from datetime import datetime, timedelta
import json
import os

st.set_page_config(page_title="Gestione Tavoli Ristorante", layout="wide")
st.title("Centralino Tavoli: Prenotazioni Telefoniche")

DB_FILE = "stato_tavoli.json"

def carica_tavoli():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            dati = json.load(f)
            for nome, info in dati.items():
                if info["fino_a"]:
                    info["fino_a"] = datetime.fromisoformat(info["fino_a"])
            return dati
    tavoli = {f"Tavolo {i} (da 2)": {"stato": "Libero", "fino_a": None, "max_cap": 2, "cliente": "", "tel": ""} for i in range(1, 4)}
    tavoli.update({f"Tavolo {i} (da 4)": {"stato": "Libero", "fino_a": None, "max_cap": 4, "cliente": "", "tel": ""} for i in range(4, 11)})
    return tavoli

def salva_tavoli(tavoli):
    dati_da_salvare = {}
    for nome, info in tavoli.items():
        dati_da_salvare[nome] = {
            "stato": info["stato"],
            "fino_a": info["fino_a"].isoformat() if info["fino_a"] else None,
            "max_cap": info["max_cap"],
            "cliente": info.get("cliente", ""),
            "tel": info.get("tel", "")
        }
    with open(DB_FILE, "w") as f:
        json.dump(dati_da_salvare, f)

tavoli_attuali = carica_tavoli()

oggi = datetime.now()
if oggi.strftime("%A") == "Monday":
    st.error("Oggi e Lunedi: il ristorante e CHIUSO.")
    st.stop()

cambiato = False
for nome, dati in list(tavoli_attuali.items()):
    if dati["stato"] == "Occupato" and dati["fino_a"] and oggi > dati["fino_a"]:
        tavoli_attuali[nome] = {"stato": "Libero", "fino_a": None, "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
        cambiato = True
if cambiato:
    salva_tavoli(tavoli_attuali)

st.header("Registra Chiamata in Arrivo")
col1, col2, col3, col4 = st.columns(4)

with col1:
    cognome = st.text_input("Cognome Cliente", placeholder="es. Rossi").strip()
with col2:
    telefono = st.text_input("Telefono", placeholder="es. 333123456")
with col3:
    persone = st.number_input("Persone", min_value=1, max_value=4, value=2)
with col4:
    orario_scelta = st.time_input("Orario Arrivo", value=oggi.time())

tavoli_disponibili = []
if persone <= 2:
    tavoli_disponibili = [nome for nome, dati in tavoli_attuali.items() if dati["max_cap"] == 2 and dati["stato"] == "Libero"]
else:
    tavoli_disponibili = [nome for nome, dati in tavoli_attuali.items() if dati["max_cap"] == 4 and dati["stato"] == "Libero"]

if tavoli_disponibili:
    tavolo_scelto = st.selectbox("Scegli il tavolo da assegnare:", tavoli_disponibili)
    
    if st.button("Assegna Tavolo Selezionato"):
        if not cognome:
            st.error("Inserisci il cognome del cliente prima di salvare.")
        else:
            ora_inizio = datetime.combine(oggi.date(), orario_scelta)
            
            if ora_inizio < oggi:
                ora_inizio = oggi
                
            tavoli_attuali[tavolo_scelto] = {
                "stato": "Occupato",
                "fino_a": ora_inizio + timedelta(minutes=120),
                "max_cap": tavoli_attuali[tavolo_scelto]["max_cap"],
                "cliente": cognome,
                "tel": telefono
            }
            salva_tavoli(tavoli_attuali)
            st.success(f"Telefono registrato! Assegnato il **{tavolo_scelto}** a Sig. {cognome}")
            st.rerun()
else:
    if persone <= 2:
        st.warning("⚠️ Tutti i tavoli da 2 sono occupati! Non puoi usare un tavolo da 4 per 2 persone.")
    else:
        st.error("❌ Nessun tavolo da 4 disponibile al momento.")

st.header("Situazione Sala")
for nome, dati in tavoli_attuali.items():
    col_tavolo, col_azione = st.columns(2)
    
    with col_tavolo:
        if dati["stato"] == "Libero":
            st.info(f"**{nome}** | **DISPONIBILE**")
        else:
            ora_fine = dati["fino_a"].strftime("%H:%M")
            info_cliente = f"Clienti: {dati.get('cliente', '')} ({dati.get('tel', '')})"
            
            tempo_rimasto = dati["fino_a"] - datetime.now()
            minuti_rimasti = int(tempo_rimasto.total_seconds() / 60)
            
            if minuti_rimasti > 0:
                countdown_testo = f"⏳ Mancano {minuti_rimasti} minuti al rilascio"
            else:
                countdown_testo = "⏳ Tempo scaduto!"
                
            st.error(f"**{nome}** | **OCCUPATO** fino alle {ora_fine} | {info_cliente} | {countdown_testo}")
            
    with col_azione:
        if dati["stato"] == "Occupato" and st.button("Libera Subito", key=nome):
            tavoli_attuali[nome] = {"stato": "Libero", "fino_a": None, "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
            salva_tavoli(tavoli_attuali)
            st.rerun()

