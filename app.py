import streamlit as st
from datetime import datetime, time
import json
import os
import shutil
import hmac

st.set_page_config(page_title="Bokningscentral", layout="wide")
st.title("📞 Bokningscentral – Telefonbokningar")

DB_FILE = "stato_bord.json"
BACKUP_FILE = "stato_bord_backup.json"
RESET_PASSWORD = "Samuelmark123#"


# ============================================================
# DATABAS
# ============================================================

def ladda_databas():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key, value in data.items():
                value.setdefault("personer", 2)
                value.setdefault("status", "Bokad")
                value.setdefault("anteckningar", value.get("note", ""))
                value.setdefault("telefon", value.get("tel", ""))
                value.setdefault("kund", value.get("cliente", ""))

            return data
        except Exception:
            return {}
    return {}


def spara_databas(db):
    if os.path.exists(DB_FILE):
        try:
            shutil.copy2(DB_FILE, BACKUP_FILE)
        except Exception:
            pass

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


db = ladda_databas()


# ============================================================
# TIDER
# ============================================================

def dagens_pass(datum):
    veckodag = datum.weekday()

    if veckodag == 6:  # Söndag
        return {
            "Lunch – Pass 1 (12:00–14:00)": {"start": time(12, 0), "slut": time(14, 0)},
            "Lunch – Pass 2 (13:00–15:00)": {"start": time(13, 0), "slut": time(15, 0)},
            "Middag – Pass 1 (16:00–18:00)": {"start": time(16, 0), "slut": time(18, 0)},
            "Middag – Pass 2 (18:00–20:00)": {"start": time(18, 0), "slut": time(20, 0)},
            "Middag – Pass 3 (20:00–22:00)": {"start": time(20, 0), "slut": time(22, 0)},
        }

    if veckodag in (4, 5):  # Fredag/Lördag
        return {
            "Lunch – Pass 1 (11:00–13:00)": {"start": time(11, 0), "slut": time(13, 0)},
            "Lunch – Pass 2 (13:00–15:00)": {"start": time(13, 0), "slut": time(15, 0)},
            "Middag – Pass 1 (16:00–18:00)": {"start": time(16, 0), "slut": time(18, 0)},
            "Middag – Pass 2 (18:00–20:00)": {"start": time(18, 0), "slut": time(20, 0)},
            "Middag – Pass 3 (20:00–22:00)": {"start": time(20, 0), "slut": time(22, 0)},
            "Middag – Pass 4 (21:00–23:00)": {"start": time(21, 0), "slut": time(23, 0)},
        }

    return {
        "Lunch – Pass 1 (11:00–13:00)": {"start": time(11, 0), "slut": time(13, 0)},
        "Lunch – Pass 2 (13:00–15:00)": {"start": time(13, 0), "slut": time(15, 0)},
        "Middag – Pass 1 (16:00–18:00)": {"start": time(16, 0), "slut": time(18, 0)},
        "Middag – Pass 2 (18:00–20:00)": {"start": time(18, 0), "slut": time(20, 0)},
        "Middag – Pass 3 (20:00–22:00)": {"start": time(20, 0), "slut": time(22, 0)},
    }


# ============================================================
# BORD
# ============================================================

BORD = {}
for i in range(1, 4):
    BORD[f"Bord {i}"] = 2
for i in range(4, 11):
    BORD[f"Bord {i}"] = 4


def kompatibelt_bord(bord, personer):
    return BORD[bord] == 2 if personer <= 2 else BORD[bord] == 4


def bokningsnyckel(datum, passnamn, bord):
    return f"{datum}|{passnamn}|{bord}"


def dela_nyckel(key):
    delar = key.split("|")
    return delar if len(delar) == 3 else ["", "", ""]


def aktiva_bokningar(db, prefix=None):
    resultat = []
    for key, info in db.items():
        if prefix and not key.startswith(prefix):
            continue
        if info.get("status", "Bokad") == "Avbokad":
            continue
        datum, passnamn, bord = dela_nyckel(key)
        if not datum:
            continue
        resultat.append({
            "key": key,
            "datum": datum,
            "pass": passnamn,
            "bord": bord,
            "kund": info.get("kund", info.get("cliente", "")),
            "telefon": info.get("telefon", info.get("tel", "")),
            "personer": int(info.get("personer", 2)),
            "anteckningar": info.get("anteckningar", info.get("note", "")),
            "status": info.get("status", "Bokad"),
        })
    return resultat


