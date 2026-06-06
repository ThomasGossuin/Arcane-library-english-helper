# \# Librarian Helper

# 

# > Assistant de rangement (Windows) pour le jeu \*\*Librarian: Tidy Up the Arcane Library!\*\*

# 

# Une petite application qui lit automatiquement le titre du livre affiché à l'écran et t'indique en temps réel \*\*où le ranger\*\* : étage, section, catégorie, couleur et taille de l'étagère.

# 

# \---

# 

# \## Ce que ça fait

# 

# Tu joues normalement. Le programme observe une petite zone de ton écran (là où le titre du livre s'affiche dans le jeu), lit le titre tout seul, et affiche dans une mini-fenêtre toujours par-dessus le jeu :

# 

# ```

# Étage 1  -  Section 1A

# Monstrologie

# Couleur : Brun / ton terreux sombre

# Étagère de 10 volumes

# ```

# 

# Tu n'as \*\*rien à taper\*\*. L'affichage se met à jour en direct dès que tu changes de livre.

# 

# \---

# 

# \## Installation (à faire une seule fois)

# 

# \### 1. Installer Python 3

# 

# Télécharge-le depuis <https://www.python.org/downloads/>

# 

# > ⚠️ Pendant l'installation, \*\*coche la case « Add Python to PATH »\*\*.

# 

# \### 2. Installer Tesseract (le moteur OCR qui lit le texte)

# 

# Télécharge le `.exe` \*\*64-bit\*\* depuis <https://github.com/UB-Mannheim/tesseract/wiki> et installe-le.

# 

# > ⚠️ Laisse le dossier par défaut : `C:\\Program Files\\Tesseract-OCR\\`

# 

# \### 3. Installer les dépendances Python

# 

# Ouvre l'invite de commandes Windows (touche \*\*Windows\*\*, tape `cmd`, \*\*Entrée\*\*), puis copie-colle cette ligne et appuie sur \*\*Entrée\*\* :

# 

# ```bash

# pip install mss pillow pytesseract rapidfuzz

# ```

# 

# \### 4. Placer les fichiers du projet

# 

# Mets les \*\*deux\*\* fichiers dans le \*\*même dossier\*\* :

# 

# ```

# librarian\_helper.py

# books\_data.py

# ```

# 

# \---

# 

# \## Lancer le programme

# 

# 1\. Mets ton jeu en mode \*\*« fenêtre sans bordure »\*\* (\*borderless windowed\*) — \*\*pas\*\* en plein écran exclusif, sinon la fenêtre d'aide ne s'affichera pas par-dessus.

# 

# 2\. Double-clique sur `librarian\_helper.py`

# &#x20;  \*(ou, dans `cmd`, depuis le dossier :)\*

# 

# &#x20;  ```bash

# &#x20;  python librarian\_helper.py

# &#x20;  ```

# 

# 3\. \*\*Au 1er lancement :\*\* un écran sombre apparaît. Avec la souris, \*\*dessine un rectangle\*\* autour de l'endroit où le titre du livre apparaît dans le jeu.

# &#x20;  \*(Tiens d'abord un livre en jeu, pour bien viser la zone du titre.)\*

# &#x20;  Relâche : c'est enregistré. La mini-fenêtre suit ensuite le livre que tu tiens.

# 

# \---

# 

# \## Utilisation

# 

# | Action | Effet |

# |--------|-------|

# | Bouton \*\*\[Zone]\*\* | Redessiner la zone de lecture si c'est mal calé |

# | Bouton \*\*\[X]\*\* | Quitter |

# | Glisser la \*\*barre du haut\*\* | Déplacer la fenêtre |

# 

# \---

# 

# \## En cas de problème

# 

# \*\*Texte mal lu\*\* — La zone est trop grande ou trop petite. Clique sur \*\*\[Zone]\*\* et dessine un rectangle plus serré autour du seul titre.

# 

# \*\*« Tesseract introuvable »\*\* — Réinstalle Tesseract en laissant le chemin par défaut (étape 2).

# 

# \*\*« Module manquant »\*\* — Refais l'étape 3 (la commande `pip`).

# 

# \*\*La fenêtre n'apparaît pas par-dessus le jeu\*\* — Passe le jeu en fenêtre sans bordure (voir « Lancer le programme »).

# 

# \*\*Score « (à vérifier) » en orange\*\* — L'OCR n'est pas sûr à 100 %. Le titre affiché en bas (entre guillemets) te montre ce que le programme a cru lire.

# 

# \---

# 

# \## Données

# 

# \*\*400 livres\*\* sont enregistrés :

# 

# \- \*\*Étage 1\*\* : sections 1A à 1N

# \- \*\*Étage 2\*\* : sections 2A à 2Q

