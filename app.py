
import streamlit as st
from datetime import datetime, time
import json
import os
import shutil
import hmac

# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(
    page_title="Centralino - Prenotazioni Pizzeria",
    layout="wide"
)

st.title("📞 Centralino: Prenotazioni Telefoniche")

DB_FILE = "stato_bord.json"
BACKUP_FILE = "stato_bord_backup.json"

# Password per il reset del database
RESET_PASSWORD = "Samuelmark123#"


# ============================================================
# DATABASE
# ============================================================

def carica_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                dati = json.load(f)

            # Compatibilità con il vecchio database
            for chiave, valore in dati.items():

                if "persone" not in valore:
                    valore["persone"] = 2

                if "stato" not in valore:
                    valore["stato"] = "Prenotato"

                if "note" not in valore:
                    valore["note"] = ""

                if "tel" not in valore:
                    valore["tel"] = ""

            return dati

        except Exception:
            return {}

    return {}


def salva_database(db):
    # Backup automatico prima di modificare
    if os.path.exists(DB_FILE):
        try:
            shutil.copy2(DB_FILE, BACKUP_FILE)
        except Exception:
            pass

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(
            db,
            f,
            indent=4,
            ensure_ascii=False
        )


db_prenotazioni = carica_database()


# ============================================================
# FUNZIONI
# ============================================================

def tavolo_compatibile(tavolo, persone, mappa_tavoli):

    capienza = mappa_tavoli[tavolo]

    if persone <= 2:
        return capienza == 2

    return capienza == 4


def prenotazioni_giornaliere(db, data_prefix):

    risultato = []

    for chiave, dati in db.items():

        if not chiave.startswith(data_prefix):
            continue

        parti = chiave.split("|")

        if len(parti) != 3:
            continue

        risultato.append({
            "chiave": chiave,
            "data": parti[0],
            "turno": parti[1],
            "tavolo": parti[2],
            "cliente": dati.get("cliente", ""),
            "tel": dati.get("tel", ""),
            "persone": dati.get("persone", 2),
            "note": dati.get("note", ""),
            "stato": dati.get("stato", "Prenotato")
        })

    return risultato


def trova_prenotazioni(db, ricerca):

    risultati = []

    ricerca = ricerca.lower().strip()

    if not ricerca:
        return risultati

    for chiave, dati in db.items():

        cliente = str(
            dati.get("cliente", "")
        ).lower()

        telefono = str(
            dati.get("tel", "")
        ).lower()

        if ricerca in cliente or ricerca in telefono:

            parti = chiave.split("|")

            if len(parti) == 3:

                risultati.append({
                    "chiave": chiave,
                    "data": parti[0],
                    "turno": parti[1],
                    "tavolo": parti[2],
                    "cliente": dati.get("cliente", ""),
                    "tel": dati.get("tel", ""),
                    "persone": dati.get("persone", 2),
                    "note": dati.get("note", ""),
                    "stato": dati.get("stato", "Prenotato")
                })

    risultati.sort(
        key=lambda x: (x["data"], x["turno"])
    )

    return risultati


def conteggio_periodo(db, prefisso):

    prenotazioni = 0
    persone = 0

    for chiave, dati in db.items():

        if chiave.startswith(prefisso):

            if dati.get("stato", "Prenotato") == "Cancellato":
                continue

            prenotazioni += 1

            try:
                persone += int(
                    dati.get("persone", 2)
                )
            except Exception:
                persone += 2

    return prenotazioni, persone


# ============================================================
# TURNI
# ============================================================