def alla_bokningar(db, prefix=None):
    resultat = []
    for key, info in db.items():
        if prefix and not key.startswith(prefix):
            continue
        datum, passnamn, bord = dela_nyckel(key)
        if not datum:
            continue
        resultat.append({
            "key": key,
            "datum": datum,
            "pass": passnamn,
            "bord": bord,
            "kund": info.get("kund", info.get("cliente", "")),
            "telefon": info.get("telefon", info.get("tel", "")),
            "personer": int(info.get("personer", 2)),
            "anteckningar": info.get("anteckningar", info.get("note", "")),
            "status": info.get("status", "Bokad"),
        })
    return resultat


def statistik(db, prefix):
    bokningar = [x for x in aktiva_bokningar(db, prefix)]
    return len(bokningar), sum(x["personer"] for x in bokningar)


# ============================================================
# SESSION STATE
# ============================================================

st.session_state.setdefault("valt_pass", None)
st.session_state.setdefault("valt_bord", None)


# ============================================================
# SIDOPANEL
# ============================================================

st.sidebar.header("📊 Sammanfattning")

idag = datetime.now().date()
idag_str = idag.isoformat()
manad_str = idag.strftime("%Y-%m")
ar_str = idag.strftime("%Y")

b_idag, p_idag = statistik(db, idag_str)
b_manad, p_manad = statistik(db, manad_str)
b_ar, p_ar = statistik(db, ar_str)

st.sidebar.metric("📆 Bokningar idag", b_idag)
st.sidebar.metric("👥 Gäster idag", p_idag)
st.sidebar.metric("🗓️ Bokningar denna månad", b_manad)
st.sidebar.metric("👥 Gäster denna månad", p_manad)
st.sidebar.metric("👑 Bokningar i år", b_ar)
st.sidebar.metric("👥 Gäster i år", p_ar)

st.sidebar.markdown("---")
st.sidebar.header("📚 Bokningsarkiv")

arkivtyp = st.sidebar.selectbox(
    "Visa bokningar efter:",
    ["Dag", "Månad", "År"]
)

datumlista = sorted(
    {dela_nyckel(k)[0] for k in db.keys() if dela_nyckel(k)[0]},
    reverse=True
)

vald_arkivperiod = None

if arkivtyp == "Dag":
    if datumlista:
        vald_arkivperiod = st.sidebar.selectbox("Välj dag:", datumlista)
    else:
        st.sidebar.info("Inga bokningar ännu.")

elif arkivtyp == "Månad":
    manader = sorted({d[:7] for d in datumlista}, reverse=True)
    if manader:
        vald_arkivperiod = st.sidebar.selectbox("Välj månad:", manader)
    else:
        st.sidebar.info("Inga bokningar ännu.")

else:
    ar_lista = sorted({d[:4] for d in datumlista}, reverse=True)
    if ar_lista:
        vald_arkivperiod = st.sidebar.selectbox("Välj år:", ar_lista)
    else:
        st.sidebar.info("Inga bokningar ännu.")


# ============================================================
# SKYDDAT SYSTEMVERKTYG
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("🔐 Systemverktyg")

with st.sidebar.expander("⚠️ Återställ databasen"):
    st.warning("Alla bokningar kommer att tas bort.")

    lösenord = st.text_input(
        "Administratörslösenord",
        type="password",
        key="reset_lösenord"
    )

    bekräfta = st.checkbox(
        "Jag bekräftar att jag vill radera alla bokningar.",
        key="reset_bekräfta"
    )

    if st.button("🗑️ ÅTERSTÄLL DATABASEN", use_container_width=True):
        if not hmac.compare_digest(lösenord, RESET_PASSWORD):
            st.error("❌ Fel lösenord.")
        elif not bekräfta:
            st.error("❌ Bekräfta först.")
        else:
            if os.path.exists(DB_FILE):
                try:
                    shutil.copy2(DB_FILE, BACKUP_FILE)
                except Exception:
                    pass
                os.remove(DB_FILE)
            st.success("✅ Databasen har återställts.")
            st.rerun()


# ============================================================
# SÖK BOKNING
# ============================================================

st.header("🔎 Sök bokning")

sökning = st.text_input(
    "Sök efter efternamn eller telefonnummer",
    placeholder="t.ex. Rossi eller 0701234567"
).strip().lower()

