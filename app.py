import streamlit as st
from datetime import datetime, time
import json
import os

st.set_page_config(page_title="Bordshantering Pizzeria", layout="wide")
st.title("Centralen: Telefonbokning")

DB_FILE = "stato_bord.json"

def ottieni_turni_del_giorno(data_selezionata):
    giorno_settimana = data_selezionata.weekday() # 0=Lunedì, 4=Venerdì, 5=Sabato, 6=Domenica
    
    if giorno_settimana == 6:  # DOMENICA (Pranzo 12:00 sfalsato, Cena chiude alle 22:00)
        return {
            "Lunch - Skift 1 (12:00 - 14:00)": {"inizio": time(12, 0), "fine": time(14, 0)},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Middag - Skift 1 (16:00 - 18:00)": {"inizio": time(16, 0), "fine": time(18, 0)},
            "Middag - Skift 2 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Middag - Skift 3 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)}
        }
    elif giorno_settimana in:  # VENERDÌ E SABATO (Pranzo 11:00, Cena sfalsata fino alle 23:00)
        return {
            "Lunch - Skift 1 (11:00 - 13:00)": {"inizio": time(11, 0), "fine": time(13, 0)},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Middag - Skift 1 (16:00 - 18:00)": {"inizio": time(16, 0), "fine": time(18, 0)},
            "Middag - Skift 2 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Middag - Skift 3 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)},
            "Middag - Skift 4 (21:00 - 23:00)": {"inizio": time(21, 0), "fine": time(23, 0)}
        }
    else:  # MARTEDÌ, MERCOLEDÌ, GIOVEDÌ (Pranzo 11:00, Cena chiude alle 22:00)
        return {
            "Lunch - Skift 1 (11:00 - 13:00)": {"inizio": time(11, 0), "fine": time(13, 0)},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Middag - Skift 1 (16:00 - 18:00)": {"inizio": time(16, 0), "fine": time(18, 0)},
            "Middag - Skift 2 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Middag - Skift 3 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)}
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
                            "stato": info.get("stato", "Libero"),
                            "max_cap": info.get("max_cap", 2),
                            "cliente": info.get("cliente", ""),
                            "tel": info.get("tel", ""),
                            "note": info.get("note", "")
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

TURNI = ottieni_turni_del_giorno(data_selezionata)

with col_turno:
    turno_selezionato = st.selectbox("Välj skift:", list(TURNI.keys()))

if data_chiave not in dati_generali:
    dati_generali[data_chiave] = {}

for t_nome in TURNI.keys():
    if t_nome not in dati_generali[data_chiave]:
        sala_turno = {f"Bord {i}": {"stato": "Libero", "max_cap": 2, "cliente": "", "tel": "", "note": ""} for i in range(1, 4)}
        sala_turno.update({f"Bord {i}": {"stato": "Libero", "max_cap": 4, "cliente": "", "tel": "", "note": ""} for i in range(4, 11)})
        dati_generali[data_chiave][t_nome] = sala_turno

salva_bord(dati_generali)

bord_attuali = dati_generali[data_chiave][turno_selezionato]
giorno_sett = data_selezionata.weekday()

# CALCOLO DELLE SOVRAPPOSIZIONI (Domenica pranzo & Venerdì/Sabato sera)
tavoli_bloccati_da_sovrapposizione = []
turno_adiacente = None

if giorno_sett == 6:  # Domenica mattina sfalsata
    if "Lunch - Skift 1" in turno_selezionato:
        turno_adiacente = "Lunch - Skift 2 (13:00 - 15:00)"
    elif "Lunch - Skift 2" in turno_selezionato:
        turno_adiacente = "Lunch - Skift 1 (12:00 - 14:00)"
elif giorno_sett in:  # Venerdì e Sabato sera sfalsati
    if "Middag - Skift 3" in turno_selezionato:
        turno_adiacente = "Middag - Skift 4 (21:00 - 23:00)"
    elif "Middag - Skift 4" in turno_selezionato:
        turno_adiacente = "Middag - Skift 3 (20:00 - 22:00)"

if turno_adiacente and turno_adiacente in dati_generali[data_chiave]:
    tavoli_bloccati_da_sovrapposizione = [
        k for k, v in dati_generali[data_chiave][turno_adiacente].items() if v["stato"] == "Occupato"
    ]

st.header("📌 Registrera ny bokning")
col1, col2, col3 = st.columns(3)

with col1:
    cognome = st.text_input("Kundens efternamn", placeholder="t.ex. Rossi").strip()
with col2:
    telefono = st.text_input("Telefonnummer", placeholder="t.ex. 076123456")
with col3:
    persone = st.number_input("Antal personer", min_value=1, max_value=4, value=2)

# Sezione Opzioni Speciali / Intolleranze
st.markdown("**Allergier eller särskilda önskemål:**")
col_g, col_l, col_n = st.columns(3)
with col_g:
    glutine = st.checkbox("Glutenintolerans (Glutenfri)")
with col_l:
    lattosio = st.checkbox("Laktosintolerans (Laktosfri)")
with col_n:
    altre_note = st.text_input("Andra önskemål / info (t.ex. Barnstol)", placeholder="Skriv här...")

bord_disponibili = []
for nome, dati in bord_attuali.items():
    if dati["stato"] == "Libero" and nome not in tavoli_bloccati_da_sovrapposizione:
        if persone <= 2 and dati["max_cap"] == 2:
            bord_disponibili.append(f"{nome} (2 pers)")
        elif persone > 2 and dati["max_cap"] == 4:
            bord_disponibili.append(f"{nome} (4 pers)")

if bord_disponibili:
    bord_scelto_completo = st.selectbox("Välj bord att tilldela:", bord_disponibili)
    bord_scelto = bord_scelto_completo.split(" (")[0]
    
    if st.button("Boka valt bord"):
        if not cognome:
            st.error("⚠️ Vänligen fyll i kundens efternamn innan du sparar.")
        else:
            # Uniamo le intolleranze selezionate in una stringa di note
            lista_note = []
            if glutine: lista_note.append("⚠️ GLUTENFRI")
            if lattosio: lista_note.append("⚠️ LAKTOSFRI")
            if altre_note.strip(): lista_note.append(altre_note.strip())
            nota_finale = " | ".join(lista_note)
            
            bord_attuali[bord_scelto] = {
                "stato": "Occupato",
                "max_cap": bord_attuali[bord_scelto]["max_cap"],
                "cliente": cognome,
                "tel": telefono,
                "note": nota_finale
            }
            dati_generali[data_chiave][turno_selezionato] = bord_attuali
            salva_bord(dati_generali)
            st.success(f"✅ Bokning klar! {bord_scelto} har tilldelats till {cognome}")
            st.rerun()
else:
    st.warning(f"⚠️ Inga passande bord är tillgängliga under detta skift.")

st.header(f"🪟 Matsalens status: {data_selezionata.strftime('%d/%m/%Y')} - {turno_selezionato}")

for nome, dati in bord_attuali.items():
    col_bord, col_azione = st.columns(2)
    cap_testo = f"{dati['max_cap']} pers"
    
    with col_bord:
        if nome in tavoli_bloccati_da_sovrapposizione:
            info_altro_turno = dati_generali[data_chiave][turno_adiacente][nome]
            st.markdown(f"🟠 <span style='color: #FF5722; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | BLOCKERAT (Bokat i det överlappande skiftet)", unsafe_allow_html=True)
            st.write(f"👉 Gäst: {info_altro_turno['cliente']} ({info_altro_turno['tel']})")
            if info_altro_turno.get("note"):
                st.info(f"📋 **Info:** {info_altro_turno['note']}")
        elif dati["stato"] == "Libero":
            st.markdown(f"🟢 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | TILLGÄNGLIGT", unsafe_allow_html=True)
        else:
            info_cliente = f"Gäst: {dati.get('cliente', '')} ({dati.get('tel', '')})"
            st.markdown(f"🔴 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | UPPTAGET", unsafe_allow_html=True)
            st.write(f"👉 {info_cliente}")
            if dati.get("note"):
                st.warning(f"📋 **Allergier/Önskemål:** {dati['note']}")
            
    with col_azione:
        if nome in tavoli_bloccati_da_sovrapposizione:
            st.write("🔒 *Hantera bokningen via det andra skiftet*")
        elif dati["stato"] == "Occupato" and st.button("Frigör bord", key=f"free_{nome}_{turno_selezionato}"):
            bord_attuali[nome] = {"stato": "Libero", "max_cap": dati["max_cap"], "cliente": "", "tel": "", "note": ""}
            dati_generali[data_chiave][turno_selezionato] = bord_attuali
            salva_bord(dati_generali)
            st.rerun()
            
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