def ottieni_turni_del_giorno(data_selezionata):

    giorno_settimana = data_selezionata.weekday()

    # DOMENICA
    if giorno_settimana == 6:

        return {
            "Pranzo - Turno 1 (12:00 - 14:00)": {
                "inizio": time(12, 0),
                "fine": time(14, 0)
            },

            "Pranzo - Turno 2 (13:00 - 15:00)": {
                "inizio": time(13, 0),
                "fine": time(15, 0)
            },

            "Cena - Turno 1 (16:00 - 18:00)": {
                "inizio": time(16, 0),
                "fine": time(18, 0)
            },

            "Cena - Turno 2 (18:00 - 20:00)": {
                "inizio": time(18, 0),
                "fine": time(20, 0)
            },

            "Cena - Turno 3 (20:00 - 22:00)": {
                "inizio": time(20, 0),
                "fine": time(22, 0)
            }
        }

    # VENERDÌ E SABATO
    elif giorno_settimana in (4, 5):

        return {
            "Pranzo - Turno 1 (11:00 - 13:00)": {
                "inizio": time(11, 0),
                "fine": time(13, 0)
            },

            "Pranzo - Turno 2 (13:00 - 15:00)": {
                "inizio": time(13, 0),
                "fine": time(15, 0)
            },

            "Cena - Turno 1 (16:00 - 18:00)": {
                "inizio": time(16, 0),
                "fine": time(18, 0)
            },

            "Cena - Turno 2 (18:00 - 20:00)": {
                "inizio": time(18, 0),
                "fine": time(20, 0)
            },

            "Cena - Turno 3 (20:00 - 22:00)": {
                "inizio": time(20, 0),
                "fine": time(22, 0)
            },

            "Cena - Turno 4 (21:00 - 23:00)": {
                "inizio": time(21, 0),
                "fine": time(23, 0)
            }
        }

    # MARTEDÌ, MERCOLEDÌ, GIOVEDÌ
    else:

        return {
            "Pranzo - Turno 1 (11:00 - 13:00)": {
                "inizio": time(11, 0),
                "fine": time(13, 0)
            },

            "Pranzo - Turno 2 (13:00 - 15:00)": {
                "inizio": time(13, 0),
                "fine": time(15, 0)
            },

            "Cena - Turno 1 (16:00 - 18:00)": {
                "inizio": time(16, 0),
                "fine": time(18, 0)
            },

            "Cena - Turno 2 (18:00 - 20:00)": {
                "inizio": time(18, 0),
                "fine": time(20, 0)
            },

            "Cena - Turno 3 (20:00 - 22:00)": {
                "inizio": time(20, 0),
                "fine": time(22, 0)
            }
        }


# ============================================================
# TAVOLI
# ============================================================

TAVOLI_MAPPATURA = {}

for i in range(1, 4):
    TAVOLI_MAPPATURA[f"Bord {i}"] = 2

for i in range(4, 11):
    TAVOLI_MAPPATURA[f"Bord {i}"] = 4


# ============================================================
# SESSION STATE
# ============================================================

if "pre_turno" not in st.session_state:
    st.session_state["pre_turno"] = None

if "pre_tavolo" not in st.session_state:
    st.session_state["pre_tavolo"] = None

if "reset_autorizzato" not in st.session_state:
    st.session_state["reset_autorizzato"] = False


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("📊 Riepilogo")

oggi_dt = datetime.now()
oggi_stringa = oggi_dt.date().isoformat()

mese_corrente = oggi_dt.strftime("%Y-%m")
anno_corrente = oggi_dt.strftime("%Y")

oggi_prenotazioni, oggi_persone = conteggio_periodo(
    db_prenotazioni,
    oggi_stringa
)

mese_prenotazioni, mese_persone = conteggio_periodo(
    db_prenotazioni,
    mese_corrente
)

anno_prenotazioni, anno_persone = conteggio_periodo(
    db_prenotazioni,
    anno_corrente
)

st.sidebar.metric(
    "📆 Prenotazioni oggi",
    oggi_prenotazioni
)

st.sidebar.metric(
    "👥 Persone oggi",
    oggi_persone
)

st.sidebar.metric(
    "🗓️ Prenotazioni questo mese",
    mese_prenotazioni
)

st.sidebar.metric(
    "👥 Persone questo mese",
    mese_persone
)

st.sidebar.metric(
    "👑 Prenotazioni quest'anno",
    anno_prenotazioni
)

st.sidebar.metric(
    "👥 Persone quest'anno",
    anno_persone
)


# ============================================================
# ARCHIVIO
# ============================================================

st.sidebar.markdown("---")

st.sidebar.header("📚 Archivio Prenotazioni")

tipo_archivio = st.sidebar.radio(
    "Visualizza per:",
    [
        "Giorno",
        "Mese",
        "Anno"
    ]
)


# ------------------------------------------------------------
# DATE DISPONIBILI NEL DATABASE
# ------------------------------------------------------------

date_database = sorted(
    list(
        set(
            chiave.split("|")[0]
            for chiave in db_prenotazioni.keys()
            if "|" in chiave
        )
    ),
    reverse=True
)


# ------------------------------------------------------------
# ARCHIVIO GIORNO
# ------------------------------------------------------------

if tipo_archivio == "Giorno":

    if date_database:

        data_archivio_stringa = st.sidebar.selectbox(
            "Seleziona giorno:",
            date_database
        )

        risultati_archivio = [
            p for p in prenotazioni_giornaliere(
                db_prenotazioni,
                data_archivio_stringa
            )
        ]

        st.sidebar.caption(
            f"📅 {data_archivio_stringa}"
        )

        st.sidebar.write(
            f"Prenotazioni: {len(risultati_archivio)}"
        )

        st.sidebar.write(
            "Persone: "
            + str(
                sum(
                    int(p["persone"])
                    for p in risultati_archivio
                    if p["stato"] != "Cancellato"
                )
            )
        )

    else:

        data_archivio_stringa = None

        st.sidebar.info(
            "Nessuna prenotazione archiviata."
        )