if sökning:
    träffar = [
        x for x in alla_bokningar(db)
        if sökning in x["kund"].lower()
        or sökning in x["telefon"].lower()
    ]

    if träffar:
        st.success(f"🔎 {len(träffar)} bokning(ar) hittades.")
        for x in träffar:
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"📅 **{x['datum']}**")
                    st.write(f"🪑 **{x['bord']}**")
                with c2:
                    st.write(f"👤 **{x['kund']}**")
                    st.write(f"👥 {x['personer']} gäster")
                    st.write(f"📞 {x['telefon']}")
                with c3:
                    st.write(x["pass"])
                    if x["status"] == "Anlänt":
                        st.success("🟢 ANLÄNT")
                    elif x["status"] == "Avbokad":
                        st.error("⚫ AVBOKAD")
                    else:
                        st.warning("🟠 BOKAD")
                    if x["anteckningar"]:
                        st.caption(f"📝 {x['anteckningar']}")
    else:
        st.warning("Ingen bokning hittades.")

st.markdown("---")


# ============================================================
# VÄLJ DATUM
# ============================================================

st.header("📆 Välj datum")

valt_datum = st.date_input(
    "Välj dag:",
    value=idag
)

datum_str = valt_datum.isoformat()

if valt_datum.weekday() == 0:
    st.error("🚨 Måndag – restaurangen är STÄNGD.")
    st.stop()

PASS = dagens_pass(valt_datum)
passlista = list(PASS.keys())


# ============================================================
# DAGENS SAMMANFATTNING
# ============================================================

dagens = aktiva_bokningar(db, datum_str)

st.subheader(f"📋 Sammanfattning {valt_datum.strftime('%d/%m/%Y')}")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("📌 Bokningar", len(dagens))
with c2:
    st.metric("👥 Gäster", sum(x["personer"] for x in dagens))
with c3:
    st.metric("🪑 Antal platser", sum(BORD.values()))


# ============================================================
# NY BOKNING
# ============================================================

st.header("📌 Lägg till ny bokning")

forvald_pass = st.session_state.get("valt_pass")
forvald_bord = st.session_state.get("valt_bord")

pass_index = passlista.index(forvald_pass) if forvald_pass in passlista else 0

c1, c2, c3, c4 = st.columns(4)

with c1:
    valt_pass = st.selectbox(
        "Vilket pass?",
        passlista,
        index=pass_index,
        key="ny_pass"
    )

with c2:
    kund = st.text_input(
        "Kundens efternamn",
        placeholder="t.ex. Rossi",
        key="ny_kund"
    ).strip()

with c3:
    telefon = st.text_input(
        "Telefonnummer",
        placeholder="t.ex. 0701234567",
        key="ny_telefon"
    ).strip()

with c4:
    personer = st.number_input(
        "Antal gäster",
        min_value=1,
        max_value=4,
        value=2,
        step=1,
        key="ny_personer"
    )

st.markdown("**Allergier eller särskilda önskemål:**")

c1, c2, c3 = st.columns(3)

with c1:
    glutenfri = st.checkbox("Glutenfri", key="ny_gluten")

with c2:
    laktosfri = st.checkbox("Laktosfri", key="ny_laktos")

with c3:
    övriga_anteckningar = st.text_input(
        "Övriga anteckningar",
        placeholder="t.ex. barnstol...",
        key="ny_anteckning"
    )

lediga_bord = []

for bord, kapacitet in BORD.items():
    key = bokningsnyckel(datum_str, valt_pass, bord)
    if key not in db and kompatibelt_bord(bord, personer):
        lediga_bord.append(bord)

if lediga_bord:
    bord_index = lediga_bord.index(forvald_bord) if forvald_bord in lediga_bord else 0

    valt_bord = st.selectbox(
        "🪑 Välj bord:",
        lediga_bord,
        index=bord_index,
        key="ny_bord"
    )

    if st.button("✅ BEKRÄFTA BOKNING", use_container_width=True):
        if not kund:
            st.error("⚠️ Ange kundens efternamn.")
        else:
            anteckningar = []
            if glutenfri:
                anteckningar.append("⚠️ GLUTENFRI")
            if laktosfri:
                anteckningar.append("⚠️ LAKTOSFRI")
            if övriga_anteckningar.strip():
                anteckningar.append(övriga_anteckningar.strip())

            nyckel = bokningsnyckel(datum_str, valt_pass, valt_bord)
            aktuell_db = ladda_databas()

            if nyckel in aktuell_db:
                st.error("❌ Bordet har precis blivit bokat.")
            else:
                aktuell_db[nyckel] = {
                    "kund": kund,
                    "telefon": telefon,
                    "personer": int(personer),
                    "anteckningar": " | ".join(anteckningar),
                    "status": "Bokad"
                }

                spara_databas(aktuell_db)
                st.session_state["valt_pass"] = None
                st.session_state["valt_bord"] = None
                st.success(f"✅ Bokning sparad för {kund} – {valt_bord}.")
                st.rerun()
