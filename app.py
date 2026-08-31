import streamlit as st
from datetime import datetime, time
import json
import os
import copy
import shutil

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
                    if "stato" not in valore:
                        valore["stato"] = "Prenotato"

                return dati

        except Exception:
            return {}

    return {}


def salva_database(db):
    # Backup prima di sovrascrivere il database
    if os.path.exists(DB_FILE):
        try:
            shutil.copy2(DB_FILE, BACKUP_FILE)
        except Exception:
            pass

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


db_prenotazioni = carica_database()


# ============================================================
# FUNZIONI UTILI
# ============================================================

def formatta_turno(turno):
    return turno


def conta_persone(db, data_prefix=None):
    totale = 0

    for chiave, dati in db.items():

        if data_prefix and not chiave.startswith(data_prefix):
            continue

        # Recupera il numero di persone.
        # Compatibilità con vecchie prenotazioni senza questo dato.
        persone = dati.get("persone", 2)

        try:
            totale += int(persone)
        except Exception:
            totale += 2

    return totale


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

        cliente = str(dati.get("cliente", "")).lower()
        telefono = str(dati.get("tel", "")).lower()

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

    risultati.sort(key=lambda x: (x["data"], x["turno"]))

    return risultati


def tavolo_compatibile(tavolo, persone, mappa_tavoli):
    capienza = mappa_tavoli[tavolo]

    if persone <= 2:
        return capienza == 2

    return capienza == 4


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
# SIDEBAR
# ============================================================

st.sidebar.header("📊 Riepilogo")

oggi_dt = datetime.now()
data_oggi_stringa = oggi_dt.date().isoformat()

prefisso_mese = oggi_dt.strftime("%Y-%m")
prefisso_anno = oggi_dt.strftime("%Y-")

totale_giorno = 0
totale_mese = 0
totale_anno = 0

persone_giorno = 0
persone_mese = 0
persone_anno = 0

for chiave_db, dati in db_prenotazioni.items():

    persone = dati.get("persone", 2)

    try:
        persone = int(persone)
    except Exception:
        persone = 2

    if chiave_db.startswith(data_oggi_stringa):
        totale_giorno += 1
        persone_giorno += persone

    if chiave_db.startswith(prefisso_mese):
        totale_mese += 1
        persone_mese += persone

    if chiave_db.startswith(prefisso_anno):
        totale_anno += 1
        persone_anno += persone


st.sidebar.metric(
    "📆 Prenotazioni oggi",
    totale_giorno
)

st.sidebar.metric(
    "👥 Persone oggi",
    persone_giorno
)

st.sidebar.metric(
    "🗓️ Prenotazioni questo mese",
    totale_mese
)

st.sidebar.metric(
    "👥 Persone questo mese",
    persone_mese
)

st.sidebar.metric(
    "👑 Prenotazioni quest'anno",
    totale_anno
)

st.sidebar.markdown(
    "<hr style='margin: 15px 0; border: 0.5px solid #444;'>",
    unsafe_allow_html=True
)


# ============================================================
# RESET DATABASE
# ============================================================

st.sidebar.header("🛠️ Strumenti di Sistema")

if st.sidebar.button(
    "⚠️ RESETTA DATABASE",
    help="Cancella tutte le prenotazioni"
):

    if os.path.exists(DB_FILE):

        try:
            shutil.copy2(DB_FILE, BACKUP_FILE)
        except Exception:
            pass

        os.remove(DB_FILE)

        st.sidebar.success(
            "✅ Database resettato!"
        )

    else:

        st.sidebar.info(
            "Il database è già vuoto."
        )

    st.rerun()