# ------------------------------------------------------------
# ARCHIVIO MESE
# ------------------------------------------------------------

elif tipo_archivio == "Mese":

    mesi_database = sorted(
        list(
            set(
                chiave.split("|")[0][:7]
                for chiave in db_prenotazioni.keys()
                if "|" in chiave
            )
        ),
        reverse=True
    )

    if mesi_database:

        mese_archivio = st.sidebar.selectbox(
            "Seleziona mese:",
            mesi_database
        )

        prenotazioni_mese_archivio = []

        for chiave, dati in db_prenotazioni.items():

            if chiave.startswith(mese_archivio):

                parti = chiave.split("|")

                if len(parti) == 3:

                    prenotazioni_mese_archivio.append({
                        "data": parti[0],
                        "turno": parti[1],
                        "tavolo": parti[2],
                        "cliente": dati.get("cliente", ""),
                        "tel": dati.get("tel", ""),
                        "persone": dati.get("persone", 2),
                        "note": dati.get("note", ""),
                        "stato": dati.get("stato", "Prenotato")
                    })

        st.sidebar.caption(
            f"🗓️ {mese_archivio}"
        )

        st.sidebar.write(
            f"Prenotazioni: "
            f"{len([p for p in prenotazioni_mese_archivio if p['stato'] != 'Cancellato'])}"
        )

        st.sidebar.write(
            "Persone: "
            + str(
                sum(
                    int(p["persone"])
                    for p in prenotazioni_mese_archivio
                    if p["stato"] != "Cancellato"
                )
            )
        )

    else:

        mese_archivio = None

        st.sidebar.info(
            "Nessuna prenotazione archiviata."
        )


# ------------------------------------------------------------
# ARCHIVIO ANNO
# ------------------------------------------------------------

else:

    anni_database = sorted(
        list(
            set(
                chiave.split("|")[0][:4]
                for chiave in db_prenotazioni.keys()
                if "|" in chiave
            )
        ),
        reverse=True
    )

    if anni_database:

        anno_archivio = st.sidebar.selectbox(
            "Seleziona anno:",
            anni_database
        )

        prenotazioni_anno_archivio = []

        for chiave, dati in db_prenotazioni.items():

            if chiave.startswith(anno_archivio):

                parti = chiave.split("|")

                if len(parti) == 3:

                    prenotazioni_anno_archivio.append({
                        "data": parti[0],
                        "turno": parti[1],
                        "tavolo": parti[2],
                        "cliente": dati.get("cliente", ""),
                        "tel": dati.get("tel", ""),
                        "persone": dati.get("persone", 2),
                        "note": dati.get("note", ""),
                        "stato": dati.get("stato", "Prenotato")
                    })

        st.sidebar.caption(
            f"👑 {anno_archivio}"
        )

        st.sidebar.write(
            f"Prenotazioni: "
            f"{len([p for p in prenotazioni_anno_archivio if p['stato'] != 'Cancellato'])}"
        )

        st.sidebar.write(
            "Persone: "
            + str(
                sum(
                    int(p["persone"])
                    for p in prenotazioni_anno_archivio
                    if p["stato"] != "Cancellato"
                )
            )
        )

    else:

        anno_archivio = None

        st.sidebar.info(
            "Nessuna prenotazione archiviata."
        )


# ============================================================
# RESET DATABASE PROTETTO
# ============================================================

st.sidebar.markdown("---")

st.sidebar.header("🔐 Strumenti di Sistema")

with st.sidebar.expander("⚠️ Reset Database"):

    st.warning(
        "Questa operazione cancella tutte "
        "le prenotazioni dal database."
    )

    password_reset = st.text_input(
        "Password amministratore:",
        type="password",
        key="password_reset"
    )

    conferma_reset = st.checkbox(
        "Confermo di voler cancellare tutte le prenotazioni",
        key="conferma_reset"
    )

    if st.button(
        "🗑️ RESETTA DATABASE",
        use_container_width=True
    ):

        password_corretta = hmac.compare_digest(
            password_reset,
            RESET_PASSWORD
        )

        if not password_corretta:

            st.error(
                "❌ Password non corretta."
            )

        elif not conferma_reset:

            st.error(
                "❌ Devi confermare il reset."
            )

        else:

            # Backup definitivo prima del reset
            if os.path.exists(DB_FILE):

                try:
                    shutil.copy2(
                        DB_FILE,
                        BACKUP_FILE
                    )
                except Exception:
                    pass

                os.remove(DB_FILE)

            st.success(
                "✅ Database resettato."
            )

            st.rerun()


# ============================================================
# RICERCA
# ============================================================