else:
    st.warning("⚠️ Inget ledigt bord för detta antal gäster under detta pass.")


# ============================================================
# REDIGERA BOKNING
# ============================================================

st.markdown("---")
st.header("✏️ Redigera bokning")

redigerbara = [x for x in dagens]

if redigerbara:
    val_redigera = st.selectbox(
        "Välj bokning:",
        [
            f"{x['bord']} – {x['kund']} – {x['personer']} gäster – {x['pass']}"
            for x in redigerbara
        ],
        key="redigera_val"
    )

    idx = [
        f"{x['bord']} – {x['kund']} – {x['personer']} gäster – {x['pass']}"
        for x in redigerbara
    ].index(val_redigera)

    gammal = redigerbara[idx]

    with st.expander("📝 Öppna bokningen för redigering", expanded=True):
        c1, c2 = st.columns(2)

        with c1:
            ny_kund = st.text_input("Efternamn", value=gammal["kund"], key="red_kund")
            ny_telefon = st.text_input("Telefonnummer", value=gammal["telefon"], key="red_tel")

        with c2:
            nya_personer = st.number_input(
                "Antal gäster",
                min_value=1,
                max_value=4,
                value=gammal["personer"],
                key="red_personer"
            )

            ny_pass = st.selectbox(
                "Pass",
                passlista,
                index=passlista.index(gammal["pass"]),
                key="red_pass"
            )

        möjliga_bord = []

        for bord in BORD:
            nyckel = bokningsnyckel(datum_str, ny_pass, bord)
            if nyckel == gammal["key"] or nyckel not in db:
                if kompatibelt_bord(bord, nya_personer):
                    möjliga_bord.append(bord)

        if möjliga_bord:
            bord_index = möjliga_bord.index(gammal["bord"]) if gammal["bord"] in möjliga_bord else 0

            ny_bord = st.selectbox(
                "🪑 Bord",
                möjliga_bord,
                index=bord_index,
                key="red_bord"
            )

            ny_anteckning = st.text_input(
                "Anteckningar / allergier",
                value=gammal["anteckningar"],
                key="red_note"
            )

            if st.button("💾 SPARA ÄNDRINGAR", use_container_width=True):
                if not ny_kund.strip():
                    st.error("❌ Ange efternamn.")
                else:
                    aktuell_db = ladda_databas()
                    nyckel = bokningsnyckel(datum_str, ny_pass, ny_bord)

                    if nyckel != gammal["key"] and nyckel in aktuell_db:
                        st.error("❌ Det valda bordet är inte ledigt.")
                    else:
                        if nyckel != gammal["key"]:
                            del aktuell_db[gammal["key"]]

                        aktuell_db[nyckel] = {
                            "kund": ny_kund.strip(),
                            "telefon": ny_telefon.strip(),
                            "personer": int(nya_personer),
                            "anteckningar": ny_anteckning.strip(),
                            "status": gammal["status"]
                        }

                        spara_databas(aktuell_db)
                        st.success("✅ Bokningen har ändrats.")
                        st.rerun()
        else:
            st.error("❌ Inget bord är tillgängligt för denna ändring.")
else:
    st.info("Inga aktiva bokningar för denna dag.")


# ============================================================
# BORDSÖVERSIKT
# ============================================================

st.markdown("---")
st.header(f"🪟 Bordsöversikt – {valt_datum.strftime('%d/%m/%Y')}")