# ============================================================
# RICERCA PRENOTAZIONE
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

                col1, col2, col3, col4 = st.columns(
                    [1.3, 2, 2, 1]
                )

                with col1:
                    st.markdown(
                        f"### {risultato['data']}"
                    )

                    st.write(
                        risultato["tavolo"]
                    )

                with col2:
                    st.markdown(
                        f"**👤 {risultato['cliente']}**"
                    )

                    st.write(
                        f"👥 {risultato['persone']} persone"
                    )

                    st.write(
                        f"📞 {risultato['tel']}"
                    )

                with col3:
                    st.write(
                        f"🕐 {risultato['turno']}"
                    )

                    if risultato["note"]:
                        st.caption(
                            f"📝 {risultato['note']}"
                        )

                with col4:

                    stato = risultato["stato"]

                    if stato == "Arrivato":
                        st.success("🟢 ARRIVATO")

                    elif stato == "Cancellato":
                        st.error("⚫ CANCELLATO")

                    else:
                        st.warning("🟠 PRENOTATO")

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


# Lunedì chiuso
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
# RIEPILOGO DELLA GIORNATA
# ============================================================

prenotazioni_oggi = prenotazioni_giornaliere(
    db_prenotazioni,
    data_chiave
)

prenotazioni_attive = [
    p for p in prenotazioni_oggi
    if p["stato"] != "Cancellato"
]

numero_prenotazioni = len(prenotazioni_attive)

numero_persone = sum(
    int(p["persone"])
    for p in prenotazioni_attive
)

st.subheader(
    f"📋 Riepilogo del {data_selezionata.strftime('%d/%m/%Y')}"
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
        "🪑 Posti disponibili totali",
        posti_totali
    )


# ============================================================
# NUOVA PRENOTAZIONE
# ============================================================

st.header("📌 Inserisci Nuova Prenotazione")

col_turno_sel, col1, col2, col3 = st.columns(4)

with col_turno_sel:

    turno_selezionato = st.selectbox(
        "In quale turno inserire:",
        list(TURNI.keys())
    )

with col1:

    cognome = st.text_input(
        "Cognome Cliente",
        placeholder="es. Rossi"
    ).strip()

with col2:

    telefono = st.text_input(
        "Numero di Telefono",
        placeholder="es. 347123456"
    ).strip()

with col3:

    persone = st.number_input(
        "Numero di Persone",
        min_value=1,
        max_value=4,
        value=2,
        step=1
    )


st.markdown(
    "**Allergie o richieste speciali:**"
)

col_g, col_l, col_n = st.columns(3)

with col_g:

    glutine = st.checkbox(
        "Intolleranza al Glutine"
    )

with col_l:

    lattosio = st.checkbox(
        "Intolleranza al Lattosio"
    )

with col_n:

    altre_note = st.text_input(
        "Note aggiuntive",
        placeholder="es. Seggiolone..."
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
                f"{t_nome} ({cap_max} pers)"
            )