st.header("🔎 Cerca Prenotazione")

ricerca = st.text_input(
    "Cerca per cognome o numero di telefono",
    placeholder="es. Rossi oppure 347123456"
)

if ricerca.strip():

    risultati = trova_prenotazioni(
        db_prenotazioni,
        ricerca
    )

    if risultati:

        st.success(
            f"🔎 Trovate {len(risultati)} prenotazioni"
        )

        for risultato in risultati:

            with st.container(border=True):

                c1, c2, c3, c4 = st.columns(
                    [1.2, 2, 2, 1]
                )

                with c1:

                    st.markdown(
                        f"### {risultato['data']}"
                    )

                    st.write(
                        f"🪑 {risultato['tavolo']}"
                    )

                with c2:

                    st.markdown(
                        f"**👤 {risultato['cliente']}**"
                    )

                    st.write(
                        f"👥 {risultato['persone']} persone"
                    )

                    st.write(
                        f"📞 {risultato['tel']}"
                    )

                with c3:

                    st.write(
                        f"🕐 {risultato['turno']}"
                    )

                    if risultato["note"]:

                        st.caption(
                            f"📝 {risultato['note']}"
                        )

                with c4:

                    if risultato["stato"] == "Arrivato":

                        st.success(
                            "🟢 ARRIVATO"
                        )

                    elif risultato["stato"] == "Cancellato":

                        st.error(
                            "⚫ CANCELLATO"
                        )

                    else:

                        st.warning(
                            "🟠 PRENOTATO"
                        )

    else:

        st.warning(
            "Nessuna prenotazione trovata."
        )


st.markdown("---")


# ============================================================
# SELEZIONE DATA
# ============================================================

st.header("📆 Selezione Data")

oggi_completo = datetime.now()

data_selezionata = st.date_input(
    "Scegli il giorno:",
    value=oggi_completo.date()
)

data_chiave = data_selezionata.isoformat()


# ============================================================
# CONTROLLO LUNEDÌ
# ============================================================

if data_selezionata.weekday() == 0:

    st.error(
        "🚨 La data selezionata è un lunedì: "
        "il ristorante è CHIUSO."
    )

    st.stop()


TURNI = ottieni_turni_del_giorno(
    data_selezionata
)


# ============================================================
# RIEPILOGO GIORNATA
# ============================================================

prenotazioni_oggi = prenotazioni_giornaliere(
    db_prenotazioni,
    data_chiave
)

prenotazioni_attive = [
    p for p in prenotazioni_oggi
    if p["stato"] != "Cancellato"
]

numero_prenotazioni = len(
    prenotazioni_attive
)

numero_persone = sum(
    int(p["persone"])
    for p in prenotazioni_attive
)

st.subheader(
    "📋 Riepilogo del "
    + data_selezionata.strftime("%d/%m/%Y")
)

r1, r2, r3 = st.columns(3)

with r1:

    st.metric(
        "📌 Prenotazioni",
        numero_prenotazioni
    )

with r2:

    st.metric(
        "👥 Persone",
        numero_persone
    )

with r3:

    posti_totali = sum(
        TAVOLI_MAPPATURA.values()
    )

    st.metric(
        "🪑 Posti totali",
        posti_totali
    )


# ============================================================
# NUOVA PRENOTAZIONE
# ============================================================

st.header("📌 Inserisci Nuova Prenotazione")


# ============================================================
# PRESELEZIONE DAL TABELLONE
# ============================================================

turno_preselezionato = st.session_state.get(
    "pre_turno"
)

tavolo_preselezionato = st.session_state.get(
    "pre_tavolo"
)

if turno_preselezionato:

    st.info(
        f"📌 Prenotazione rapida selezionata: "
        f"**{tavolo_preselezionato}** — "
        f"**{turno_preselezionato}**"
    )


lista_turni = list(TURNI.keys())

if (
    turno_preselezionato
    and turno_preselezionato in lista_turni
):

    indice_turno_default = lista_turni.index(
        turno_preselezionato
    )

else:

    indice_turno_default = 0


col_turno_sel, col1, col2, col3 = st.columns(4)


with col_turno_sel:

    turno_selezionato = st.selectbox(
        "In quale turno inserire:",
        lista_turni,
        index=indice_turno_default,
        key="nuova_prenotazione_turno"
    )


with col1:

    cognome = st.text_input(
        "Cognome Cliente",
        placeholder="es. Rossi",
        key="nuova_prenotazione_cognome"
    ).strip()


with col2:

    telefono = st.text_input(
        "Numero di Telefono",
        placeholder="es. 347123456",
        key="nuova_prenotazione_tel"
    ).strip()


