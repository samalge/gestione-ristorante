import streamlit as st
from datetime import datetime, time
import json
import os

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

# Carichiamo il registro unico delle prenotazioni
db_prenotazioni = carica_database()

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

# Configurazione fissa e immutabile della sala
TAVOLI_MAPPATURA = {}
for i in range(1, 4):   TAVOLI_MAPPATURA[f"Bord {i}"] = 2
for i in range(4, 11):  TAVOLI_MAPPATURA[f"Bord {i}"] = 4

giorno_sett = data_selezionata.weekday()

# CALCOLO DELLE SOVRAPPOSIZIONI GLOBALI (Turni sfalsati domenicali e weekend)
tavoli_occupati_in_turno_adiacente = []
turno_adiacente = None

if giorno_sett == 6:  # Domenica pranzo sfalsato
    if "Pranzo - Turno 1" in turno_selezionato:
        turno_adiacente = "Pranzo - Turno 2 (13:00 - 15:00)"
    elif "Pranzo - Turno 2" in turno_selezionato:
        turno_adiacente = "Pranzo - Turno 1 (12:00 - 14:00)"
elif giorno_sett in (4, 5):  # Venerdì e Sabato sera sfalsati
    if "Cena - Turno 3" in turno_selezionato:
        turno_adiacente = "Cena - Turno 4 (21:00 - 23:00)"
    elif "Cena - Turno 4" in turno_selezionato:
        turno_adiacente = "Cena - Turno 3 (20:00 - 22:00)"

if turno_adiacente:
    for t_nome in TAVOLI_MAPPATURA.keys():
        chiave_adiacente = f"{data_chiave}|{turno_adiacente}|{t_nome}"
        if chiave_adiacente in db_prenotazioni:
            tavoli_occupati_in_turno_adiacente.append(t_nome)

st.header("📌 Registra Nuova Prenotazione")
col1, col2, col3 = st.columns(3)

with col1:
    cognome = st.text_input("Cognome Cliente", placeholder="es. Rossi").strip()
with col2:
    telefono = st.text_input("Numero di Telefono", placeholder="es. 347123456")
with col3:
    persone = st.number_input("Numero di Persone", min_value=1, max_value=4, value=2)

st.markdown("**Allergier o richieste speciali:**")
col_g, col_l, col_n = st.columns(3)
with col_g:
    glutine = st.checkbox("Intolleranza al Glutine (Senza Glutine)")
with col_l:
    lattosio = st.checkbox("Intolleranza al Lattosio (Senza Lattosio)")
with col_n:
    altre_note = st.text_input("Note aggiuntive (es. Seggiolone)", placeholder="Scrivi qui...")

# Generazione dinamica dei tavoli selezionabili nel menu a tendina
bord_disponibili = []
for t_nome, cap_max in TAVOLI_MAPPATURA.items():
    chiave_corrente = f"{data_chiave}|{turno_selezionato}|{t_nome}"
    
    # Il tavolo è libero solo se non è prenotato nel turno corrente e non è bloccato dall'adiacente
    if chiave_corrente not in db_prenotazioni and t_nome not in tavoli_occupati_in_turno_adiacente:
        if persone <= 2 and cap_max == 2:
            bord_disponibili.append(f"{t_nome} (2 pers)")
        elif persone > 2 and cap_max == 4:
            bord_disponibili.append(f"{t_nome} (4 pers)")

if bord_disponibili:
    bord_scelto_completo = st.selectbox("Seleziona tavolo da assegnare:", bord_disponibili)
    bord_scelto = bord_scelto_completo.split(" (")[0] # Estrazione pulita e garantita al 100% della stringa tavolo
    
    if st.button("Conferma Prenotazione Tavolo"):
        if not cognome:
            st.error("⚠️ Inserisci il cognome del cliente prima di salvare.")
        else:
            lista_note = []
            if glutine: lista_note.append("⚠️ SENZA GLUTINE")
            if lattosio: lista_note.append("⚠️ SENZA LATTOSIO")
            if altre_note.strip(): lista_note.append(altre_note.strip())
            nota_finale = " | ".join(lista_note)
            
            # Salvataggio lineare a chiave unica
            chiave_salvataggio = f"{data_chiave}|{turno_selezionato}|{bord_scelto}"
            db_prenotazioni[chiave_salvataggio] = {
                "cliente": cognome,
                "tel": telefono,
                "note": nota_finale
            }
            salva_database(db_prenotazioni)
            st.success(f"✅ Prenotazione completata! Il {bord_scelto} è stato assegnato a {cognome}")
            st.rerun()
else:
    st.warning(f"⚠️ Nessun tavolo disponibile per {persone} persone in questo turno.")

st.header(f"🪟 Stato della Sala: {data_selezionata.strftime('%d/%m/%Y')} - {turno_selezionato}")

for t_nome, cap_max in TAVOLI_MAPPATURA.items():
    col_bord, col_azione = st.columns(2)
    cap_testo = f"{cap_max} persone max"
    chiave_tavolo_corrente = f"{data_chiave}|{turno_selezionato}|{t_nome}"
    
    with col_bord:
        if t_nome in tavoli_occupati_in_turno_adiacente:
            chiave_adiacente_cerca = f"{data_chiave}|{turno_adiacente}|{t_nome}"
            info_altro = db_prenotazioni[chiave_adiacente_cerca]
            st.markdown(f"🟠 <span style='color: #FF5722; font-size: 24px; font-weight: bold;'>{t_nome}</span> ({cap_testo}) | BLOCCATO (Prenotato nel turno sovrapposto)", unsafe_allow_html=True)
            st.write(f"👉 Cliente nel turno adiacente: {info_altro['cliente']} ({info_altro['tel']})")
            if info_altro.get("note"):
                st.info(f"📋 **Note:** {info_altro['note']}")
                
        elif chiave_tavolo_corrente in db_prenotazioni:
            info_cliente = db_prenotazioni[chiave_tavolo_corrente]
            st.markdown(f"🔴 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{t_nome}</span> ({cap_testo}) | OCCUPATO", unsafe_allow_html=True)
            st.write(f"👉 Cliente: {info_cliente['cliente']} ({info_cliente['tel']})")
            if info_cliente.get("note"):
                st.warning(f"📋 **Allergier/Note:** {info_cliente['note']}")
        else:
            st.markdown(f"🟢 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{t_nome}</span> ({cap_testo}) | DISPONIBILE", unsafe_allow_html=True)
            
    with col_azione:
        if t_nome in tavoli_occupati_in_turno_adiacente:
            st.write("🔒 *Gestisci la prenotazione dal turno adiacente*")
        elif chiave_tavolo_corrente in db_prenotazioni:
            if st.button("Libera Tavolo", key=f"free_{chiave_tavolo_corrente}"):
                del db_prenotazioni[chiave_tavolo_corrente]
                salva_database(db_prenotazioni)
                st.rerun()
                
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
