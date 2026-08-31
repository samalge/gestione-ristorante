import streamlit as st
from datetime import datetime, time
import json
import os
import copy

st.set_page_config(page_title="Bordshantering Pizzeria", layout="wide")
st.title("Centralen: Telefonbokning")

DB_FILE = "stato_bord.json"

# --- Systemverktyg med lösenordsskydd ---
st.sidebar.header("🛠️ Systemverktyg")
psw_input = st.sidebar.text_input("Ange säkerhetslösenord:", type="password")

if st.sidebar.button("⚠️ NOLLSTÄLL DATABASEN", help="Klicka här för att rensa alla bokningar och starta om systemet"):
    if psw_input == "Samuelmark123#":
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.sidebar.success("✅ Databasen har återställts! Laddar om...")
        else:
            st.sidebar.info("Databasen är redan tom.")
        st.rerun()
    else:
        st.sidebar.error("❌ Felaktigt lösenord! Åtkomst nekad.")

def ottieni_turni_del_giorno(data_selezionata):
    giorno_settimana = data_selezionata.weekday() # 0=Måndag, 4=Fredag, 5=Lördag, 6=Söndag
    
    if giorno_settimana == 6:  # SÖNDAG
        return {
            "Lunch - Skift 1 (12:00 - 14:00)": {"inizio": "12:00", "fine": "14:00"},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": "13:00", "fine": "15:00"},
            "Middag - Skift 1 (16:00 - 18:00)": {"inizio": "16:00", "fine": "18:00"},
            "Middag - Skift 2 (18:00 - 20:00)": {"inizio": "18:00", "fine": "20:00"},
            "Middag - Skift 3 (20:00 - 22:00)": {"inizio": "20:00", "fine": "22:00"}
        }
    elif giorno_settimana in (4, 5):  # FREDAG OCH LÖRDAG
        return {
            "Lunch - Skift 1 (11:00 - 13:00)": {"inizio": "11:00", "fine": "13:00"},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": "13:00", "fine": "15:00"},
            "Middag - Skift 1 (16:00 - 18:00)": {"inizio": "16:00", "fine": "18:00"},
            "Middag - Skift 2 (18:00 - 20:00)": {"inizio": "18:00", "fine": "20:00"},
            "Middag - Skift 3 (20:00 - 22:00)": {"inizio": "20:00", "fine": "22:00"},
            "Middag - Skift 4 (21:00 - 23:00)": {"inizio": "21:00", "fine": "23:00"}
        }
    else:  # TISDAG, ONSDAG, TORSDAG
        return {
            "Lunch - Skift 1 (11:00 - 13:00)": {"inizio": "11:00", "fine": "13:00"},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": "13:00", "fine": "15:00"},
            "Middag - Skift 1 (16:00 - 18:00)": {"inizio": "16:00", "fine": "18:00"},
            "Middag - Skift 2 (18:00 - 20:00)": {"inizio": "18:00", "fine": "20:00"},
            "Middag - Skift 3 (20:00 - 22:00)": {"inizio": "20:00", "fine": "22:00"}
        }