for bord, kapacitet in BORD.items():
    st.markdown(f"### 🪑 {bord} – {kapacitet} platser")

    kolumner = st.columns(len(passlista))

    for i, passnamn in enumerate(passlista):
        with kolumner[i]:
            key = bokningsnyckel(datum_str, passnamn, bord)
            info = db.get(key)

            st.caption(passnamn)

            if info:
                status = info.get("status", "Bokad")
                kundnamn = info.get("kund", info.get("cliente", ""))
                telefonnummer = info.get("telefon", info.get("tel", ""))
                antal = int(info.get("personer", 2))
                anteckning = info.get("anteckningar", info.get("note", ""))

                if status == "Anlänt":
                    st.success("🟢 ANLÄNT")
                elif status == "Avbokad":
                    st.error("⚫ AVBOKAD")
                else:
                    st.warning("🟠 BOKAD")

                st.write(f"👤 **{kundnamn}**")
                st.write(f"👥 {antal} gäster")
                st.write(f"📞 {telefonnummer}")

                if anteckning:
                    st.caption(f"📝 {anteckning}")

                # Kunden har kommit
                if status == "Bokad":
                    if st.button("🟢 Anlänt", key=f"ankomst_{key}", use_container_width=True):
                        aktuell_db = ladda_databas()
                        if key in aktuell_db:
                            aktuell_db[key]["status"] = "Anlänt"
                            spara_databas(aktuell_db)
                        st.rerun()

                # Återställ ankomststatus
                if status == "Anlänt":
                    if st.button("↩️ Återställ", key=f"aterstall_{key}", use_container_width=True):
                        aktuell_db = ladda_databas()
                        if key in aktuell_db:
                            aktuell_db[key]["status"] = "Bokad"
                            spara_databas(aktuell_db)
                        st.rerun()

                # AVBOKA
                if status != "Avbokad":
                    if st.button("❌ Avboka", key=f"avboka_{key}", use_container_width=True):
                        aktuell_db = ladda_databas()
                        if key in aktuell_db:
                            aktuell_db[key]["status"] = "Avbokad"
                            spara_databas(aktuell_db)
                        st.rerun()

                # FRIGÖR BORD – behåller bokningen i historiken
                with st.expander("🪑 Frigör bord"):
                    st.caption(
                        "Bordet blir ledigt igen. Bokningen sparas i historiken som avbokad."
                    )

                    if st.button("🪑 FRIGÖR BORDET", key=f"frigör_{key}", use_container_width=True):
                        aktuell_db = ladda_databas()
                        if key in aktuell_db:
                            aktuell_db[key]["status"] = "Avbokad"
                            aktuell_db[key]["frigjort"] = True
                            aktuell_db[key]["frigjort_tid"] = datetime.now().isoformat(timespec="seconds")
                            spara_databas(aktuell_db)

                        st.success(f"✅ {bord} är nu ledigt.")
                        st.rerun()

                # PERMANENT RADERING
                with st.expander("⚠️ Permanent radering"):
                    st.caption("Använd endast om bokningen verkligen ska tas bort från databasen.")

                    if st.button("🗑️ Radera permanent", key=f"radera_{key}", use_container_width=True):
                        aktuell_db = ladda_databas()
                        if key in aktuell_db:
                            del aktuell_db[key]
                            spara_databas(aktuell_db)
                        st.rerun()

            else:
                st.success("🟢 LEDIGT")

                if st.button("➕ Boka", key=f"boka_{key}", use_container_width=True):
                    st.session_state["valt_pass"] = passnamn
                    st.session_state["valt_bord"] = bord
                    st.rerun()

    st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #444;'>", unsafe_allow_html=True)


# ============================================================
# SAMMANFATTNING PER PASS
# ============================================================

st.markdown("---")
st.header("📊 Sammanfattning per pass")

for passnamn in passlista:
    passbokningar = [
        x for x in dagens
        if x["pass"] == passnamn
    ]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.write(f"**{passnamn}**")

    with c2:
        st.write(f"🪑 {len(passbokningar)} bord")

    with c3:
        st.write(f"👥 {sum(x['personer'] for x in passbokningar)} gäster")


# ============================================================
# ARKIV
# ============================================================

st.markdown("---")
st.header("📚 Bokningsarkiv")

if vald_arkivperiod:

    arkiv = alla_bokningar(
        db,
        vald_arkivperiod
    )

    if arkiv:
        arkiv.sort(key=lambda x: (x["datum"], x["pass"], x["bord"]))

        for x in arkiv:
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)

                with c1:
                    st.write(f"📅 **{x['datum']}**")
                    st.write(f"🪑 **{x['bord']}**")

                with c2:
                    st.write(f"👤 **{x['kund']}**")
                    st.write(f"👥 {x['personer']} gäster")
                    st.write(f"📞 {x['telefon']}")

                with c3:
                    st.write(x["pass"])

                    if x["status"] == "Anlänt":
                        st.success("🟢 ANLÄNT")
                    elif x["status"] == "Avbokad":
                        st.error("⚫ AVBOKAD")
                    else:
                        st.warning("🟠 BOKAD")

                    if x["anteckningar"]:
                        st.caption(f"📝 {x['anteckningar']}")
    else:
        st.info("Inga bokningar för den valda perioden.")
