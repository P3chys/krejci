import sqlite3
import hashlib
import os
from base64 import b64encode
from flask import Flask, render_template, redirect, url_for, request, session
from datetime import timedelta, datetime
import flask_mail
import random
import string
import re

app = Flask(__name__) #vytvoří flaskové prostředí

app.secret_key = "njePJU1O55jpHata" #Secret key pro funkčnost sessions
app.permanent_session_lifetime = timedelta(days=5) #Permanentní sessions

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'simakrejci2003@gmail.com' #Odchozí e-mailová adresa
app.config['MAIL_PASSWORD'] = 'elnrgjavnmecfhsp' #Pokud používáte Gmail, vygeneruje vám 16místný textový řetězec, který sem dosadíte
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = flask_mail.Mail(app)

admin_password = "admin" #Heslo administrátora
admin_email = "simakrejci2003@gmail.com" #Na tento e-mail budou chodit zprávy z kontaktní stránky

#Připojení do databáze
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/info", methods=["GET", "POST"])
def info():
    if "username" in session:
        if session["usertype"] == "admin":
            return redirect(url_for("index"))

    #Odeslání zprávy
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        msg = flask_mail.Message("Zpráva z WPP", sender=email, recipients=[admin_email])
        msg.body = message + "\n\nZprávu vám zaslal " + name + ", e-mail: " + email
        mail.send(msg)

        return render_template("info.html", status="odeslano")

    return render_template("info.html")

@app.route("/o_projektu")
def o_projektu():
    return render_template("o_projektu.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/registrace2", methods=["GET", "POST"])
def registrace2():
    #Přesměrování již přihlášeného uživatele
    if "username" in session:
        return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM certifikace")
    certifikace = cur.fetchall()

    #Zpracování formuláře
    if request.method == "POST":
        d_usertype = request.form.get("usertype")
        d_jmeno = request.form.get("jmeno")
        d_prijmeni = request.form.get("prijmeni")
        d_email = request.form.get("email")
        d_datum = request.form.get("datum")
        d_telefon = request.form.get("telefon")
        d_certifikace = request.form.getlist("certifikace")
        d_cena = request.form.get("cena")
        d_ucet = request.form.get("ucet")
        d_username = request.form.get("username")
        d_password = request.form.get("password")
    
        #Kryptografická sůl
        d_salt = b64encode(os.urandom(16)).decode("utf-8")
        d_password += d_salt
    
        #Hashovací funkce
        d_hash = hashlib.sha256(d_password.encode("utf-8")).hexdigest()
    
        #Uživatel se nesmí zaregistrovat jako admin
        if d_username == "admin":
            return render_template("registrace2.html", data="existing", certifikace=certifikace)

        if d_usertype == "student":
            cur.execute("SELECT username FROM student WHERE username=?", [d_username])
            if cur.fetchone() != None: #Student s tímto username již existuje
                return render_template("registrace2.html", data="existing", certifikace=certifikace)
            cur.execute("insert into student (jmeno, prijmeni, email, datum_narozeni, telefon, username, sul, password) values (?, ?, ?, ?, ?, ?, ?, ?);", [d_jmeno, d_prijmeni, d_email, d_datum, d_telefon, d_username, d_salt, d_hash])
        else:
            cur.execute("SELECT username FROM instruktor WHERE username=?", [d_username])
            if cur.fetchone() != None: #Instruktor s tímto username již existuje
                return render_template("registrace2.html", data="existing", certifikace=certifikace)
            cur.execute("insert into instruktor (jmeno, prijmeni, email, datum_narozeni, telefon, cena_za_hodinu, cislo_uctu, username, sul, password) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", [d_jmeno, d_prijmeni, d_email, d_datum, d_telefon, d_cena, d_ucet, d_username, d_salt, d_hash])
    
        conn.commit()

        id_uzivatele = cur.lastrowid

        #Pokud má uživatel nějaké certifikace, uloží se do databáze
        for c in d_certifikace:
            cur.execute("INSERT INTO vlastnim_certifikaci (id_uzivatele, status_uzivatele, id_c) VALUES (?, ?, ?)", [id_uzivatele, d_usertype, c])
            conn.commit()
    
        #Vrati me to na stranku login
        return redirect(url_for("login2"))
    return render_template("registrace2.html", certifikace=certifikace)

