import streamlit as st
from datetime import datetime, time
import json
import os

st.set_page_config(page_title="Bordshantering Restaurang", layout="wide")
st.title("Centralen: Telefonbokning")

DB_FILE = "stato_bord.json"

def ottieni_turni_del_giorno(data_selezionata):
    giorno_settimana = data_selezionata.weekday() # 0=Lunedì, 6=Domenica
    
    if giorno_settimana == 6:  # DOMENICA: Turni sfalsati a pranzo
        return {
            "Lunch - Skift 1 (12:00 - 14:00)": {"inizio": time(12, 0), "fine": time(14, 0)},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Middag - Skift 1 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Middag - Skift 2 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)},
            "Middag - Skift 3 (22:00 - 00:00)": {"inizio": time(22, 0), "fine": time(0, 0)}
        }
    else:  # DA MARTEDÌ A SABATO: Turni standard da 120 min
        return {
            "Lunch - Skift 1 (11:00 - 13:00)": {"inizio": time(11, 0), "fine": time(13, 0)},
            "Lunch - Skift 2 (13:00 - 15:00)": {"inizio": time(13, 0), "fine": time(15, 0)},
            "Middag - Skift 1 (18:00 - 20:00)": {"inizio": time(18, 0), "fine": time(20, 0)},
            "Middag - Skift 2 (20:00 - 22:00)": {"inizio": time(20, 0), "fine": time(22, 0)},
            "Middag - Skift 3 (22:00 - 00:00)": {"inizio": time(22, 0), "fine": time(0, 0)}
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

TURNI = ottieni_turni_del_giorno(data_selezionata)

with col_turno:
    turno_selezionato = st.selectbox("Välj skift:", list(TURNI.keys()))

# Configurazione completa dei tavoli della pizzeria
TAVOLI_CONFIG = {}
for i in range(1, 4):   TAVOLI_CONFIG[f"Bord {i}"] = 2
for i in range(4, 11):  TAVOLI_CONFIG[f"Bord {i}"] = 4

# Logica di ottimizzazione per la DOMENICA A PRANZO per evitare sovrapposizioni
tavoli_filtrati_per_turno = TAVOLI_CONFIG.copy()
is_domenica = data_selezionata.weekday() == 6

if is_domenica and "Lunch - Skift 1" in turno_selezionato:
    # Solo tavoli DISPARI per il turno delle 12:00
    tavoli_filtrati_per_turno = {k: v for k, v in TAVOLI_CONFIG.items() if int(k.split()[1]) % 2 != 0}
elif is_domenica and "Lunch - Skift 2" in turno_selezionato:
    # Solo tavoli PARI per il turno delle 13:00
    tavoli_filtrati_per_turno = {k: v for k, v in TAVOLI_CONFIG.items() if int(k.split()[1]) % 2 == 0}

if data_chiave not in dati_generali:
    dati_generali[data_chiave] = {}

if turno_selezionato not in dati_generali[data_chiave]:
    # Inizializza il turno nel database usando la configurazione filtrata o totale
    sala_turno = {nome: {"stato": "Libero", "max_cap": cap, "cliente": "", "tel": ""} for nome, cap in tavoli_filtrati_per_turno.items()}
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
for nome, dati in bord_attuali.items():
    if dati["stato"] == "Libero":
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
            bord_attuali[bord_scelto] = {
                "stato": "Occupato",
                "max_cap": bord_attuali[bord_scelto]["max_cap"],
                "cliente": cognome,
                "tel": telefono
            }
            dati_generali[data_chiave][turno_selezionato] = bord_attuali
            salva_bord(dati_generali)
            st.success(f"✅ Bokning klar! {bord_scelto} har tilldelats till {cognome} för {turno_selezionato}")
            st.rerun()
else:
    st.warning(f"⚠️ Inga passande bord är tillgängliga för {persone} personer under detta skift.")

st.header(f"🪟 Matsalens status: {data_selezionata.strftime('%d/%m/%Y')} - {turno_selezionato}")

if is_domenica and "Lunch" in turno_selezionato:
    st.info("💡 Söndagsoptimering aktiverad: Salen är uppdelad i jämna/udda bord för att hantera överlappande tider (12:00 och 13:00).")

for nome, dati in bord_attuali.items():
    col_bord, col_azione = st.columns(2)
    cap_testo = f"{dati['max_cap']} pers"
    
    with col_bord:
        if dati["stato"] == "Libero":
            st.markdown(f"🟢 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | TILLGÄNGLIGT", unsafe_allow_html=True)
        else:
            info_cliente = f"Gäst: {dati.get('cliente', '')} ({dati.get('tel', '')})"
            st.markdown(f"🔴 <span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{nome}</span> ({cap_testo}) | UPPTAGET", unsafe_allow_html=True)
            st.write(f"👉 {info_cliente}")
            
    with col_azione:
        if dati["stato"] == "Occupato" and st.button("Frigör bord", key=f"free_{nome}_{turno_selezionato}"):
            bord_attuali[nome] = {"stato": "Libero", "max_cap": dati["max_cap"], "cliente": "", "tel": ""}
            dati_generali[data_chiave][turno_selezionato] = bord_attuali
            salva_bord(dati_generali)
            st.rerun()
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
