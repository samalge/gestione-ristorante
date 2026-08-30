import streamlit as st
from datetime import datetime, timedelta, date, time
import json
import os

st.set_page_config(page_title="Bordshantering Restaurang", layout="wide")
st.title("Centralen: Telefonbokning")

DB_FILE = "stato_bord.json"

def carica_bord():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                dati = json.load(f)
            if dati and "Bord 1" in dati:
                return {}
            dati_puliti = {}
            for data_str, tavoli in dati.items():
                dati_puliti[data_str] = {}
                for nome, info in tavoli.items():
                    dati_puliti[data_str][nome] = {
                        "stato": info["stato"],
                        "fino_a": datetime.fromisoformat(info["fino_a"]) if info["fino_a"] else None,
                        "max_cap": info["max_cap"],
                        "cliente": info.get("cliente", ""),
                        "tel": info.get("tel", "")
                    }
            return dati_puliti
        except Exception:
            return {}
    return {}

def salva_bord(dati_totali):
    dati_da_salvare = {}
    for data_str, tavoli in dati_totali.items():
        dati_da_salvare[data_str] = {}
        for nome, info in tavoli.items():
            dati_da_salvare[data_str][nome] = {
                "stato": info["stato"],
                "fino_a": info["fino_a"].isoformat() if info["fino_a"] else None,
                "max_cap": info["max_cap"],
                "cliente": info.get("cliente", ""),
                "tel": info.get("tel", "")
            }
    with open(DB_FILE, "w") as f:
        json.dump(dati_da_salvare, f)

dati_generali = carica_bord()

st.header("📆 Välj datum för bokning")
oggi_completo = datetime.now()
data_selezionata = st.date_input("Välj dag:", value=oggi_completo.date())
data_chiave = data_selezionata.isoformat()

if data_selezionata.strftime("%A") == "Monday":
    st.error("🚨 Det valda datumet är en måndag: restaurangen är STÄNGD.")
    st.stop()

if data_chiave not in dati_generali:
    sala_giorno = {f"Bord {i}": {"stato": "Libero", "fino_a": None, "max_cap": 2, "cliente": "", "tel": ""} for i in range(1, 4)}
    sala_giorno.update({f"Bord {i}": {"stato": "Libero", "fino_a": None, "max_cap": 4, "cliente": "", "tel": ""} for i in range(4, 11)})
    dati_generali[data_chiave] = sala_giorno
    salva_bord(dati_generali)

bord_attuali = dati_generali[data_chiave]

if data_selezionata == oggi_completo.date():
    cambiato = False
    for nome, dati in list(bord_attuali.items()):
        if dati["stato"] == "Occupato" and dati["fino_a"] and oggi_completo > dati["fino_a"]:
            bord_attuali[nome] = {"stato": "Libero", "fino_a": None, "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
            cambiato = True
    if cambiato:
        dati_generali[data_chiave] = bord_attuali
        salva_bord(dati_generali)

st.header("📌 Registrera ny bokning")
col1, col2, col3, col4 = st.columns(4)

with col1:
    cognome = st.text_input("Kundens efternamn", placeholder="t.ex. Rossi").strip()
with col2:
    telefono = st.text_input("Telefonnummer", placeholder="t.ex. 076123456")
with col3:
    persone = st.number_input("Antal personer", min_value=1, max_value=4, value=2)
with col4:
    orario_scelta = st.time_input("Ankomsttid", value=oggi_completo.time())

bord_disponibili = []
if persone <= 2:
    bord_disponibili = [f"{nome} (2 pers)" for nome, dati in bord_attuali.items() if dati["max_cap"] == 2 and dati["stato"] == "Libero"]
else:
    bord_disponibili = [f"{nome} (4 pers)" for nome, dati in bord_attuali.items() if dati["max_cap"] == 4 and dati["stato"] == "Libero"]

if bord_disponibili:
    bord_scelto_completo = st.selectbox("Valj bord att tilldela:", bord_disponibili)
    bord_scelto = bord_scelto_completo.split(" (")[0]
    
    if st.button("Boka valt bord"):
        if not cognome:
            st.error("⚠️ Vanligen fyll i kundens efternamn innan du sparar.")
        else:
            ora_inizio = datetime.combine(data_selezionata, orario_scelta)
            if data_selezionata == oggi_completo.date() and ora_inizio < oggi_completo:
                ora_inizio = oggi_completo
                
            bord_attuali[bord_scelto] = {
                "stato": "Occupato",
                "fino_a": ora_inizio + timedelta(minutes=120),
                "max_cap": bord_attuali[bord_scelto]["max_cap"],
                "cliente": cognome,
                "tel": telefono
            }
            dati_generali[data_chiave] = bord_attuali
            salva_bord(dati_generali)
            st.success(f"✅ Bokning klar! {bord_scelto} har tilldelats till {cognome} den {data_selezionata.strftime('%d/%m')}")
            st.rerun()
else:
    if persone <= 2:
        st.warning("⚠️ Alla 2-mansbord ar upptagna!")
    else:
        st.error("❌ Inga 4-mansbord ar tillgangliga just nu.")

st.header(f"🪟 Matsalens status: {data_selezionata.strftime('%d/%m/%Y')}")

for nome, dati in bord_attuali.items():
    col_bord, col_azione = st.columns(2)
    cap_testo = "2 pers" if dati["max_cap"] == 2 else "4 pers"
    
    with col_bord:
        if dati["stato"] == "Libero":
            st.markdown(f"🟢 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | TILLGÄNGLIGT", unsafe_allow_html=True)
        else:
            ora_fine = dati["fino_a"].strftime("%H:%M")
            info_cliente = f"Gäst: {dati.get('cliente', '')} ({dati.get('tel', '')})"
            if data_selezionata == oggi_completo.date():
                tempo_rimasto = dati["fino_a"] - datetime.now()
                minuti_rimasti = int(tempo_rimasto.total_seconds() / 60)
                countdown_testo = f"⏳ {minuti_rimasti} min återstår" if minuti_rimasti > 0 else "⏳ Tiden har gått ut!"
            else:
                countdown_testo = f"⏱️ Bokad till {ora_fine}"
            st.markdown(f"🔴 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | UPPTAGET | Sluttid: {ora_fine} | **{countdown_testo}**", unsafe_allow_html=True)
            st.write(f"👉 {info_cliente}")
            
    with col_azione:
        if dati["stato"] == "Occupato" and st.button("Frigör bord", key=nome):
            bord_attuali[nome] = {"stato": "Libero", "fino_a": None, "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
            dati_generali[data_chiave] = bord_attuali
            salva_bord(dati_generali)
            st.rerun()
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