@app.route("/login2", methods=["GET", "POST"])
def login2():
    #Přesměrování již přihlášeného uživatele
    if "username" in session:
        return redirect(url_for("index"))

    #Zpracování formuláře
    if request.method == "POST":
        d_username = request.form.get("username")
        d_password = request.form.get("password")
        d_usertype = request.form.get("usertype")
        conn = get_db_connection()
        cur = conn.cursor()

        #Přihlášení admina
        if d_username == "admin":
            if d_password == admin_password:
                session.permanent = True
                session["usertype"] = "admin"
                session["username"] = "admin"
                return redirect(url_for("index"))
            else:
                return render_template("login2.html", data="wrong")
    
        if d_usertype == "student":
            cur.execute("select * from student where username=?",[d_username])
            user = cur.fetchone()
        else:
            cur.execute("select * from instruktor where username=?", [d_username])
            user = cur.fetchone()
        if user is None:
            #Neexistující uživatel
            return render_template("login2.html", data="non-existent")
        else:
            d_password += user["sul"]
            #Porovnání hashů
            if hashlib.sha256(d_password.encode("utf-8")).hexdigest() == user["password"]: #Úspěšně přihlášen
                session.permanent = True

                session["usertype"] = d_usertype
                session["id"] = user["id"]
                session["username"] = user["username"]

                return redirect(url_for("index"))
            else: #Špatné heslo
                return render_template("login2.html", data="wrong")
                
    return render_template("login2.html")