with col3:

    persone = st.number_input(
        "Numero di Persone",
        min_value=1,
        max_value=4,
        value=2,
        step=1,
        key="nuova_prenotazione_persone"
    )


st.markdown(
    "**Allergie o richieste speciali:**"
)

col_g, col_l, col_n = st.columns(3)

with col_g:

    glutine = st.checkbox(
        "Intolleranza al Glutine",
        key="nuova_glutine"
    )


with col_l:

    lattosio = st.checkbox(
        "Intolleranza al Lattosio",
        key="nuova_lattosio"
    )


with col_n:

    altre_note = st.text_input(
        "Note aggiuntive",
        placeholder="es. Seggiolone...",
        key="nuova_note"
    )


# ============================================================
# TAVOLI DISPONIBILI
# ============================================================

bord_disponibili = []

for t_nome, cap_max in TAVOLI_MAPPATURA.items():

    chiave_corrente = (
        f"{data_chiave}|"
        f"{turno_selezionato}|"
        f"{t_nome}"
    )

    if chiave_corrente not in db_prenotazioni:

        if tavolo_compatibile(
            t_nome,
            persone,
            TAVOLI_MAPPATURA
        ):

            bord_disponibili.append(
                t_nome
            )


if bord_disponibili:

    # Se il tavolo selezionato dal tabellone
    # è ancora disponibile, lo mettiamo come default
    if (
        tavolo_preselezionato
        in bord_disponibili
    ):

        indice_tavolo_default = (
            bord_disponibili.index(
                tavolo_preselezionato
            )
        )

    else:

        indice_tavolo_default = 0


    bord_scelto = st.selectbox(
        "🪑 Seleziona tavolo:",
        bord_disponibili,
        index=indice_tavolo_default,
        key="nuova_prenotazione_tavolo"
    )


    if st.button(
        "✅ CONFERMA PRENOTAZIONE",
        use_container_width=True
    ):

        if not cognome:

            st.error(
                "⚠️ Inserisci il cognome del cliente."
            )

        else:

            lista_note = []

            if glutine:

                lista_note.append(
                    "⚠️ SENZA GLUTINE"
                )

            if lattosio:

                lista_note.append(
                    "⚠️ SENZA LATTOSIO"
                )

            if altre_note.strip():

                lista_note.append(
                    altre_note.strip()
                )

            nota_finale = " | ".join(
                lista_note
            )

            db_aggiornato = carica_database()

            chiave_salvataggio = (
                f"{data_chiave}|"
                f"{turno_selezionato}|"
                f"{bord_scelto}"
            )

            # Controllo finale contro doppia prenotazione
            if chiave_salvataggio in db_aggiornato:

                st.error(
                    "❌ Questo tavolo è stato appena prenotato."
                )

            else:

                db_aggiornato[
                    chiave_salvataggio
                ] = {

                    "cliente":
                        cognome,

                    "tel":
                        telefono,

                    "persone":
                        int(persone),

                    "note":
                        nota_finale,

                    "stato":
                        "Prenotato"
                }

                salva_database(
                    db_aggiornato
                )

                # Reset della prenotazione rapida
                st.session_state[
                    "pre_turno"
                ] = None

                st.session_state[
                    "pre_tavolo"
                ] = None

                st.success(
                    f"✅ Prenotazione salvata: "
                    f"{cognome} — {bord_scelto}"
                )

                st.rerun()

else:

    st.warning(
        "⚠️ Nessun tavolo disponibile "
        "per il numero di persone selezionato "
        "in questo turno."
    )


# ============================================================
# MODIFICA PRENOTAZIONE
# ============================================================

st.markdown("---")

st.header("✏️ Modifica Prenotazione")

prenotazioni_modificabili = [
    p for p in prenotazioni_oggi
    if p["stato"] != "Cancellato"
]