def carica_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salva_database(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db_prenotazioni = carica_database()

st.header("📆 Välj datum")
oggi_completo = datetime.now()
data_selezionata = st.date_input("Välj dag:", value=oggi_completo.date())
data_chiave = data_selezionata.isoformat()

if data_selezionata.strftime("%A") == "Monday":
    st.error("🚨 Det valda datumet är en måndag: restaurangen är STÄNGD.")
    st.stop()

TURNI = ottieni_turni_del_giorno(data_selezionata)

# Bordskonfiguration (10 bord)
TAVOLI_MAPPATURA = {}
for i in range(1, 4):   TAVOLI_MAPPATURA[f"Bord {i}"] = 2
for i in range(4, 11):  TAVOLI_MAPPATURA[f"Bord {i}"] = 4

giorno_sett = data_selezionata.weekday()

# --- Ny bokning ---
st.header("📌 Registrera ny bokning")
col_turno_sel, col1, col2, col3 = st.columns(4)

lista_turni_disponibili = list(TURNI.keys())

default_turno_index = 0
if "pre_turno" in st.session_state and st.session_state["pre_turno"] in lista_turni_disponibili:
    default_turno_index = lista_turni_disponibili.index(st.session_state["pre_turno"])

with col_turno_sel:
    turno_selezionato = st.selectbox("Välj skift för bokning:", lista_turni_disponibili, index=default_turno_index)

with col1:
    cognome = st.text_input("Kundens efternamn", placeholder="t.ex. Rossi").strip()
with col2:
    telefono = st.text_input("Telefonnummer", placeholder="t.ex. 076123456")
with col3:
    persone = st.number_input("Antal personer", min_value=1, max_value=4, value=2)

st.markdown("**Allergier eller särskilda önskemål:**")
col_g, col_l, col_n = st.columns(3)
with col_g:
    glutine = st.checkbox("Glutenintolerans (Glutenfri)")
with col_l:
    lattosio = st.checkbox("Laktosintolerans (Laktosfri)")
with col_n:
    altre_note = st.text_input("Andra önskemål (t.ex. Barnstol)", placeholder="Skriv här...")

# Hantering av överlappande tider
tavoli_occupati_in_turno_adiacente = []
turno_adiacente = None
if giorno_sett == 6:
    if "Lunch - Skift 1" in turno_selezionato: turno_adiacente = "Lunch - Skift 2 (13:00 - 15:00)"
    elif "Lunch - Skift 2" in turno_selezionato: turno_adiacente = "Lunch - Skift 1 (12:00 - 14:00)"
elif giorno_sett in (4, 5):
    if "Middag - Skift 3" in turno_selezionato: turno_adiacente = "Middag - Skift 4 (21:00 - 23:00)"
    elif "Middag - Skift 4" in turno_selezionato: turno_adiacente = "Middag - Skift 3 (20:00 - 22:00)"

if turno_adiacente:
    for t_nome in TAVOLI_MAPPATURA.keys():
        if f"{data_chiave}|{turno_adiacente}|{t_nome}" in db_prenotazioni:
            tavoli_occupati_in_turno_adiacente.append(t_nome)

bord_disponibili = []
for t_nome, cap_max in TAVOLI_MAPPATURA.items():
    chiave_corrente = f"{data_chiave}|{turno_selezionato}|{t_nome}"
    if chiave_corrente not in db_prenotazioni and t_nome not in tavoli_occupati_in_turno_adiacente:
        if persone <= 2 and cap_max == 2:
            bord_disponibili.append(f"{t_nome} (2 pers)")
        elif persone > 2 and cap_max == 4:
            bord_disponibili.append(f"{t_nome} (4 pers)")

default_tavolo_index = 0
if "pre_tavolo" in st.session_state:
    testo_cercato = f"{st.session_state['pre_tavolo']} (2 pers)" if TAVOLI_MAPPATURA.get(st.session_state['pre_tavolo']) == 2 else f"{st.session_state['pre_tavolo']} (4 pers)"
    if testo_cercato in bord_disponibili:
        default_tavolo_index = bord_disponibili.index(testo_cercato)

if bord_disponibili:
    bord_scelto_completo = st.selectbox("Välj ledigt bord:", bord_disponibili, index=default_tavolo_index)
    # 🔴 CORREZIONE RIGA 138: Estratta la stringa pura usando [0]
    bord_scelto = bord_scelto_completo.split(" (")[0]
    
    if st.button("Boka valt bord"):
        if not cognome:
            st.error("⚠️ Vänligen fyll i kundens efternamn innan du sparar.")
        else:
            lista_note = []
            if glutine: lista_note.append("⚠️ GLUTENFRI")
            if lattosio: lista_note.append("⚠️ LAKTOSFRI")
            if altre_note.strip(): lista_note.append(altre_note.strip())
            nota_finale = " | ".join(lista_note)
            
            db_aggiornato = carica_database()
            chiave_salvataggio = f"{data_chiave}|{turno_selezionato}|{bord_scelto}"
            db_aggiornato[chiave_salvataggio] = {"cliente": cognome, "tel": telefono, "note": nota_finale}
            salva_database(db_aggiornato)
            
            if "pre_turno" in st.session_state: del st.session_state["pre_turno"]
            if "pre_tavolo" in st.session_state: del st.session_state["pre_tavolo"]
            
            st.success(f"✅ Bokning klar för {bord_scelto} under {turno_selezionato}!")
            st.rerun()
else:
    st.warning("⚠️ Inga passande bord är tillgängliga under detta skift.")


# --- 🪟 Matsalens status (Tabellöversikt) ---
st.header(f"🪟 Matsalens status: {data_selezionata.strftime('%d/%m/%Y')}")

lista_turni_del_giorno = list(TURNI.keys())
numero_colonne = len(lista_turni_del_giorno)

for t_nome, cap_max in TAVOLI_MAPPATURA.items():
    st.markdown(f"### 📦 {t_nome} (Max: {cap_max} pers)")
    colonne_turno = st.columns(numero_colonne)
    
    for indice, t_nome_orario in enumerate(lista_turni_del_giorno):
        with colonne_turno[indice]:
            t_bloccato = False
            t_adiacente_local = None
            if giorno_sett == 6:
                if "Lunch - Skift 1" in t_nome_orario: t_adiacente_local = "Lunch - Skift 2 (13:00 - 15:00)"
                elif "Lunch - Skift 2" in t_nome_orario: t_adiacente_local = "Lunch - Skift 1 (12:00 - 14:00)"
            elif giorno_sett in (4, 5):
                if "Middag - Skift 3" in t_nome_orario: t_adiacente_local = "Middag - Skift 4 (21:00 - 23:00)"
                elif "Middag - Skift 4" in t_nome_orario: t_adiacente_local = "Middag - Skift 3 (20:00 - 22:00)"
            
            if t_adiacente_local and f"{data_chiave}|{t_adiacente_local}|{t_nome}" in db_prenotazioni:
                t_bloccato = True

            chiave_specifica = f"{data_chiave}|{t_nome_orario}|{t_nome}"
            # 🔴 CORREZIONE RIGA 191: Estratta la stringa pura usando [0]
            nome_turno_breve = t_nome_orario.split(" (")[0]
            
            st.markdown(f"**{nome_turno_breve}**")
            st.caption(f"⏰ {TURNI[t_nome_orario]['inizio']} - {TURNI[t_nome_orario]['fine']}")
            
            if t_bloccato:
                info_blocco = db_prenotazioni[f"{data_chiave}|{t_adiacente_local}|{t_nome}"]
                st.markdown("🟠 <span style='color: #FF5722; font-size: 20px; font-weight: bold;'>BLOCKERAT</span>", unsafe_allow_html=True)
                st.caption(f"Bokat i nästa skift: {info_blocco['cliente']}")
            elif chiave_specifica in db_prenotazioni:
                info_p = db_prenotazioni[chiave_specifica]
                st.markdown("🔴 <span style='color: #D32F2F; font-size: 20px; font-weight: bold;'>BOKAT</span>", unsafe_allow_html=True)
                st.write(f"👤 **{info_p['cliente']}**")
                st.write(f"📞 {info_p['tel']}")
                if info_p.get("note"):
                    st.caption(f"📝 {info_p['note']}")
                