@app.route("/lekce", methods=["GET", "POST"])
def lekce():
    #Přesměrování nepřihlášeného uživatele
    if "username" not in session:
        return redirect(url_for("index"))

    if session["usertype"] == "admin":
        return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()

    #Zobrazení stránky lekce pro instruktora
    if session["usertype"] == "instruktor":

        if request.method == "POST":
            delete = request.form.get("delete")

            #Instruktor vytvořil lekci
            if delete == None:
                editovat = request.form.get("edit")
                nazev = request.form.get("nazev")
                popis = request.form.get("popis")
                datum = request.form.get("datetime")
                trvani = request.form.get("trvani")
                select_misto = request.form.get("select_misto")

                if editovat != "0":
                    cur.execute("DELETE FROM lekce WHERE id_l=?", [editovat])
                    conn.commit()
    
                #Přidat do tabulky nové místo
                if select_misto == "nove":
                    ulice = request.form.get("ulice")
                    cislo_popisne = request.form.get("cislo_popisne")
                    mesto = request.form.get("mesto")
                    psc = request.form.get("psc")
    
                    cur.execute("INSERT INTO misto (ulice, mesto, cislo_popisne, smerovaci_cislo) VALUES (?, ?, ?, ?)", [ulice, mesto, cislo_popisne, psc])
                    conn.commit()
    
                    select_misto = cur.lastrowid
    
                #Přidat novou lekci
                if editovat != "0":
                    cur.execute("INSERT INTO lekce (id_l, nazev, popis, datum, delka_trvani, id_m, id_i) VALUES (?, ?, ?, ?, ?, ?, ?)", [editovat, nazev, popis, datum, trvani, select_misto, session["id"]])            
                else:
                    cur.execute("INSERT INTO lekce (nazev, popis, datum, delka_trvani, id_m, id_i) VALUES (?, ?, ?, ?, ?, ?)", [nazev, popis, datum, trvani, select_misto, session["id"]])            
                conn.commit()

            #Instruktor odstranil lekci
            else:
                cur.execute("DELETE FROM lekce WHERE id_l=?", [delete])
                conn.commit()

        try:
            edit = request.args.get("edit")
        except AttributeError:
            edit = False

        cur.execute("SELECT misto.* FROM misto INNER JOIN lekce ON misto.id_m=lekce.id_m WHERE lekce.id_i=? GROUP BY misto.id_m", [session["id"]])
        mista = cur.fetchall()

        if not edit:
            cur.execute("SELECT lekce_prihlasky.*, student.id AS id_studenta, student.jmeno, student.prijmeni, student.telefon, student.email FROM lekce_prihlasky INNER JOIN student ON lekce_prihlasky.id_s=student.id WHERE lekce_prihlasky.id_i=?", [session["id"]])
            prihlasky = cur.fetchall()
    
            cur.execute("SELECT vlastnim_certifikaci.*, certifikace.licence FROM vlastnim_certifikaci INNER JOIN certifikace ON vlastnim_certifikaci.id_c=certifikace.id_c WHERE status_uzivatele='student'")
            certifikace = cur.fetchall()
        
            #Roztřídit certifikace podle uživatelů
            roztridene_certifikace = {}
            for c in certifikace:
                if c["id_uzivatele"] in roztridene_certifikace.keys():
                    roztridene_certifikace[c["id_uzivatele"]].append(c["licence"])
                else:
                    roztridene_certifikace[c["id_uzivatele"]] = [c["licence"]]
        
            for i in roztridene_certifikace.keys():
                roztridene_certifikace[i] = ", ".join(roztridene_certifikace[i])
        
            cur.execute("SELECT lekce.*, misto.* FROM lekce INNER JOIN misto ON lekce.id_m=misto.id_m WHERE DATE(lekce.datum) >= DATE('now') AND lekce.id_i=? ORDER BY lekce.datum", [session["id"]])
            lekce = [dict(row) for row in cur]
            for i in range(0, len(lekce), 1):
                lekce[i]["datum"] = datetime.strptime(lekce[i]["datum"], '%Y-%m-%dT%H:%M').strftime("%d.%m.%Y %H:%M")
            
            return render_template("lekce_instruktor.html", mista=mista, prihlasky=prihlasky, lekce=lekce, certifikace=roztridene_certifikace, edit=edit)

        else:
            cur.execute("SELECT * FROM lekce WHERE DATE(datum) >= DATE('now') AND id_i=? AND id_l=?", [session["id"], edit])
            lekce = cur.fetchone()
            
            if lekce == None:
                return redirect(url_for("lekce"))

            return render_template("lekce_instruktor.html", mista=mista, lekce=lekce, edit=edit)

    #Zobrazení stránky lekce pro studenta
    #Student provedl akci (Zapsat se/Odhlásit se)
    if request.method == "POST":
        akce = request.form.get("akce")
        id_l = request.form.get("class_id_l")
        id_i = request.form.get("class_id_i")
        #Student se zapsal na lekci
        if akce == "zapsat":
            cur.execute("SELECT * FROM lekce_prihlasky WHERE id_s=? AND id_l=?", [session["id"], id_l])
            prihlaseno = cur.fetchone()
            if prihlaseno is None:
                cur.execute("INSERT INTO lekce_prihlasky (id_s, id_l, id_i) VALUES (?, ?, ?)", [session["id"], id_l, id_i])
                conn.commit()

        #Student se odhlásil z lekce
        else:
            cur.execute("DELETE FROM lekce_prihlasky WHERE id_s=? AND id_l=?", [session["id"], id_l])
            conn.commit()

    #Lekce jsou filtrovány podle adresy
    pouzite_filtry = request.args.getlist("filtry")
    try:
        pouzite_filtry = [int(i) for i in pouzite_filtry]
    except ValueError:
        pouzite_filtry = []

    cur.execute("SELECT misto.* FROM lekce INNER JOIN misto ON lekce.id_m=misto.id_m WHERE DATE(lekce.datum) >= DATE('now') GROUP BY misto.id_m ORDER BY misto.mesto")
    filtry = cur.fetchall()

    cur.execute("SELECT id_l FROM lekce_prihlasky WHERE id_s=?", [session["id"]])
    arr = [dict(row) for row in cur]
    prihlasky = []
    for i in range(0, len(arr), 1):
        prihlasky.append(arr[i]["id_l"])

    sql = "SELECT lekce.*, instruktor.jmeno, instruktor.prijmeni, misto.* FROM lekce INNER JOIN instruktor ON lekce.id_i=instruktor.id INNER JOIN misto ON lekce.id_m=misto.id_m WHERE DATE(lekce.datum) >= DATE('now') AND ("
    for i in range(0, len(pouzite_filtry), 1):
        sql += "misto.id_m=?"
        if i < len(pouzite_filtry) - 1:
            sql += " OR "
    if len(pouzite_filtry) == 0:
        sql += "1=1"
    sql += ") ORDER BY lekce.datum"

    cur.execute(sql, pouzite_filtry)
    lekce = [dict(row) for row in cur]
    for i in range(0, len(lekce), 1):
        lekce[i]["datum"] = datetime.strptime(lekce[i]["datum"], '%Y-%m-%dT%H:%M').strftime("%d.%m.%Y %H:%M")
        lekce[i]["prihlaseno"] = lekce[i]["id_l"] in prihlasky
    return render_template("lekce_student.html", my_classes=lekce, filtry=filtry, pouzite_filtry=pouzite_filtry,
                           pocet_filtru=len(pouzite_filtry))