if prenotazioni_modificabili:

    opzioni_modifica = []

    for p in prenotazioni_modificabili:

        opzioni_modifica.append(
            f"{p['tavolo']} — "
            f"{p['cliente']} — "
            f"{p['persone']} pers. — "
            f"{p['turno']}"
        )


    scelta_modifica = st.selectbox(
        "Seleziona la prenotazione:",
        opzioni_modifica,
        key="selezione_modifica"
    )


    indice_modifica = opzioni_modifica.index(
        scelta_modifica
    )


    prenotazione_selezionata = (
        prenotazioni_modificabili[
            indice_modifica
        ]
    )


    with st.expander(
        "📝 Apri modifica prenotazione",
        expanded=True
    ):

        col_a, col_b = st.columns(2)

        with col_a:

            nuovo_cliente = st.text_input(
                "Cognome",
                value=prenotazione_selezionata[
                    "cliente"
                ],
                key="mod_cliente"
            )

            nuovo_telefono = st.text_input(
                "Telefono",
                value=prenotazione_selezionata[
                    "tel"
                ],
                key="mod_tel"
            )


        with col_b:

            nuova_persone = st.number_input(
                "Numero persone",
                min_value=1,
                max_value=4,
                value=int(
                    prenotazione_selezionata[
                        "persone"
                    ]
                ),
                key="mod_persone"
            )


            indice_turno = lista_turni.index(
                prenotazione_selezionata[
                    "turno"
                ]
            )


            nuovo_turno = st.selectbox(
                "Turno",
                lista_turni,
                index=indice_turno,
                key="mod_turno"
            )


        # --------------------------------------------
        # TAVOLI DISPONIBILI PER LA MODIFICA
        # --------------------------------------------

        tavoli_modifica = []

        for t_nome, capienza in TAVOLI_MAPPATURA.items():

            nuova_chiave = (
                f"{data_chiave}|"
                f"{nuovo_turno}|"
                f"{t_nome}"
            )

            chiave_vecchia = (
                prenotazione_selezionata[
                    "chiave"
                ]
            )

            if nuova_chiave == chiave_vecchia:

                if tavolo_compatibile(
                    t_nome,
                    nuova_persone,
                    TAVOLI_MAPPATURA
                ):

                    tavoli_modifica.append(
                        t_nome
                    )

            elif nuova_chiave not in db_prenotazioni:

                if tavolo_compatibile(
                    t_nome,
                    nuova_persone,
                    TAVOLI_MAPPATURA
                ):

                    tavoli_modifica.append(
                        t_nome
                    )


        if tavoli_modifica:

            if (
                prenotazione_selezionata[
                    "tavolo"
                ] in tavoli_modifica
            ):

                indice_tavolo = (
                    tavoli_modifica.index(
                        prenotazione_selezionata[
                            "tavolo"
                        ]
                    )
                )

            else:

                indice_tavolo = 0


            nuovo_tavolo = st.selectbox(
                "🪑 Tavolo",
                tavoli_modifica,
                index=indice_tavolo,
                key="mod_tavolo"
            )


            nuove_note = st.text_input(
                "Note / allergie",
                value=prenotazione_selezionata[
                    "note"
                ],
                key="mod_note"
            )


            if st.button(
                "💾 SALVA MODIFICHE",
                use_container_width=True
            ):

                if not nuovo_cliente.strip():

                    st.error(
                        "❌ Inserisci il cognome."
                    )

                else:

                    db_modifica = carica_database()

                    vecchia_chiave = (
                        prenotazione_selezionata[
                            "chiave"
                        ]
                    )

                    nuova_chiave = (
                        f"{data_chiave}|"
                        f"{nuovo_turno}|"
                        f"{nuovo_tavolo}"
                    )


                    if (
                        nuova_chiave != vecchia_chiave
                        and nuova_chiave in db_modifica
                    ):

                        st.error(
                            "❌ Il nuovo tavolo "
                            "non è disponibile."
                        )

                    else:

                        if (
                            nuova_chiave
                            != vecchia_chiave
                        ):

                            del db_modifica[
                                vecchia_chiave
                            ]


                        db_modifica[
                            nuova_chiave
                        ] = {

                            "cliente":
                                nuovo_cliente.strip(),

                            "tel":
                                nuovo_telefono.strip(),

                            "persone":
                                int(nuova_persone),

                            "note":
                                nuove_note.strip(),

                            "stato":
                                prenotazione_selezionata[
                                    "stato"
                                ]
                        }


                        salva_database(
                            db_modifica
                        )

                        st.success(
                            "✅ Prenotazione modificata."
                        )

                        st.rerun()

        else:

            st.error(
                "❌ Nessun tavolo disponibile "
                "per questa modifica."
            )

else:

    st.info(
        "Nessuna prenotazione attiva "
        "per questa giornata."
    )


# ============================================================
# TABELLONE
# ============================================================

st.markdown("---")

st.header(
    "🪟 Tabellone del "
    + data_selezionata.strftime("%d/%m/%Y")
)


lista_turni_del_giorno = list(
    TURNI.keys()
)

numero_colonne = len(
    lista_turni_del_giorno
)


