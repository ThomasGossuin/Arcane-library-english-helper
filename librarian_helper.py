# -*- coding: utf-8 -*-
"""
Librarian Helper - assistant de rangement pour
"Librarian: Tidy Up the Arcane Library!"

Lit en continu une zone de l'ecran (la ou le titre du livre s'affiche dans
le jeu), reconnait le titre par OCR, et affiche dans une petite fenetre
toujours au-dessus : l'etage, la section et la couleur de l'etagere.

--- INSTALLATION (Windows) ---
1) Installer Python 3 : https://www.python.org/downloads/
   (cocher "Add Python to PATH" pendant l'installation)
2) Installer Tesseract OCR :
   https://github.com/UB-Mannheim/tesseract/wiki  (prendre le .exe 64-bit)
   Laisser le chemin par defaut C:\\Program Files\\Tesseract-OCR\\
3) Ouvrir l'invite de commandes (cmd) et taper :
       pip install mss pillow pytesseract rapidfuzz
4) Mettre librarian_helper.py ET books_data.py dans le MEME dossier.
5) Lancer :  python librarian_helper.py

--- UTILISATION ---
- Au 1er lancement, on te demande de DESSINER un rectangle a la souris
  autour de l'endroit ou le titre du livre apparait dans le jeu.
- Ensuite la petite fenetre suit en direct le livre que tu tiens.
- Boutons : [Zone] pour redefinir la zone, [X] pour quitter.
- IMPORTANT : lance le jeu en mode "fenetre sans bordure" (borderless),
  pas en plein ecran exclusif, sinon l'overlay ne s'affiche pas par-dessus.
"""

import os
import sys
import re
import json
import time
import threading
import tkinter as tk

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib_helper_config.json")
SCORE_OK = 72          # score mini pour afficher une correspondance sure
SCORE_MAYBE = 55       # entre 55 et 72 : "incertain"
POLL_SECONDS = 0.4     # frequence de capture/OCR

# ---------------------------------------------------------------- deps
def die(msg):
    try:
        r = tk.Tk(); r.withdraw()
        from tkinter import messagebox
        messagebox.showerror("Librarian Helper", msg)
    except Exception:
        pass
    print(msg)
    sys.exit(1)

try:
    import mss
    from PIL import Image
    import pytesseract
    from rapidfuzz import process, fuzz
except ImportError as e:
    die("Module manquant : %s\n\nOuvre cmd et tape :\n"
        "    pip install mss pillow pytesseract rapidfuzz" % e.name)

try:
    from books_data import BOOKS
except Exception as e:
    die("Impossible de charger books_data.py (doit etre dans le meme dossier).\n%s" % e)

# ---------------------------------------------------------------- tesseract path
def setup_tesseract():
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd = c
            return True
    # sinon on espere qu'il est dans le PATH
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

# ---------------------------------------------------------------- matching
def norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

CHOICES = {i: norm(b["title"]) for i, b in enumerate(BOOKS)}

def lookup(ocr_text):
    q = norm(ocr_text)
    if len(q) < 4:
        return None, 0
    res = process.extractOne(q, CHOICES, scorer=fuzz.token_set_ratio)
    if not res:
        return None, 0
    _, score, idx = res
    return BOOKS[idx], score

# ---------------------------------------------------------------- config
def load_region():
    try:
        with open(CONFIG_PATH, "r") as f:
            d = json.load(f)
        r = d.get("region")
        if r and all(k in r for k in ("left", "top", "width", "height")):
            return r
    except Exception:
        pass
    return None

def save_region(region):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({"region": region}, f)
    except Exception:
        pass

