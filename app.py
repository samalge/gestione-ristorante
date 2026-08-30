import streamlit as st
import json
import os

st.set_page_config(page_title="Gestione Magazzino", layout="wide")
st.title("📦 Magazzino & Dispensa Ristorante")

DB_FILE = "stato_magazzino.json"

def carica_magazzino():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    # Prodotti iniziali di esempio (puoi modificarli o cancellarli direttamente dall'app)
    return {
        "101": {"nome": "Pasta Barilla", "scorta": 20, "soglia_minima": 5},
        "102": {"nome": "Polpa di Pomodoro", "scorta": 50, "soglia_minima": 10},
        "103": {"nome": "Vino Rosso della Casa", "scorta": 12, "soglia_minima": 3}
    }

def salva_magazzino(inventario):
    with open(DB_FILE, "w") as f:
        json.dump(inventario, f)

inventario = carica_magazzino()

# BARRA LATERALE: CARICO MERCI (Arrivo Fornitori)
st.sidebar.header("🚚 Carico Merci (Arrivo Fornitori)")
nuovo_codice = st.sidebar.text_input("Codice Prodotto / Codice a Barre:", placeholder="es. 104 o scansiona")
nuovo_nome = st.sidebar.text_input("Nome Prodotto:", placeholder="es. Mozzarella")
quantita_carico = st.sidebar.number_input("Quantità da aggiungere:", min_value=1, value=10)
soglia_allerta = st.sidebar.number_input("Scorta minima di allerta:", min_value=1, value=5)

if st.sidebar.button("Registra e Aggiungi al Magazzino"):
    if not nuovo_codice or not nuovo_nome:
        st.sidebar.error("Devi inserire sia il codice che il nome del prodotto!")
    else:
        if nuovo_codice in inventario:
            inventario[nuovo_codice]["scorta"] += quantita_carico
        else:
            inventario[nuovo_codice] = {"nome": nuovo_nome, "scorta": quantita_carico, "soglia_minima": soglia_allerta}
        salva_magazzino(inventario)
        st.sidebar.success(f"Registrato! Aggiunti {quantita_carico} pz di {nuovo_nome}.")
        st.rerun()


# PANNELLO CENTRALE: SCARICO RAPIDO (Cucina / Bar)
st.header("🛒 Scarico Rapido (Uscita merci per la cucina)")
col_scan, col_quantita = st.columns(2)

with col_scan:
    codice_prelievo = st.text_input("Scansiona codice a barre o digita il codice prodotto:", key="scan", placeholder="Posiziona il cursore qui")
with col_quantita:
    quantita_prelievo = st.number_input("Quantità da prelevare:", min_value=1, value=1, key="qta")

if st.button("🔄 Conferma Prelievo", use_container_width=True):
    if codice_prelievo in inventario:
        if inventario[codice_prelievo]["scorta"] >= quantita_prelievo:
            inventario[codice_prelievo]["scorta"] -= quantita_prelievo
            salva_magazzino(inventario)
            st.success(f"Prelevati {quantita_prelievo} pz di **{inventario[codice_prelievo]['nome']}**!")
            st.rerun()
        else:
            st.error(f"Scorte insufficienti! Hai solo {inventario[codice_prelievo]['scorta']} pz in magazzino.")
    else:
        st.error("Codice prodotto non trovato nel database!")


# INVENTARIO IN TEMPO REALE
st.header("📊 Inventario in Tempo Reale")

for codice, info in list(inventario.items()):
    col_info, col_azioni = st.columns(2)
    scorta_attuale = info["scorta"]
    soglia = info["soglia_minima"]
    
    with col_info:
        if scorta_attuale <= soglia:
            # Allerta rossa se il prodotto sta per finire sotto la soglia minima
            st.error(f"🚨 **[{codice}] {info['nome']}** | In Magazzino: **{scorta_attuale}** pz (Sotto la scorta minima di {soglia} pz!)")
        else:
            st.info(f"📦 **[{codice}] {info['nome']}** | In Magazzino: **{scorta_attuale}** pz")
            
    with col_azioni:
        # Pulsante rapido per eliminare 1 pezzo (es. se scade o si rompe una bottiglia)
        if st.button("Elimina 1 pz", key=f"del_{codice}"):
            if inventario[codice]["scorta"] > 0:
                inventario[codice]["scorta"] -= 1
                salva_magazzino(inventario)
                st.rerun()
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)