for t_nome, cap_max in TAVOLI_MAPPATURA.items():

    st.markdown(
        f"### 🪑 {t_nome} — {cap_max} posti"
    )

    colonne_turno = st.columns(
        numero_colonne
    )


    for indice, t_nome_orario in enumerate(
        lista_turni_del_giorno
    ):

        with colonne_turno[indice]:

            chiave_specifica = (
                f"{data_chiave}|"
                f"{t_nome_orario}|"
                f"{t_nome}"
            )


            # =================================================
            # TAVOLO OCCUPATO
            # =================================================

            if chiave_specifica in db_prenotazioni:

                info_p = db_prenotazioni[
                    chiave_specifica
                ]

                stato = info_p.get(
                    "stato",
                    "Prenotato"
                )


                st.caption(
                    t_nome_orario
                )


                if stato == "Arrivato":

                    st.success(
                        "🟢 ARRIVATO"
                    )

                elif stato == "Cancellato":

                    st.error(
                        "⚫ CANCELLATO"
                    )

                else:

                    st.warning(
                        "🟠 PRENOTATO"
                    )


                st.write(
                    f"👤 **{info_p.get('cliente', '')}**"
                )

                st.write(
                    f"👥 {info_p.get('persone', 2)} persone"
                )

                st.write(
                    f"📞 {info_p.get('tel', '')}"
                )


                if info_p.get("note"):

                    st.caption(
                        f"📝 {info_p['note']}"
                    )


                # --------------------------------------------
                # ARRIVATO
                # --------------------------------------------

                if stato == "Prenotato":

                    if st.button(
                        "🟢 Arrivato",
                        key=f"arr_{chiave_specifica}",
                        use_container_width=True
                    ):

                        db_stato = carica_database()

                        if chiave_specifica in db_stato:

                            db_stato[
                                chiave_specifica
                            ]["stato"] = "Arrivato"

                            salva_database(
                                db_stato
                            )

                        st.rerun()


                # --------------------------------------------
                # RIPRISTINA
                # --------------------------------------------

                elif stato == "Arrivato":

                    if st.button(
                        "↩️ Ripristina",
                        key=f"rip_{chiave_specifica}",
                        use_container_width=True
                    ):

                        db_stato = carica_database()

                        if chiave_specifica in db_stato:

                            db_stato[
                                chiave_specifica
                            ]["stato"] = "Prenotato"

                            salva_database(
                                db_stato
                            )

                        st.rerun()


                # --------------------------------------------
                # CANCELLA
                # --------------------------------------------

                if stato != "Cancellato":

                    if st.button(
                        "❌ Cancella",
                        key=f"del_{chiave_specifica}",
                        use_container_width=True
                    ):

                        db_cancella = carica_database()

                        if chiave_specifica in db_cancella:

                            db_cancella[
                                chiave_specifica
                            ]["stato"] = "Cancellato"

                            salva_database(
                                db_cancella
                            )

                        st.rerun()


                # --------------------------------------------
                # ELIMINAZIONE DEFINITIVA
                # --------------------------------------------

                with st.expander(
                    "⚠️ Eliminazione definitiva"
                ):

                    st.caption(
                        "Elimina completamente "
                        "questa prenotazione."
                    )

                    if st.button(
                        "🗑️ Elimina definitivamente",
                        key=f"harddel_{chiave_specifica}",
                        use_container_width=True
                    ):

                        db_elimina = carica_database()

                        if chiave_specifica in db_elimina:

                            del db_elimina[
                                chiave_specifica
                            ]

                            salva_database(
                                db_elimina
                            )

                        st.rerun()


            # =================================================
            # TAVOLO LIBERO
            # =================================================

            else:

                st.success(
                    "🟢 LIBERO"
                )

                st.caption(
                    t_nome_orario
                )


                # --------------------------------------------
                # PRENOTAZIONE RAPIDA
                # --------------------------------------------

                if st.button(
                    "➕ Prenota",
                    key=f"book_{chiave_specifica}",
                    use_container_width=True
                ):

                    st.session_state[
                        "pre_turno"
                    ] = t_nome_orario

                    st.session_state[
                        "pre_tavolo"
                    ] = t_nome

                    # Torna in cima alla pagina
                    # con turno e tavolo già selezionati
                    st.rerun()


    st.markdown(
        "<hr style='margin: 10px 0; "
        "border: 0.5px solid #444;'>",
        unsafe_allow_html=True
    )


# ============================================================
# RIEPILOGO PER TURNO
# ============================================================

st.markdown("---")

st.header("📊 Riepilogo per Turno")


for turno in TURNI.keys():

    prenotazioni_turno = []

    for p in prenotazioni_oggi:

        if (
            p["turno"] == turno
            and p["stato"] != "Cancellato"
        ):

            prenotazioni_turno.append(p)


    numero_tavoli = len(
        prenotazioni_turno
    )

    persone_turno = sum(
        int(p["persone"])
        for p in prenotazioni_turno
    )


    col_a, col_b, col_c = st.columns(3)


    with col_a:

        st.markdown(
            f"**{turno}**"
        )


    with col_b:

        st.write(
            f"🪑 {numero_tavoli} tavoli"
        )


    with col_c:

        st.write(
            f"👥 {persone_turno} persone"
        )


