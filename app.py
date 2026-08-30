import streamlit as st
from datetime import datetime, timedelta
import json
import os

st.set_page_config(page_title="Bordshantering Restaurang", layout="wide")
st.title("Centralen: Telefonbokning")

DB_FILE = "stato_tavoli.json"

def carica_tavoli():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            dati = json.load(f)
            for nome, info in dati.items():
                if info["fino_a"]:
                    info["fino_a"] = datetime.fromisoformat(info["fino_a"])
            return dati
    tavoli = {f"Bord {i}": {"stato": "Libero", "fino_a": None, "max_cap": 2, "cliente": "", "tel": ""} for i in range(1, 4)}
    tavoli.update({f"Bord {i}": {"stato": "Libero", "fino_a": None, "max_cap": 4, "cliente": "", "tel": ""} for i in range(4, 11)})
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
    st.error("🚨 Idag ar det mandag: restaurangen ar STANGD.")
    st.stop()

cambiato = False
for nome, dati in list(tavoli_attuali.items()):
    if dati["stato"] == "Occupato" and dati["fino_a"] and oggi > dati["fino_a"]:
        tavoli_attuali[nome] = {"stato": "Libero", "fino_a": None, "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
        cambiato = True
if cambiato:
    salva_tavoli(tavoli_attuali)

# NY BOKNING PANEL
st.header("📌 Registrera ny bokning")
col1, col2, col3, col4 = st.columns(4)

with col1:
    cognome = st.text_input("Kundens efternamn", placeholder="t.ex. Rossi").strip()
with col2:
    telefono = st.text_input("Telefonnummer", placeholder="t.ex. 076123456")
with col3:
    persone = st.number_input("Antal personer", min_value=1, max_value=4, value=2)
with col4:
    orario_scelta = st.time_input("Ankomsttid", value=oggi.time())

tavoli_disponibili = []
if persone <= 2:
    tavoli_disponibili = [f"{nome} (2 pers)" for nome, dati in tavoli_attuali.items() if dati["max_cap"] == 2 and dati["stato"] == "Libero"]
else:
    tavoli_disponibili = [f"{nome} (4 pers)" for nome, dati in tavoli_attuali.items() if dati["max_cap"] == 4 and dati["stato"] == "Libero"]

if tavoli_disponibili:
    tavolo_scelto_completo = st.selectbox("Valj bord att tilldela:", tavoli_disponibili)
    tavolo_scelto = tavolo_scelto_completo.split(" (")[0] # Prende solo "Bord X"
    
    if st.button("Boka valt bord"):
        if not cognome:
            st.error("⚠️ Vanligen fyll i kundens efternamn innan du sparar.")
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
            st.success(f"✅ Bokning klar! {tavolo_scelto} har tilldelats till {cognome}")
            st.rerun()
else:
    if persone <= 2:
        st.warning("⚠️ Alla 2-mansbord ar upptagna! (Regel: Du far inte valja ett 4-mansbord for endast 2 personer).")
    else:
        st.error("❌ Inga 4-mansbord ar tillgangliga just nu.")

# MATTSALENS STATUS
st.header("🪟 Matsalens status i realtid")

for nome, dati in tavoli_attuali.items():
    col_tavolo, col_azione = st.columns([3, 1])
    cap_testo = "2 pers" if dati["max_cap"] == 2 else "4 pers"
    
    with col_tavolo:
        if dati["stato"] == "Libero":
            # Solo il nome del tavolo (Bord X) è in azzurro e più grande
            st.markdown(
                f"🟢 <span style='color: #4CC9F0; font-size: 22px; font-weight: bold;'>{nome}</span> "
                f"({cap_testo}) | TILLGÄNGLIGT", 
                unsafe_allow_html=True
            )
        else:
            ora_fine = dati["fino_a"].strftime("%H:%M")
            info_cliente = f"Gäst: {dati.get('cliente', '')} ({dati.get('tel', '')})"
            
            tempo_rimasto = dati["fino_a"] - datetime.now()
            minuti_rimasti = int(tempo_rimasto.total_seconds() / 60)
            
            if minuti_rimasti > 0:
                countdown_testo = f"⏳ {minuti_rimasti} min återstår"
            else:
                countdown_testo = "⏳ Tiden har gått ut!"
                
            # Solo il nome del tavolo (Bord X) è in rosso/rosa e più grande
            st.markdown(
                f"🔴 <span style='color: #F72585; font-size: 22px; font-weight: bold;'>{nome}</span> "
                f"({cap_testo}) | UPPTAGET | Sluttid: {ora_fine} | **{countdown_testo}**", 
                unsafe_allow_html=True
            )
            st.write(f"👉 {info_cliente}")
            
    with col_azione:
        if dati["stato"] == "Occupato" and st.button("Frigör bord", key=nome):
            tavoli_attuali[nome] = {"stato": "Libero", "fino_a": None, "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
            salva_tavoli(tavoli_attuali)
            st.rerun()
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