@app.route("/uzivatele", methods=["GET", "POST"])
def uzivatele():
    # Zobrazit pouze pro admina
    if "username" not in session:
        return redirect(url_for("index"))
    else:
        if session["usertype"] != "admin":
            return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Smazat uživatele
    if request.method == "POST":
        user_id = request.form.get("user_id")
        status = request.form.get("status")
        if status == "student":
            cur.execute("DELETE FROM student WHERE id=?", [user_id])
        else:
            cur.execute("DELETE FROM instruktor WHERE id=?", [user_id])
        conn.commit()

    try:
        search = request.args.get("search").lower()
    except AttributeError:
        search = ""
    arr = []
    for i in range(5):
        arr.append(search)

    # Vyhledávání studenta
    cur.execute(
        "SELECT * FROM student WHERE jmeno LIKE ? || '%' OR prijmeni LIKE ? || '%' OR username LIKE ? || '%' OR email LIKE ? || '%' OR telefon LIKE ? || '%'",
        arr)
    studenti = [dict(row) for row in cur]
    for i in range(0, len(studenti), 1):
        if re.search("^" + search, studenti[i]["jmeno"].lower()):
            studenti[i]["jmeno"] = "<mark>" + studenti[i]["jmeno"][:len(search)] + "</mark>" + studenti[i]["jmeno"][
                                                                                               len(search):]
        if re.search("^" + search, studenti[i]["prijmeni"].lower()):
            studenti[i]["prijmeni"] = "<mark>" + studenti[i]["prijmeni"][:len(search)] + "</mark>" + studenti[i][
                                                                                                         "prijmeni"][
                                                                                                     len(search):]
        if re.search("^" + search, studenti[i]["username"].lower()):
            studenti[i]["username"] = "<mark>" + studenti[i]["username"][:len(search)] + "</mark>" + studenti[i][
                                                                                                         "username"][
                                                                                                     len(search):]
        if re.search("^" + search, studenti[i]["email"].lower()):
            studenti[i]["email"] = "<mark>" + studenti[i]["email"][:len(search)] + "</mark>" + studenti[i]["email"][
                                                                                               len(search):]
        if re.search("^" + search, studenti[i]["telefon"]):
            studenti[i]["telefon"] = "<mark>" + studenti[i]["telefon"][:len(search)] + "</mark>" + studenti[i][
                                                                                                       "telefon"][
                                                                                                   len(search):]

    # Vyhledávání instruktora
    cur.execute(
        "SELECT * FROM instruktor WHERE jmeno LIKE ? || '%' OR prijmeni LIKE ? || '%' OR username LIKE ? || '%' OR email LIKE ? || '%' OR telefon LIKE ? || '%'",
        arr)
    instruktori = [dict(row) for row in cur]
    for i in range(0, len(instruktori), 1):
        if re.search("^" + search, instruktori[i]["jmeno"].lower()):
            instruktori[i]["jmeno"] = "<mark>" + instruktori[i]["jmeno"][:len(search)] + "</mark>" + instruktori[i][
                                                                                                         "jmeno"][
                                                                                                     len(search):]
        if re.search("^" + search, instruktori[i]["prijmeni"].lower()):
            instruktori[i]["prijmeni"] = "<mark>" + instruktori[i]["prijmeni"][:len(search)] + "</mark>" + \
                                         instruktori[i]["prijmeni"][len(search):]
        if re.search("^" + search, instruktori[i]["username"].lower()):
            instruktori[i]["username"] = "<mark>" + instruktori[i]["username"][:len(search)] + "</mark>" + \
                                         instruktori[i]["username"][len(search):]
        if re.search("^" + search, instruktori[i]["email"].lower()):
            instruktori[i]["email"] = "<mark>" + instruktori[i]["email"][:len(search)] + "</mark>" + instruktori[i][
                                                                                                         "email"][
                                                                                                     len(search):]
        if re.search("^" + search, instruktori[i]["telefon"]):
            instruktori[i]["telefon"] = "<mark>" + instruktori[i]["telefon"][:len(search)] + "</mark>" + instruktori[i][
                                                                                                             "telefon"][
                                                                                                         len(search):]

    return render_template("uzivatele.html", studenti=studenti, instruktori=instruktori)


