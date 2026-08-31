import streamlit as st
from datetime import datetime, time
import json
import os
import copy

st.set_page_config(page_title="Gestione Tavoli Pizzeria", layout="wide")
st.title("Centralino: Prenotazioni Telefoniche")

DB_FILE = "stato_bord.json"

# --- STRUMENTO DI RESET ---
st.sidebar.header("🛠️ Strumenti di Sistema")
if st.sidebar.button("⚠️ RESETTA DATABASE", help="Cancella tutte le prenotazioni e riparte da zero"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        st.sidebar.success("✅ Database resettato! Riavvio...")
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


# =========================================================================
# 📊 PANNELLO STATISTICHE NELLA BARRA LATERALE (A SINISTRA)
# =========================================================================
st.sidebar.markdown("<hr style='margin: 10px 0; border: 0.5px solid #555;'>", unsafe_allow_html=True)
st.sidebar.header("📊 Statistikpanel")

tipo_stat = st.sidebar.selectbox(
    "Välj statistikvy:",
    ["Specifik dag", "Hel månad", "Hela året"],
    key="stat_view_selector"
)

totale_ospiti = 0
posti_tavoli = {"Bord 1": 2, "Bord 2": 2, "Bord 3": 2, "Bord 4": 4, "Bord 5": 4, "Bord 6": 4, "Bord 7": 4, "Bord 8": 4, "Bord 9": 4, "Bord 10": 4}
data_corrente = datetime.now()

if tipo_stat == "Specifik dag":
    giorno_stat = st.sidebar.date_input("Välj dag:", value=data_corrente.date(), key="stat_day_input")
    chiave_cerca = giorno_stat.isoformat()
    for chiave in db_prenotazioni.keys():
        if chiave.startswith(chiave_cerca):
            nome_tavolo = chiave.split("|")[-1]
            totale_ospiti += posti_tavoli.get(nome_tavolo, 2)

elif tipo_stat == "Hel månad":
    anno_stat = st.sidebar.number_input("Välj år:", min_value=2024, max_value=2030, value=data_corrente.year, key="stat_year_input_m")
    mese_stat = st.sidebar.selectbox(
        "Välj månad:",
        ["Januari", "Februari", "Mars", "April", "Maj", "Juni", "Juli", "Augusti", "September", "Oktober", "November", "December"],
        index=data_corrente.month - 1,
        key="stat_month_input"
    )
    mappa_mesi = {"Januari":"01", "Februari":"02", "Mars":"03", "April":"04", "Maj":"05", "Juni":"06", "Juli":"07", "Augusti":"08", "September":"09", "Oktober":"10", "November":"11", "December":"12"}
    chiave_cerca = f"{anno_stat}-{mappa_mesi[mese_stat]}"
    for chiave in db_prenotazioni.keys():
        if chiave.startswith(chiave_cerca):
            nome_tavolo = chiave.split("|")[-1]
            totale_ospiti += posti_tavoli.get(nome_tavolo, 2)

elif tipo_stat == "Hela året":
    anno_solo = st.sidebar.number_input("Välj år:", min_value=2024, max_value=2030, value=data_corrente.year, key="stat_year_only_input")
    chiave_cerca = f"{anno_solo}-"
    for chiave in db_prenotazioni.keys():
        if chiave.startswith(chiave_cerca):
            nome_tavolo = chiave.split("|")[-1]
            totale_ospiti += posti_tavoli.get(nome_tavolo, 2)

st.sidebar.metric(label="👥 Totalt antal gäster:", value=f"{totale_ospiti} st")
st.sidebar.markdown("<hr style='margin: 10px 0; border: 0.5px solid #555;'>", unsafe_allow_html=True)
# =========================================================================


st.header("📆 Selezione Data")
oggi_completo = datetime.now()
data_selezionata = st.date_input("Scegli il giorno:", value=oggi_completo.date())
data_chiave = data_selezionata.isoformat()

if data_selezionata.strftime("%A") == "Monday":
    st.error("🚨 La data selezionata è un lunedì: il ristorante è CHIUSO.")
    st.stop()

TURNI = ottieni_turni_del_giorno(data_selezionata)

# Configurazione fissa dei tavoli (2 o 4 posti)
TAVOLI_MAPPATURA = {}
for i in range(1, 4):   TAVOLI_MAPPATURA[f"Bord {i}"] = 2
for i in range(4, 11):  TAVOLI_MAPPATURA[f"Bord {i}"] = 4

giorno_sett = data_selezionata.weekday()

# --- BLOCCO PRENOTAZIONE ---
st.header("📌 Inserisci Nuova Prenotazione")
col_turno_sel, col1, col2, col3 = st.columns(4)

with col_turno_sel:
    turno_selezionato = st.selectbox("In quale turno inserire:", list(TURNI.keys()))

with col1:
    cognome = st.text_input("Cognome Cliente", placeholder="es. Rossi").strip()
with col2:
    telefono = st.text_input("Numero di Telefono", placeholder="es. 347123456")
with col3:
    persone = st.number_input("Numero di Persone", min_value=1, max_value=4, value=2)

st.markdown("**Allergier o richieste speciali per questa prenotazione:**")
col_g, col_l, col_n = st.columns(3)
with col_g:
    glutine = st.checkbox("Intolleranza al Glutine (Senza Glutine)")
with col_l:
    lattosio = st.checkbox("Intolleranza al Lattosio (Senza Lattosio)")
with col_n:
    altre_note = st.text_input("Note aggiuntive (es. Seggiolone)", placeholder="Scrivi qui...")

# Calcolo sovrapposizioni per il menu a tendina dinamico della prenotazione
tavoli_occupati_in_turno_adiacente = []
turno_adiacente = None
if giorno_sett == 6:
    if "Pranzo - Turno 1" in turno_selezionato: turno_adiacente = "Pranzo - Turno 2 (13:00 - 15:00)"
    elif "Pranzo - Turno 2" in turno_selezionato: turno_adiacente = "Pranzo - Turno 1 (12:00 - 14:00)"
elif giorno_sett in (4, 5):
    if "Cena - Turno 3" in turno_selezionato: turno_adiacente = "Cena - Turno 4 (21:00 - 23:00)"
    elif "Cena - Turno 4" in turno_selezionato: turno_adiacente = "Cena - Turno 3 (20:00 - 22:00)"

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

if bord_disponibili:
    bord_scelto_completo = st.selectbox("Seleziona tavolo libero per questo turno:", bord_disponibili)
    bord_scelto = bord_scelto_completo.split(" (")
    
    if st.button("Conferma Prenotazione Tavolo"):
        if not cognome:
            st.error("⚠️ Inserisci il cognome del cliente prima di salvare.")
        else:
            lista_note = []
            if glutine: lista_note.append("⚠️ SENZA GLUTINE")
            if lattosio: lista_note.append("⚠️ SENZA LATTOSIO")
            if altre_note.strip(): lista_note.append(altre_note.strip())
            nota_finale = " | ".join(lista_note)
            
            db_aggiornato = carica_database()
            chiave_salvataggio = f"{data_chiave}|{turno_selezionato}|{bord_scelto}"
            db_aggiornato[chiave_salvataggio] = {"cliente": cognome, "tel": telefono, "note": nota_finale}
            salva_database(db_aggiornato)
            st.success(f"✅ Prenotazione salvata per {bord_scelto} nel turno {turno_selezionato}!")
            st.rerun()
else:
    st.warning("⚠️ Nessun tavolo disponibile per il numero di persone selezionato in questo turno.")


# --- 🪟 NUOVA INTERFACCIA: TABELLONE COMPLETO DELLA GIORNATA ---
st.header("🪟 Tabellone Stato di Oggi: " + str(data_selezionata.strftime('%d/%m/%Y')))

# Creiamo le colonne per ogni turno presente nella giornata attuale
lista_turni_del_giorno = list(TURNI.keys())
numero_colonne = len(lista_turni_del_giorno)

# Creiamo una riga per ogni tavolo della pizzeria
for t_nome, cap_max in TAVOLI_MAPPATURA.items():
    st.markdown(f"### 📦 {t_nome} (Capienza max: {cap_max} persone)")
    
    # Allineiamo i turni in orizzontale su colonne distinte
    colonne_turno = st.columns(numero_colonne)
    