# ============================================================
# ARCHIVIO VISIBILE
# ============================================================

st.markdown("---")

st.header("📚 Consultazione Archivio")


if tipo_archivio == "Giorno":

    if data_archivio_stringa:

        dati_archivio = prenotazioni_giornaliere(
            db_prenotazioni,
            data_archivio_stringa
        )

        if dati_archivio:

            st.subheader(
                f"📅 Prenotazioni del "
                f"{data_archivio_stringa}"
            )

            for p in dati_archivio:

                with st.container(border=True):

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.write(
                            f"🪑 **{p['tavolo']}**"
                        )

                        st.write(
                            p["turno"]
                        )

                    with c2:

                        st.write(
                            f"👤 **{p['cliente']}**"
                        )

                        st.write(
                            f"👥 {p['persone']} persone"
                        )

                        st.write(
                            f"📞 {p['tel']}"
                        )

                    with c3:

                        if p["stato"] == "Arrivato":

                            st.success(
                                "🟢 ARRIVATO"
                            )

                        elif p["stato"] == "Cancellato":

                            st.error(
                                "⚫ CANCELLATO"
                            )

                        else:

                            st.warning(
                                "🟠 PRENOTATO"
                            )

                        if p["note"]:

                            st.caption(
                                f"📝 {p['note']}"
                            )

        else:

            st.info(
                "Nessuna prenotazione per questo giorno."
            )


elif tipo_archivio == "Mese":

    if mese_archivio:

        dati_archivio = []

        for chiave, dati in db_prenotazioni.items():

            if chiave.startswith(mese_archivio):

                parti = chiave.split("|")

                if len(parti) == 3:

                    dati_archivio.append({
                        "data": parti[0],
                        "turno": parti[1],
                        "tavolo": parti[2],
                        "cliente": dati.get("cliente", ""),
                        "tel": dati.get("tel", ""),
                        "persone": dati.get("persone", 2),
                        "note": dati.get("note", ""),
                        "stato": dati.get("stato", "Prenotato")
                    })


        dati_archivio.sort(
            key=lambda x: (
                x["data"],
                x["turno"]
            )
        )


        if dati_archivio:

            st.subheader(
                f"🗓️ Prenotazioni del mese "
                f"{mese_archivio}"
            )


            for p in dati_archivio:

                with st.container(border=True):

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.write(
                            f"📅 **{p['data']}**"
                        )

                        st.write(
                            f"🪑 {p['tavolo']}"
                        )

                    with c2:

                        st.write(
                            f"👤 **{p['cliente']}**"
                        )

                        st.write(
                            f"👥 {p['persone']} persone"
                        )

                    with c3:

                        st.write(
                            p["turno"]
                        )

                        if p["stato"] == "Arrivato":

                            st.success(
                                "🟢 ARRIVATO"
                            )

                        elif p["stato"] == "Cancellato":

                            st.error(
                                "⚫ CANCELLATO"
                            )

                        else:

                            st.warning(
                                "🟠 PRENOTATO"
                            )


        else:

            st.info(
                "Nessuna prenotazione per questo mese."
            )


else:

    if anno_archivio:

        dati_archivio = []

        for chiave, dati in db_prenotazioni.items():

            if chiave.startswith(anno_archivio):

                parti = chiave.split("|")

                if len(parti) == 3:

                    dati_archivio.append({
                        "data": parti[0],
                        "turno": parti[1],
                        "tavolo": parti[2],
                        "cliente": dati.get("cliente", ""),
                        "tel": dati.get("tel", ""),
                        "persone": dati.get("persone", 2),
                        "note": dati.get("note", ""),
                        "stato": dati.get("stato", "Prenotato")
                    })


        dati_archivio.sort(
            key=lambda x: (
                x["data"],
                x["turno"]
            )
        )


        if dati_archivio:

            st.subheader(
                f"👑 Prenotazioni dell'anno "
                f"{anno_archivio}"
            )


            for p in dati_archivio:

                with st.container(border=True):

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.write(
                            f"📅 **{p['data']}**"
                        )

                        st.write(
                            f"🪑 {p['tavolo']}"
                        )

                    with c2:

                        st.write(
                            f"👤 **{p['cliente']}**"
                        )

                        st.write(
                            f"👥 {p['persone']} persone"
                        )

                    with c3:

                        st.write(
                            p["turno"]
                        )

                        if p["stato"] == "Arrivato":

                            st.success(
                                "🟢 ARRIVATO"
                            )

                        elif p["stato"] == "Cancellato":

                            st.error(
                                "⚫ CANCELLATO"
                            )

                        else:

                            st.warning(
                                "🟠 PRENOTATO"
                            )

        else:

            st.info(
                "Nessuna prenotazione per questo anno."
            )
```