@app.route("/instruktori", methods=["GET"])
def instruktori():
    # Přesměrování nepřihlášeného uživatele
    if "username" not in session:
        return redirect(url_for("index"))

    if session["usertype"] == "admin":
        return redirect(url_for("index"))

    # vytvořím propojení
    conn = get_db_connection()
    cur = conn.cursor()

    # Instruktoři jsou filtrováni podle certifikací
    pouzite_filtry = request.args.getlist("filtry")
    try:
        pouzite_filtry = [int(i) for i in pouzite_filtry]
    except ValueError:
        pouzite_filtry = []

    cur.execute("SELECT * FROM certifikace")
    filtry = cur.fetchall()

    # vytvořím proměnou do které si načtu data
    sql = "SELECT instruktor.* FROM vlastnim_certifikaci INNER JOIN instruktor ON vlastnim_certifikaci.id_uzivatele=instruktor.id WHERE vlastnim_certifikaci.status_uzivatele='instruktor' AND ("
    for i in range(0, len(pouzite_filtry), 1):
        sql += "vlastnim_certifikaci.id_c=?"
        if i < len(pouzite_filtry) - 1:
            sql += " OR "
    if len(pouzite_filtry) == 0:
        sql += "1=1"
    sql += ") GROUP BY instruktor.id"

    cur.execute(sql, pouzite_filtry)
    instruktori = cur.fetchall()

    cur.execute(
        "SELECT vlastnim_certifikaci.*, certifikace.licence FROM vlastnim_certifikaci INNER JOIN certifikace ON vlastnim_certifikaci.id_c=certifikace.id_c WHERE status_uzivatele='instruktor'")
    certifikace = cur.fetchall()

    # Roztřídit certifikace podle uživatelů
    roztridene_certifikace = {}
    for c in certifikace:
        if c["id_uzivatele"] in roztridene_certifikace.keys():
            roztridene_certifikace[c["id_uzivatele"]].append(c["licence"])
        else:
            roztridene_certifikace[c["id_uzivatele"]] = [c["licence"]]

    for i in roztridene_certifikace.keys():
        roztridene_certifikace[i] = ", ".join(roztridene_certifikace[i])

    # volání instruktori.html a předání dat o instruktorech
    return render_template('instruktori.html', instruktori=instruktori, certifikace=roztridene_certifikace,
                           filtry=filtry, pouzite_filtry=pouzite_filtry, pocet_filtru=len(pouzite_filtry))