if bord_disponibili:

    bord_scelto_completo = st.selectbox(
        "Seleziona tavolo libero:",
        bord_disponibili
    )

    bord_scelto = bord_scelto_completo.split(" (")[0]

    if st.button(
        "✅ Conferma Prenotazione Tavolo",
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

            db_aggiornato[
                chiave_salvataggio
            ] = {

                "cliente": cognome,

                "tel": telefono,

                "persone": int(persone),

                "note": nota_finale,

                "stato": "Prenotato"
            }

            salva_database(
                db_aggiornato
            )

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
        "Seleziona la prenotazione da modificare:",
        opzioni_modifica
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

            indice_turno = list(
                TURNI.keys()
            ).index(
                prenotazione_selezionata[
                    "turno"
                ]
            )

            nuovo_turno = st.selectbox(
                "Turno",
                list(TURNI.keys()),
                index=indice_turno,
                key="mod_turno"
            )


        st.markdown("**Tavolo**")

        tavoli_modifica = []

        for t_nome, capienza in TAVOLI_MAPPATURA.items():

            nuova_chiave = (
                f"{data_chiave}|"
                f"{nuovo_turno}|"
                f"{t_nome}"
            )

            # Il tavolo originale rimane disponibile
            if (
                nuova_chiave
                == prenotazione_selezionata[
                    "chiave"
                ]
            ):

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

                indice_tavolo = tavoli_modifica.index(
                    prenotazione_selezionata[
                        "tavolo"
                    ]
                )

            else:

                indice_tavolo = 0

            nuovo_tavolo = st.selectbox(
                "Seleziona nuovo tavolo:",
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


            col_salva, col_annulla = st.columns(2)

            with col_salva:

                if st.button(
                    "💾 SALVA MODIFICHE",
                    use_container_width=True
                ):

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
                            "non è più disponibile."
                        )

                    elif not nuovo_cliente.strip():

                        st.error(
                            "❌ Inserisci il cognome."
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
                            "✅ Prenotazione modificata!"
                        )

                        st.rerun()

        else:

            st.error(
                "❌ Nessun tavolo disponibile "
                "per questa modifica."
            )

else:

    st.info(
        "Non ci sono prenotazioni attive "
        "da modificare per questa giornata."
    )


# ============================================================
# TABELLONE GIORNALIERO
# ============================================================

st.markdown("---")

st.header(
    "🪟 Tabellone Stato del Giorno: "
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
        f"### 🪑 {t_nome} "
        f"— {cap_max} posti"
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

            # ------------------------------------------------
            # OCCUPATO
            # ------------------------------------------------

            if chiave_specifica in db_prenotazioni:

                info_p = db_prenotazioni[
                    chiave_specifica
                ]

                stato = info_p.get(
                    "stato",
                    "Prenotato"
                )

                if stato == "Cancellato":

                    st.markdown(
                        "⚫ **CANCELLATO**"
                    )

                elif stato == "Arrivato":

                    st.success(
                        "🟢 ARRIVATO"
                    )

                else:

                    st.warning(
                        "🟠 PRENOTATO"
                    )

                st.caption(
                    t_nome_orario
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
                # STATO ARRIVATO
                # --------------------------------------------

                if stato == "Prenotato":

                    if st.button(
                        "🟢 Arrivato",
                        key=f"arr_{chiave_specifica}",
                        use_container_width=True
                    ):

                        db_stato = carica_database()

                        if (
                            chiave_specifica
                            in db_stato
                        ):

                            db_stato[
                                chiave_specifica
                            ]["stato"] = "Arrivato"

                            salva_database(
                                db_stato
                            )

                        st.rerun()


                # --------------------------------------------
                # RIPRISTINA DA ARRIVATO
                # --------------------------------------------

                elif stato == "Arrivato":

                    if st.button(
                        "↩️ Ripristina",
                        key=f"rip_{chiave_specifica}",
                        use_container_width=True
                    ):

                        db_stato = carica_database()

                        if (
                            chiave_specifica
                            in db_stato
                        ):

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

                if st.button(
                    "❌ Cancella",
                    key=f"del_{chiave_specifica}",
                    use_container_width=True
                ):

                    db_cancella = carica_database()

                    if (
                        chiave_specifica
                        in db_cancella
                    ):

                        # Non eliminiamo subito.
                        # La prenotazione rimane nello storico.
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
                        "Questa operazione elimina "
                        "completamente la prenotazione."
                    )

                    if st.button(
                        "🗑️ Elimina definitivamente",
                        key=f"harddel_{chiave_specifica}",
                        use_container_width=True
                    ):

                        db_elimina = carica_database()

                        if (
                            chiave_specifica
                            in db_elimina
                        ):

                            del db_elimina[
                                chiave_specifica
                            ]

                            salva_database(
                                db_elimina
                            )

                        st.rerun()


            # ------------------------------------------------
            # LIBERO
            # ------------------------------------------------

            else:

                st.success(
                    "🟢 LIBERO"
                )

                st.caption(
                    t_nome_orario
                )

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

                    st.info(
                        "Inserisci la prenotazione "
                        "nel modulo sopra."
                    )


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
