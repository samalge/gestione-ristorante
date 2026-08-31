import streamlit as st
from datetime import datetime, time
import json
import os
import copy

st.set_page_config(page_title="Bordshantering Pizzeria", layout="wide")
st.title("Centralen: Telefonbokning")

DB_FILE = "stato_bord.json"

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

# --- 📊 PANNELLO STATISTICHE NELLA BARRA LATERALE ---
st.sidebar.header("📊 Statistikpanel")

tipo_stat = st.sidebar.selectbox(
    "Välj statistikvy:",
    ["Specifik dag", "Hel månad", "Hela året"]
)

totale_ospiti_calcolato = 0

if tipo_stat == "Specifik dag":
    giorno_stat = st.sidebar.date_input("Välj dag för statistik:", value=datetime.now().date(), key="stat_day")
    chiave_giorno_stat = giorno_stat.isoformat()
    
    for chiave, info in db_prenotazioni.items():
        if chiave.startswith(chiave_giorno_stat):
            tavolo_id = chiave.split("|")[-1]
            cap_stimata = 4 if "Bord 1" not in tavolo_id and "Bord 2" not in tavolo_id and "Bord 3" not in tavolo_id else 2
            totale_ospiti_calcolato += cap_stimata

elif tipo_stat == "Hel månad":
    anno_corrente = datetime.now().year
    anno_stat = st.sidebar.number_input("Välj år:", min_value=2024, max_value=2030, value=anno_corrente, key="stat_month_year")
    mese_stat = st.sidebar.selectbox(
        "Välj månad:",
        ["Januari", "Februari", "Mars", "April", "Maj", "Juni", "Juli", "Augusti", "September", "Oktober", "November", "December"],
        index=datetime.now().month - 1
    )
    mesi_mappa = {"Januari":"01", "Februari":"02", "Mars":"03", "April":"04", "Maj":"05", "Juni":"06", "Juli":"07", "Augusti":"08", "September":"09", "Oktober":"10", "November":"11", "December":"12"}
    prefisso_mese = f"{anno_stat}-{mesi_mappa[mese_stat]}"
    
    for chiave, info in db_prenotazioni.items():
        if chiave.startswith(prefisso_mese):
            tavolo_id = chiave.split("|")[-1]
            cap_stimata = 4 if "Bord 1" not in tavolo_id and "Bord 2" not in tavolo_id and "Bord 3" not in tavolo_id else 2
            totale_ospiti_calcolato += cap_stimata

elif tipo_stat == "Hela året":
    anno_corrente = datetime.now().year
    anno_stat = st.sidebar.number_input("Välj år:", min_value=2024, max_value=2030, value=anno_corrente, key="stat_year_only")
    prefisso_anno = f"{anno_stat}-"
    
    for chiave, info in db_prenotazioni.items():
        if chiave.startswith(prefisso_anno):
            tavolo_id = chiave.split("|")[-1]
            cap_stimata = 4 if "Bord 1" not in tavolo_id and "Bord 2" not in tavolo_id and "Bord 3" not in tavolo_id else 2
            totale_ospiti_calcolato += cap_stimata

st.sidebar.metric(label="👥 Totalt antal gäster", value=f"{totale_ospiti_calcolato} st")
st.sidebar.markdown("<hr style='margin: 15px 0; border: 0.5px solid #555;'>", unsafe_allow_html=True)


# --- 🛠️ SECURE SESSION LOGIN / LOGOUT RESET SYSTEM ---
st.sidebar.header("🛠️ Systemverktyg")

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if not st.session_state["admin_logged_in"]:
    psw_input = st.sidebar.text_input("Ange säkerhetslösenord:", type="password", key="admin_psw_field")
    if st.sidebar.button("🔓 Logga in"):
        if psw_input == "Samuelmark123#":
            st.session_state["admin_logged_in"] = True
            st.rerun()
        else:
            st.sidebar.error("❌ Felaktigt lösenord!")
else:
    st.sidebar.success("🔒 Systemet är upplåst")
    
    if st.sidebar.button("⚠️ NOLLSTÄLL DATABASEN", help="Klicka här för att rensa alla bokningar och starta om systemet"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.sidebar.success("✅ Databasen har återställts!")
        else:
            st.sidebar.info("Databasen är redan tom.")
        st.session_state["admin_logged_in"] = False
        st.rerun()
        
    if st.sidebar.button("🔒 Logga ut"):
        st.session_state["admin_logged_in"] = False
        st.rerun()

st.sidebar.markdown("<hr style='margin: 15px 0; border: 0.5px solid #555;'>", unsafe_allow_html=True)


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
    # 🔴 CORREZIONE: Estratta la stringa di testo pulita con l'indice [0]
    bord_scelto = bord_scelto_completo.split(" (")[0]
    
    if st.button("Boka valt bord"):
        if not cognome:
            st.error("⚠️ Vänligen fyll i kundens efternamn innan du sparar.")
        else:
            lista_note = []
            if glutine: lista_note.append("⚠️ GLUTENFRI")
            if lattosio: lista_note.append("⚠️ LAKTOSFRI")