@app.route("/profil", methods=["GET", "POST"])
def profil():
    # Přesměrování nepřihlášeného uživatele
    if "username" not in session:
        return redirect(url_for("index"))

    if session["usertype"] == "admin":
        return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM certifikace")
    certifikace = cur.fetchall()

    # Zobrazení stránky pro instruktora
    if session["usertype"] == "instruktor":
        # Změna údajů
        if request.method == "POST":
            jmeno = request.form.get("jmeno")
            prijmeni = request.form.get("prijmeni")
            datum_narozeni = request.form.get("datum_narozeni")
            telefon = request.form.get("telefon")
            email = request.form.get("email")
            cena_za_hodinu = request.form.get("cena_za_hodinu")
            cislo_uctu = request.form.get("cislo_uctu")
            d_certifikace = request.form.getlist("certifikace")

            # Změní údaje v tabulce instruktor
            cur.execute(
                "UPDATE instruktor SET jmeno=?, prijmeni=?, datum_narozeni=?, telefon=?, email=?, cena_za_hodinu=?, cislo_uctu=? WHERE id=?",
                [jmeno, prijmeni, datum_narozeni, telefon, email, cena_za_hodinu, cislo_uctu, session["id"]])
            conn.commit()

            # Vymaže dosavadní certifikáty instruktora
            cur.execute("DELETE FROM vlastnim_certifikaci WHERE id_uzivatele=? AND status_uzivatele=?",
                        [session["id"], session["usertype"]])
            conn.commit()

            # Vloží nové certifikáty
            for c in d_certifikace:
                cur.execute("INSERT INTO vlastnim_certifikaci (id_uzivatele, status_uzivatele, id_c) VALUES (?, ?, ?)",
                            [session["id"], session["usertype"], c])
                conn.commit()

        # Vybere certifikáty instruktora
        cur.execute(
            "SELECT certifikace.id_c FROM vlastnim_certifikaci INNER JOIN certifikace ON vlastnim_certifikaci.id_c=certifikace.id_c WHERE status_uzivatele='instruktor' AND id_uzivatele=?",
            [session["id"]])
        vysledek = cur.fetchall()
        c_instruktora = []
        for i in vysledek:
            c_instruktora.append(i["id_c"])

        cur.execute("SELECT * FROM instruktor WHERE id=?", [session["id"]])
        instruktor = cur.fetchone()

        cur.execute("SELECT delka_trvani FROM lekce WHERE DATE(datum) < DATE('now') AND id_i=?", [session["id"]])
        pocet_hodin = cur.fetchall()
        soucet = timedelta(hours=0)
        for i in pocet_hodin:
            hours = int(i["delka_trvani"][:2])
            minutes = int(i["delka_trvani"][3:])
            soucet += timedelta(hours=hours, minutes=minutes)

        soucet = str(soucet.days * 24 + soucet.seconds // 3600) + " hodin " + str(
            (soucet.seconds // 60) % 60) + " minut"

        return render_template("profil_instruktor.html", instruktor=instruktor, certifikace=certifikace,
                               c_instruktora=c_instruktora, hodin=soucet)

    # Zobrazení stránky pro studenta
    # Změna údajů
    if request.method == "POST":
        jmeno = request.form.get("jmeno")
        prijmeni = request.form.get("prijmeni")
        datum_narozeni = request.form.get("datum_narozeni")
        telefon = request.form.get("telefon")
        email = request.form.get("email")
        d_certifikace = request.form.getlist("certifikace")

        # Změní údaje v tabulce student
        cur.execute("UPDATE student SET jmeno=?, prijmeni=?, datum_narozeni=?, telefon=?, email=? WHERE id=?",
                    [jmeno, prijmeni, datum_narozeni, telefon, email, session["id"]])
        conn.commit()

        # Vymaže dosavadní certifikáty studenta
        cur.execute("DELETE FROM vlastnim_certifikaci WHERE id_uzivatele=? AND status_uzivatele=?",
                    [session["id"], session["usertype"]])
        conn.commit()

        # Vloží nové certifikáty
        for c in d_certifikace:
            cur.execute("INSERT INTO vlastnim_certifikaci (id_uzivatele, status_uzivatele, id_c) VALUES (?, ?, ?)",
                        [session["id"], session["usertype"], c])
            conn.commit()

    # Vybere certifikáty studenta
    cur.execute(
        "SELECT certifikace.id_c FROM vlastnim_certifikaci INNER JOIN certifikace ON vlastnim_certifikaci.id_c=certifikace.id_c WHERE status_uzivatele='student' AND id_uzivatele=?",
        [session["id"]])
    vysledek = cur.fetchall()
    c_studenta = []
    for i in vysledek:
        c_studenta.append(i["id_c"])

    cur.execute("SELECT * FROM student WHERE id=?", [session["id"]])
    student = cur.fetchone()

    return render_template("profil_student.html", student=student, certifikace=certifikace, c_studenta=c_studenta)


@app.route("/odhlasit")
def odhlasit():
    # Vymaže sessions
    keys = list(session.keys())
    for key in keys:
        session.pop(key, None)
    return redirect(url_for("login2"))


@app.route("/forgotten", methods=["GET", "POST"])
def forgotten():
    if "username" in session:
        return redirect(url_for("index"))

    # Zpracování formuláře
    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor()

        username = request.form.get("username")
        usertype = request.form.get("usertype")

        salt = b64encode(os.urandom(16)).decode("utf-8")  # Kryptografická sůl
        letters = string.ascii_lowercase + string.digits
        new_password = ''.join(random.choice(letters) for i in range(8))  # Náhodný 8místný textový řetězec - nové heslo
        salted = new_password + salt
        password_hash = hashlib.sha256(salted.encode("utf-8")).hexdigest()  # Hash, který se uloží do tabulky

        if usertype == "instruktor":
            cur.execute("SELECT email FROM instruktor WHERE username=?", [username])
            user = cur.fetchone()
            if user != None:  # Ověření, že instruktor s tímto username existuje
                cur.execute("UPDATE instruktor SET sul=?, password=? WHERE username=?", [salt, password_hash, username])
                conn.commit()
        else:
            cur.execute("SELECT email FROM student WHERE username=?", [username])
            user = cur.fetchone()
            if user != None:  # Ověření, že student s tímto username existuje
                cur.execute("UPDATE student SET sul=?, password=? WHERE username=?", [salt, password_hash, username])
                conn.commit()

        if user == None:  # Uživatel neexistuje
            return render_template("forgotten.html", data="non-existent")

        # Odeslat e-mail s novým heslem
        msg = flask_mail.Message("Zapomenuté heslo", sender=admin_email, recipients=[user["email"]])
        msg.body = "Dobrý den, vaše nové heslo je nyní: " + new_password
        mail.send(msg)

        return render_template("forgotten.html", data="sent")

    return render_template("forgotten.html")


if __name__ == '__main__':
    app.run()