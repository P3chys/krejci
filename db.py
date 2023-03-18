import sqlite3

# otevření spojení s databází
conn = sqlite3.connect('database.db')

# vytvoření kurzoru
cur = conn.cursor()

# vytvoření tabulky "instruktor"
cur.execute('''CREATE TABLE IF NOT EXISTS "instruktor" (
	"id"	integer NOT NULL,
	"jmeno"	text,
	"prijmeni"	text,
	"datum_narozeni"	text,
	"telefon"	text,
	"email"	text,
	"cena_za_hodinu"	integer,
	"username"	text,
	"cislo_uctu"	text,
	"sul"	TEXT,
	"password"	text,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
conn.commit()

# vytvoření tabulky "student"
cur.execute('''CREATE TABLE IF NOT EXISTS "student" (
	"id"	integer NOT NULL,
	"jmeno"	text,
	"prijmeni"	text,
	"datum_narozeni"	text,
	"telefon"	text,
	"email"	text,
	"username"	text,
	"sul"	TEXT,
	"password"	text,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
conn.commit()

# vytvoření tabulky "misto"
cur.execute('''CREATE TABLE IF NOT EXISTS "misto" (
	"id_m"	INTEGER NOT NULL,
	"ulice"	text,
	"mesto"	text,
	"cislo_popisne"	integer,
	"smerovaci_cislo"	integer,
	PRIMARY KEY("id_m" AUTOINCREMENT)
);''')
conn.commit()

# vytvoření tabulky "lekce"
cur.execute('''CREATE TABLE IF NOT EXISTS "lekce" (
	"id_l"	INTEGER NOT NULL,
	"nazev"	text,
	"popis"	text,
	"datum"	text,
	"delka_trvani"	text,
	"id_m"	integer,
	"id_i"	integer,
	FOREIGN KEY("id_m") REFERENCES "misto"("id_m"),
	PRIMARY KEY("id_l" AUTOINCREMENT)
);''')
conn.commit()

# vytvoření tabulky "lekce_prihlasky"
cur.execute('''CREATE TABLE IF NOT EXISTS "lekce_prihlasky" (
	"id"	INTEGER NOT NULL,
	"id_s"	INTEGER,
	"id_l"	INTEGER,
	"id_i"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')
conn.commit()

# vytvoření tabulky "certifikace"
cur.execute('''CREATE TABLE IF NOT EXISTS "certifikace" (
	"id_c"	integer NOT NULL,
	"licence"	text,
	PRIMARY KEY("id_c" AUTOINCREMENT)
);''')
conn.commit()

# vytvoření tabulky "vlastnim_certifikaci"
cur.execute('''CREATE TABLE IF NOT EXISTS "vlastnim_certifikaci" (
	"id_v"	INTEGER NOT NULL,
	"id_uzivatele"	integer,
	"status_uzivatele"	TEXT,
	"id_c" integer,
	FOREIGN KEY("id_c") REFERENCES "certifikace"("id_c"),
	PRIMARY KEY("id_v" AUTOINCREMENT)
);''')
conn.commit()
"""
cur.execute('''INSERT INTO "certifikace" ("certifikace.id_c","certifikace.licence") VALUES (1,'OWD'),
 (2,'AOWD'),
 (3,'Sidemount OWD'),
 (4,'EANX'),
 (5,'Dry suit diver'),
 (6,'Open water DPV diver'),
 (7,'Deep diver'),
 (8,'AEANX'),
 (9,'Rescue diver'),
 (10,'Ice diver'),
 (11,'Cave diver'),
 (12,'Divemaster');''')
conn.commit()
"""