# ---------------------------------------------------------------- region picker
def pick_region():
    """Plein ecran translucide : on dessine un rectangle a la souris."""
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.30)
    root.configure(bg="black")
    root.attributes("-topmost", True)
    root.title("Selection de la zone")

    canvas = tk.Canvas(root, cursor="cross", bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(root.winfo_screenwidth() // 2, 40,
                       text="Dessine un rectangle autour du TITRE du livre  -  Echap pour annuler",
                       fill="white", font=("Segoe UI", 18, "bold"))

    state = {"x0": 0, "y0": 0, "rect": None, "region": None}

    def on_press(e):
        state["x0"], state["y0"] = e.x, e.y
        if state["rect"]:
            canvas.delete(state["rect"])
        state["rect"] = canvas.create_rectangle(e.x, e.y, e.x, e.y,
                                                outline="#ffcf5c", width=3)

    def on_drag(e):
        if state["rect"]:
            canvas.coords(state["rect"], state["x0"], state["y0"], e.x, e.y)

    def on_release(e):
        x0, y0 = state["x0"], state["y0"]
        x1, y1 = e.x, e.y
        left, top = min(x0, x1), min(y0, y1)
        w, h = abs(x1 - x0), abs(y1 - y0)
        if w > 10 and h > 8:
            state["region"] = {"left": left, "top": top, "width": w, "height": h}
        root.destroy()

    def on_esc(e):
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_esc)
    root.mainloop()
    return state["region"]

# ---------------------------------------------------------------- OCR worker
class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.region = None
        self.lock = threading.Lock()
        self.result = {"title": "", "floor": "", "section": "", "cat": "",
                       "color": "", "vol": "", "note": "", "score": 0, "raw": ""}
        self.running = True
        self._last_raw = None

    def set_region(self, region):
        with self.lock:
            self.region = region
            self._last_raw = None

    def get(self):
        with self.lock:
            return dict(self.result)

    def run(self):
        sct = mss.mss()
        cfg = "--psm 6"  # bloc de texte uniforme
        while self.running:
            with self.lock:
                region = dict(self.region) if self.region else None
            if not region:
                time.sleep(0.2)
                continue
            try:
                shot = sct.grab(region)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                # upscale + niveaux de gris aident l'OCR sur petites polices
                img = img.convert("L").resize((img.width * 2, img.height * 2))
                raw = pytesseract.image_to_string(img, config=cfg)
                raw = " ".join(raw.split())
            except Exception as ex:
                raw = ""
                with self.lock:
                    self.result = {**self.result, "raw": "Erreur OCR: %s" % ex}
                time.sleep(POLL_SECONDS)
                continue

            if raw == self._last_raw:
                time.sleep(POLL_SECONDS)
                continue
            self._last_raw = raw

            book, score = lookup(raw)
            with self.lock:
                if book and score >= SCORE_MAYBE:
                    self.result = {
                        "title": book["title"], "floor": str(book["floor"]),
                        "section": book["section"], "cat": book["cat"],
                        "color": book["color"],
                        "vol": "Etagere de %d volumes" % book["vol"],
                        "note": book.get("note", ""), "score": score, "raw": raw,
                    }
                else:
                    self.result = {"title": "", "floor": "", "section": "",
                                   "cat": "", "color": "", "vol": "", "note": "",
                                   "score": score, "raw": raw}
            time.sleep(POLL_SECONDS)

# ---------------------------------------------------------------- overlay UI
BG = "#161118"; FG = "#f3e9d2"; GOLD = "#ffcf5c"; MUT = "#9b8fa3"; OK = "#7ee0a0"
WARN = "#ffb454"; DIM = "#5a4f63"

class Overlay:
    def __init__(self, worker):
        self.worker = worker
        self.root = tk.Tk()
        self.root.title("Librarian Helper")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-alpha", 0.94)
        except Exception:
            pass
        self.root.geometry("+40+40")
        self.root.configure(bg=BG)

        bar = tk.Frame(self.root, bg="#241a2b")
        bar.pack(fill="x")
        tk.Label(bar, text="  Arcane Librarian", bg="#241a2b", fg=GOLD,
                 font=("Georgia", 11, "bold")).pack(side="left", pady=4)
        tk.Button(bar, text="X", command=self.quit, bg="#241a2b", fg=MUT,
                  bd=0, activebackground="#3a2a45", activeforeground="white",
                  font=("Segoe UI", 10, "bold")).pack(side="right", padx=4)
        tk.Button(bar, text="Zone", command=self.repick, bg="#241a2b", fg=MUT,
                  bd=0, activebackground="#3a2a45", activeforeground="white",
                  font=("Segoe UI", 9)).pack(side="right")

        body = tk.Frame(self.root, bg=BG, padx=16, pady=12)
        body.pack(fill="both", expand=True)

        self.loc = tk.Label(body, text="--", bg=BG, fg=GOLD,
                            font=("Georgia", 30, "bold"))
        self.loc.pack(anchor="w")
        self.cat = tk.Label(body, text="En attente d'un livre...", bg=BG, fg=FG,
                            font=("Segoe UI", 13, "bold"), wraplength=340, justify="left")
        self.cat.pack(anchor="w", pady=(2, 6))
        self.color = tk.Label(body, text="", bg=BG, fg=FG,
                              font=("Segoe UI", 11), wraplength=340, justify="left")
        self.color.pack(anchor="w")
        self.vol = tk.Label(body, text="", bg=BG, fg=MUT,
                            font=("Segoe UI", 10), wraplength=340, justify="left")
        self.vol.pack(anchor="w")
        self.note = tk.Label(body, text="", bg=BG, fg=WARN,
                             font=("Segoe UI", 10, "bold"), wraplength=340, justify="left")
        self.note.pack(anchor="w")
        self.title = tk.Label(body, text="", bg=BG, fg=MUT,
                              font=("Segoe UI", 9, "italic"), wraplength=340, justify="left")
        self.title.pack(anchor="w", pady=(8, 0))
        self.status = tk.Label(body, text="", bg=BG, fg=DIM,
                               font=("Consolas", 8), wraplength=340, justify="left")
        self.status.pack(anchor="w", pady=(6, 0))

        # deplacable a la souris
        for w in (bar,):
            w.bind("<ButtonPress-1>", self._start_move)
            w.bind("<B1-Motion>", self._on_move)
        self._ox = self._oy = 0

        self.root.after(150, self.refresh)

    def _start_move(self, e):
        self._ox, self._oy = e.x, e.y

    def _on_move(self, e):
        x = self.root.winfo_x() + e.x - self._ox
        y = self.root.winfo_y() + e.y - self._oy
        self.root.geometry("+%d+%d" % (x, y))

    def repick(self):
        self.root.withdraw()
        time.sleep(0.2)
        region = pick_region()
        if region:
            save_region(region)
            self.worker.set_region(region)
        self.root.deiconify()

    def quit(self):
        self.worker.running = False
        self.root.destroy()

    def refresh(self):
        r = self.worker.get()
        if r["section"]:
            self.loc.config(text="Etage %s  -  %s" % (r["floor"], r["section"]), fg=GOLD)
            conf = OK if r["score"] >= SCORE_OK else WARN
            tag = "" if r["score"] >= SCORE_OK else "  (a verifier)"
            self.cat.config(text=r["cat"] + tag, fg=conf)
            self.color.config(text="Couleur : " + r["color"])
            self.vol.config(text=r["vol"])
            self.note.config(text=("/!\\ " + r["note"]) if r["note"] else "")
            self.title.config(text='"%s"' % r["title"])
        else:
            self.loc.config(text="--", fg=DIM)
            if r["raw"]:
                self.cat.config(text="Aucune correspondance fiable", fg=MUT)
            else:
                self.cat.config(text="En attente d'un livre...", fg=MUT)
            self.color.config(text="")
            self.vol.config(text="")
            self.note.config(text="")
            self.title.config(text="")
        self.status.config(text="OCR: %s" % (r["raw"][:60] if r["raw"] else "-"))
        self.root.after(250, self.refresh)

    def run(self):
        self.root.mainloop()

# ---------------------------------------------------------------- main
def main():
    if not setup_tesseract():
        die("Tesseract OCR introuvable.\n\nInstalle-le depuis :\n"
            "https://github.com/UB-Mannheim/tesseract/wiki\n"
            "puis relance le programme.")

    region = load_region()
    if not region:
        region = pick_region()
        if not region:
            die("Aucune zone selectionnee. Relance et dessine un rectangle.")
        save_region(region)

    worker = Worker()
    worker.set_region(region)
    worker.start()

    Overlay(worker).run()

if __name__ == "__main__":
    main()
