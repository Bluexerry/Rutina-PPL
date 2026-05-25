# -*- coding: utf-8 -*-
"""
Rutina PPL · Edición Premium 2026
==================================
Generador de PDF profesional con:
 - Tipografía Rondana (Black / Regular / Light / Ultra Light)
 - Paleta energética (negro carbón, naranja fuego, rojo intenso, ámbar)
 - Fotos reales de sesión servidas por Pexels API (con caché local)
 - Tarjetas de músculos trabajados por sesión (fallback sin Pexels)
 - Calentamientos específicos de 5 min para Push, Pull y Legs
 - Ciclo de entrenamiento 2 días activos + 1 día de descanso (sin semana fija)
 - Tablas de ejercicios con series, reps, tempos y descansos
 - Tablas comparativas por sesión (Hipertrofia · Fuerza · Resistencia)
 - Adaptaciones a lesiones, recuperación y glosario técnico

Toda la información de entrenamiento procede del briefing del usuario
(estructura PPL, series, reps, tempos, descansos, variantes, lesiones).
Basada en las guías ACSM 2026 y evidencia actual sobre hipertrofia.
"""

import os
import urllib.parse
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether, ListFlowable, ListItem,
    HRFlowable, NextPageTemplate, Image, Flowable
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, Polygon, String, Line, Group
from reportlab.graphics import renderPDF
import urllib.request as _urllib_request
import json as _json

# ============================================================
# 1) TIPOGRAFÍA — RONDANA
# ============================================================
pdfmetrics.registerFont(TTFont("Rondana-Black",      "Rondana-Black.ttf"))
pdfmetrics.registerFont(TTFont("Rondana-Regular",    "Rondana-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Rondana-Light",      "Rondana-Light.ttf"))
pdfmetrics.registerFont(TTFont("Rondana-UltraLight", "Rondana-UltraLight.ttf"))

from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily(
    "Rondana",
    normal="Rondana-Regular",
    bold="Rondana-Black",
    italic="Rondana-Light",
    boldItalic="Rondana-Black",
)

F_DISPLAY = "Rondana-Black"
F_BOLD    = "Rondana-Black"
F_BODY    = "Rondana-Regular"
F_LIGHT   = "Rondana-Light"
F_THIN    = "Rondana-UltraLight"

# ============================================================
# 2) PALETA — Energía de gimnasio
# ============================================================
NEGRO        = colors.HexColor("#0B0B0E")
GRIS_TINTA   = colors.HexColor("#16171B")
GRIS_OSCURO  = colors.HexColor("#1F2127")
GRIS_MEDIO   = colors.HexColor("#3A3D44")
GRIS_SUAVE   = colors.HexColor("#9A9CA3")
GRIS_HUMO    = colors.HexColor("#D9DADE")
GRIS_CLARO   = colors.HexColor("#EEEFF1")
BLANCO       = colors.HexColor("#FFFFFF")

NARANJA      = colors.HexColor("#FF6A1A")
NARANJA_OSC  = colors.HexColor("#CC4F0E")
ROJO         = colors.HexColor("#E11D2C")
ROJO_OSC     = colors.HexColor("#A8131E")
AMBAR        = colors.HexColor("#F4B400")
ARENA        = colors.HexColor("#FFE6CF")
VERDE_NEON   = colors.HexColor("#A8E10C")

COL_PUSH     = NARANJA
COL_PULL     = ROJO
COL_LEGS     = AMBAR
COL_HIPER    = NARANJA
COL_FUERZA   = ROJO
COL_RESIS    = AMBAR

OUTPUT = "Rutina_PPL_Premium.pdf"

# ============================================================
# 3) ESTILOS DE TEXTO
# ============================================================
H1 = ParagraphStyle("H1", fontName=F_DISPLAY, fontSize=28, leading=32,
                    textColor=NEGRO, spaceBefore=4, spaceAfter=10)
H2 = ParagraphStyle("H2", fontName=F_DISPLAY, fontSize=16, leading=20,
                    textColor=NARANJA_OSC, spaceBefore=14, spaceAfter=6)
H3 = ParagraphStyle("H3", fontName=F_BOLD, fontSize=12, leading=15,
                    textColor=NEGRO, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("Body", fontName=F_BODY, fontSize=10, leading=14.5,
                      textColor=GRIS_OSCURO, alignment=TA_JUSTIFY, spaceAfter=5)
BODY_LIGHT = ParagraphStyle("BodyLight", parent=BODY, fontName=F_LIGHT)
BODY_BOLD  = ParagraphStyle("BodyBold",  parent=BODY, fontName=F_BOLD)
SMALL = ParagraphStyle("Small", fontName=F_LIGHT, fontSize=8.5, leading=11,
                       textColor=GRIS_MEDIO, alignment=TA_CENTER)
CAPTION = ParagraphStyle("Caption", fontName=F_LIGHT, fontSize=8.5, leading=11,
                         textColor=GRIS_MEDIO, alignment=TA_CENTER, spaceAfter=4)
WHITE_H = ParagraphStyle("WhiteH", fontName=F_DISPLAY, fontSize=12, leading=15,
                         textColor=BLANCO)
WHITE_BODY = ParagraphStyle("WhiteBody", fontName=F_BODY, fontSize=9.5, leading=13,
                            textColor=BLANCO)

# ============================================================
# 4) UTILIDADES VISUALES
# ============================================================

# ---- Clave API de Pexels (GRATUITA en https://www.pexels.com/api/) ----
# Regístrate, copia tu clave y pégala aquí para activar las fotos de sección.
PEXELS_API_KEY = ""  # ← pega tu clave aquí

_IMG_QUERIES = {
    "PUSH":     "bench press chest workout gym",
    "PULL":     "lat pulldown back workout gym",
    "LEGS":     "squat leg workout barbell gym",
    "COVER":    "gym fitness bodybuilding dark",
    "PUSH_msc": "chest pectoral shoulder press muscles anatomy",
    "PULL_msc": "back latissimus dorsi pull workout muscles",
    "LEGS_msc": "leg squat quadriceps glutes workout muscles",
}

# ============================================================
# 4.bis) BIBLIOTECA DE IMÁGENES DE EJERCICIO (Free Exercise DB)
# ------------------------------------------------------------
# Todas las imágenes de ejercicio se sirven desde una sola biblioteca
# open-source (yuhonas/free-exercise-db) bajo licencia gratuita.
# Son fotografías reales con fondo neutro (no generadas).
# ============================================================
EXERCISE_IMG_BASE = ("https://raw.githubusercontent.com/yuhonas/"
                     "free-exercise-db/main/exercises/")

# Mapeo: nombre del ejercicio en la rutina → slug del repo
EXERCISE_SLUGS = {
    # ---------- PUSH · calentamiento ----------
    "Movilidad de hombros":          "Arm_Circles",
    "Band pull-aparts":               "Band_Pull_Apart",
    "Rotación externa con banda":     "Side-Lying_Floor_Stretch",
    "Flexiones lentas":               "Pushups",
    "Serie de aproximación":          "Barbell_Bench_Press_-_Medium_Grip",
    # ---------- PUSH · V1 hipertrofia ----------
    "Press de banca plano (barra)":   "Barbell_Bench_Press_-_Medium_Grip",
    "Press militar (barra/manc.)":    "Standing_Military_Press",
    "Press inclinado mancuernas":     "Incline_Dumbbell_Press",
    "Aperturas (máquina/manc.)":      "Dumbbell_Flyes",
    "Elevaciones laterales (manc.)":  "Side_Lateral_Raise",
    "Extensión tríceps en polea":     "Triceps_Pushdown",
    # ---------- PUSH · V2 fuerza ----------
    "Press de banca pesado":          "Barbell_Bench_Press_-_Medium_Grip",
    "Press militar pesado":           "Standing_Military_Press",
    "Fondos en paralelas":            "Dips_-_Chest_Version",
    "Elevaciones laterales":          "Side_Lateral_Raise",
    "Press francés (barra/manc.)":    "Lying_Triceps_Press",
    "Extensión tríceps mancuernas":   "Seated_Triceps_Press",
    # ---------- PUSH · V3 resistencia ----------
    "Press banca con mancuernas":     "Dumbbell_Bench_Press",
    "Flexiones (push-ups)":           "Pushups",
    "Press sentado en máquina":       "Machine_Shoulder_Military_Press",
    "Elevaciones laterales ligeras":  "Side_Lateral_Raise",
    "Extensión tríceps tras nuca":    "Seated_Triceps_Press",
    # ---------- PULL · calentamiento ----------
    "Movilidad torácica":             "Cat_Stretch",
    "Face pulls con banda":           "Face_Pull",
    "Dead-hang colgado":              "Pullups",
    "Aproximación al jalón":          "Wide-Grip_Lat_Pulldown",
    # ---------- PULL · V1 ----------
    "Jalón al pecho (polea)":         "Wide-Grip_Lat_Pulldown",
    "Remo con barra (o T-bar)":       "Bent_Over_Barbell_Row",
    "Remo en máquina sentado":        "Seated_Cable_Rows",
    "Curl martillo (manc.)":          "Hammer_Curls",
    "Curl de bíceps (barra/manc.)":   "Barbell_Curl",
    "Face pulls":                     "Face_Pull",
    # ---------- PULL · V2 ----------
    "Dominadas":                      "Pullups",
    "Remo con barra pesado":          "Bent_Over_Barbell_Row",
    "Remo en polea sentada (neutro)": "Seated_Cable_Rows",
    "Jalón agarre estrecho (polea)":  "Close-Grip_Front_Lat_Pulldown",
    "Curl con barra Z pesado":        "EZ-Bar_Curl",
    # ---------- PULL · V3 ----------
    "Remo polea baja (agarre ancho)": "Seated_Cable_Rows",
    "Jalón agarre neutro":            "V-Bar_Pulldown",
    "Remo máquina (agarre neutro)":   "Leverage_Iso_Row",
    "Curl bíceps alterno (manc.)":    "Dumbbell_Bicep_Curl",
    "Jalón brazos rígidos en polea":  "Straight-Arm_Pulldown",
    # ---------- LEGS · calentamiento ----------
    "Movilidad de cadera":            "Leg-Up_Hamstring_Stretch",
    "Movilidad de tobillos":          "Ankle_Circles",
    "Monster walks con banda":        "Monster_Walk",
    "Glute bridge con banda":         "Butt_Lift_Bridge",
    "Sentadillas progresivas":        "Bodyweight_Squat",
    # ---------- LEGS · V1 ----------
    "Sentadilla con barra":           "Barbell_Squat",
    "Peso muerto rumano":             "Romanian_Deadlift",
    "Prensa de piernas":              "Leg_Press",
    "Zancadas con mancuernas":        "Dumbbell_Lunges",
    "Elevación de talones":           "Standing_Calf_Raises",
    # ---------- LEGS · V2 ----------
    "Sentadilla trasera pesada":      "Barbell_Squat",
    "Peso muerto (estándar o sumo)":  "Barbell_Deadlift",
    "Zancada búlgara (barra/manc.)":  "Dumbbell_Rear_Lunge",
    "Hip Thrust con barra":           "Barbell_Hip_Thrust",
    "Curl femoral tumbado (máquina)": "Lying_Leg_Curls",
    # ---------- LEGS · V3 ----------
    "Sentadilla libre (cuerpo)":      "Bodyweight_Squat",
    "Step-ups (subida a banco)":      "Dumbbell_Step_Ups",
    "Puente de glúteos (hip thrust)": "Barbell_Glute_Bridge",
    "Prensa de piernas ligera":       "Leg_Press",
    "Elevación de gemelos":           "Standing_Calf_Raises",
    # ---------- CORE ----------
    "Dead Bug":                       "Dead_Bug",
    "Pallof Press":                   "Pallof_Press_With_Rotation",
    "Ab Wheel Rollout":               "Ab_Roller",
    "Plancha lateral + rotación":     "Side_Bridge",
}

# Caché en memoria de rutas locales ya resueltas
_EX_IMG_CACHE = {}


def _slug_for_exercise(name):
    """Devuelve el slug del repo para un nombre dado (case-insensitive,
    quita HTML simple)."""
    key = name.strip()
    # Coincidencia exacta primero
    if key in EXERCISE_SLUGS:
        return EXERCISE_SLUGS[key]
    # Coincidencia parcial (por si el nombre lleva paréntesis extra)
    for k, v in EXERCISE_SLUGS.items():
        if k.lower() in key.lower() or key.lower() in k.lower():
            return v
    return None


def fetch_exercise_image(name, width=1.7*cm, height=1.25*cm, index=0):
    """Descarga (o reutiliza desde caché) la imagen del ejercicio.
    `index` 0 = posición inicial, 1 = posición final (free-exercise-db tiene 2).
    Devuelve un flowable Image o un placeholder gris si no se encuentra.
    Todas las imágenes proceden de la MISMA biblioteca (free-exercise-db)."""
    slug = _slug_for_exercise(name)
    if not slug:
        return _img_placeholder(width, height)

    cache_key = f"{slug}__{index}"
    if cache_key in _EX_IMG_CACHE:
        cached = _EX_IMG_CACHE[cache_key]
        if cached and os.path.exists(cached):
            try:
                return Image(cached, width=width, height=height)
            except Exception:
                pass
        else:
            return _img_placeholder(width, height)

    cache_path = os.path.join("_ex_imgs", f"{slug}_{index}.jpg")
    os.makedirs("_ex_imgs", exist_ok=True)

    if not os.path.exists(cache_path):
        primary = f"{EXERCISE_IMG_BASE}{urllib.parse.quote(slug)}/{index}.jpg"
        fallback = f"{EXERCISE_IMG_BASE}{urllib.parse.quote(slug)}/{1 - index}.jpg"
        ok = False
        for url in (primary, fallback):
            try:
                req = _urllib_request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with _urllib_request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                with open(cache_path, "wb") as f:
                    f.write(data)
                ok = True
                break
            except Exception:
                continue
        if not ok:
            _EX_IMG_CACHE[cache_key] = None
            print(f"  [img] no encontrada para: {name}  ({slug}/{index})")
            return _img_placeholder(width, height)

    _EX_IMG_CACHE[cache_key] = cache_path
    try:
        return Image(cache_path, width=width, height=height)
    except Exception:
        return _img_placeholder(width, height)


class _img_placeholder(Flowable):
    """Recuadro gris cuando no hay imagen disponible."""
    def __init__(self, w, h):
        super().__init__(); self.w = w; self.h = h
    def wrap(self, *a): return (self.w, self.h)
    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor("#D9DADE"))
        c.rect(0, 0, self.w, self.h, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor("#9A9CA3"))
        c.setLineWidth(0.4)
        c.rect(0, 0, self.w, self.h, fill=0, stroke=1)

def fetch_section_photo(session_key, width, height):
    """Descarga una foto real de Pexels para la sesión indicada.
    Usa caché local (_img_push.jpg, etc.).
    Sin clave API devuelve None (el PDF se genera igual, sin foto).
    """
    cache = f"_img_{session_key.lower()}.jpg"
    if os.path.exists(cache):
        try:
            return Image(cache, width=width, height=height)
        except Exception:
            pass
    if not PEXELS_API_KEY:
        return None
    query = urllib.parse.quote(_IMG_QUERIES.get(session_key, "gym fitness"))
    api_url = (f"https://api.pexels.com/v1/search?query={query}"
               f"&per_page=1&orientation=landscape&size=large")
    req = _urllib_request.Request(api_url,
                                  headers={"Authorization": PEXELS_API_KEY})
    try:
        with _urllib_request.urlopen(req, timeout=8) as resp:
            data = _json.loads(resp.read())
        photo_url = data["photos"][0]["src"]["large"]
        _urllib_request.urlretrieve(photo_url, cache)
        return Image(cache, width=width, height=height)
    except Exception:
        return None


# ----- Mapa muscular vectorial (silueta estilizada) -----

class MuscleMap(Flowable):
    """
    Silueta esquemática de cuerpo humano (front+back) con regiones musculares
    coloreadas según la sesión (PUSH / PULL / LEGS).
    No es anatomía clínica — es un infográfico estilizado.
    """
    def __init__(self, session="PUSH", width=8.5*cm, height=11*cm):
        super().__init__()
        self.session = session
        self.width = width
        self.height = height

    def wrap(self, *a):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        # Fondo claro
        c.setFillColor(GRIS_CLARO); c.rect(0, 0, w, h, fill=1, stroke=0)
        # Banda inferior
        c.setFillColor(NEGRO); c.rect(0, 0, w, 0.7*cm, fill=1, stroke=0)
        c.setFillColor(BLANCO)
        c.setFont(F_DISPLAY, 9)
        c.drawCentredString(w/2, 0.22*cm, f"MAPA MUSCULAR · SESIÓN {self.session}")

        # dos siluetas (front, back) lado a lado
        for i, lado in enumerate(("FRONTAL", "POSTERIOR")):
            cx = w * (0.27 if i == 0 else 0.73)
            cy = h * 0.55
            self._draw_silhouette(c, cx, cy, lado)

    def _draw_silhouette(self, c, cx, cy, lado):
        # Escala
        s = 0.85
        # Cuerpo: cabeza, torso, brazos, piernas en formas suaves
        # Cabeza
        c.setFillColor(GRIS_HUMO); c.setStrokeColor(GRIS_MEDIO); c.setLineWidth(0.6)
        c.circle(cx, cy + 3.4*cm*s, 0.55*cm*s, fill=1, stroke=1)
        # Torso (trapecio)
        torso = c.beginPath()
        torso.moveTo(cx - 1.3*cm*s, cy + 2.7*cm*s)
        torso.lineTo(cx + 1.3*cm*s, cy + 2.7*cm*s)
        torso.lineTo(cx + 1.05*cm*s, cy + 0.2*cm*s)
        torso.lineTo(cx - 1.05*cm*s, cy + 0.2*cm*s)
        torso.close()
        c.drawPath(torso, fill=1, stroke=1)
        # Brazos
        c.roundRect(cx - 2.05*cm*s, cy + 0.6*cm*s, 0.55*cm*s, 2.15*cm*s, 0.25*cm*s, fill=1, stroke=1)
        c.roundRect(cx + 1.5*cm*s,  cy + 0.6*cm*s, 0.55*cm*s, 2.15*cm*s, 0.25*cm*s, fill=1, stroke=1)
        # Antebrazos
        c.roundRect(cx - 2.05*cm*s, cy - 1.4*cm*s, 0.5*cm*s, 1.85*cm*s, 0.22*cm*s, fill=1, stroke=1)
        c.roundRect(cx + 1.55*cm*s, cy - 1.4*cm*s, 0.5*cm*s, 1.85*cm*s, 0.22*cm*s, fill=1, stroke=1)
        # Piernas
        c.roundRect(cx - 1.0*cm*s,  cy - 2.4*cm*s, 0.85*cm*s, 2.6*cm*s, 0.3*cm*s, fill=1, stroke=1)
        c.roundRect(cx + 0.15*cm*s, cy - 2.4*cm*s, 0.85*cm*s, 2.6*cm*s, 0.3*cm*s, fill=1, stroke=1)
        # Gemelos
        c.roundRect(cx - 0.95*cm*s, cy - 4.6*cm*s, 0.75*cm*s, 2.1*cm*s, 0.28*cm*s, fill=1, stroke=1)
        c.roundRect(cx + 0.2*cm*s,  cy - 4.6*cm*s, 0.75*cm*s, 2.1*cm*s, 0.28*cm*s, fill=1, stroke=1)

        # Regiones coloreadas según sesión y lado
        sess = self.session
        if sess == "PUSH":
            # Frontal: pectoral, deltoides frontal/lateral, tríceps (en parte trasera del brazo)
            if lado == "FRONTAL":
                # Pectorales
                self._region(c, cx-1.1*cm*s, cy+1.55*cm*s, 2.2*cm*s, 1.0*cm*s, NARANJA, "Pectoral")
                # Deltoides
                c.setFillColor(NARANJA)
                c.circle(cx-1.55*cm*s, cy+2.55*cm*s, 0.45*cm*s, fill=1, stroke=0)
                c.circle(cx+1.55*cm*s, cy+2.55*cm*s, 0.45*cm*s, fill=1, stroke=0)
                self._label(c, cx-2.6*cm*s, cy+2.9*cm*s, "Deltoides")
                self._label(c, cx-0.7*cm*s, cy+2.05*cm*s, "Pectoral")
            else:
                # Tríceps (cara posterior brazo)
                c.setFillColor(NARANJA)
                c.roundRect(cx-2.0*cm*s, cy+0.8*cm*s, 0.5*cm*s, 1.8*cm*s, 0.2*cm*s, fill=1, stroke=0)
                c.roundRect(cx+1.55*cm*s, cy+0.8*cm*s, 0.5*cm*s, 1.8*cm*s, 0.2*cm*s, fill=1, stroke=0)
                self._label(c, cx-2.7*cm*s, cy+1.7*cm*s, "Tríceps")
        elif sess == "PULL":
            if lado == "POSTERIOR":
                # Dorsales (gran V)
                pts = [cx-1.3*cm*s, cy+2.6*cm*s,
                       cx+1.3*cm*s, cy+2.6*cm*s,
                       cx+1.0*cm*s, cy+0.3*cm*s,
                       cx,         cy+0.9*cm*s,
                       cx-1.0*cm*s, cy+0.3*cm*s]
                c.setFillColor(ROJO)
                p = c.beginPath()
                p.moveTo(pts[0], pts[1])
                for i in range(2, len(pts), 2): p.lineTo(pts[i], pts[i+1])
                p.close(); c.drawPath(p, fill=1, stroke=0)
                # Trapecio
                c.setFillColor(ROJO_OSC)
                p2 = c.beginPath()
                p2.moveTo(cx-1.1*cm*s, cy+2.75*cm*s)
                p2.lineTo(cx+1.1*cm*s, cy+2.75*cm*s)
                p2.lineTo(cx+0.35*cm*s, cy+2.1*cm*s)
                p2.lineTo(cx-0.35*cm*s, cy+2.1*cm*s)
                p2.close(); c.drawPath(p2, fill=1, stroke=0)
                self._label(c, cx-0.3*cm*s, cy+1.7*cm*s, "Dorsales")
                self._label(c, cx-2.3*cm*s, cy+2.85*cm*s, "Trapecio")
            else:
                # Bíceps (frontal del brazo)
                c.setFillColor(ROJO)
                c.roundRect(cx-2.0*cm*s, cy+1.0*cm*s, 0.5*cm*s, 1.6*cm*s, 0.2*cm*s, fill=1, stroke=0)
                c.roundRect(cx+1.55*cm*s, cy+1.0*cm*s, 0.5*cm*s, 1.6*cm*s, 0.2*cm*s, fill=1, stroke=0)
                self._label(c, cx-2.7*cm*s, cy+1.85*cm*s, "Bíceps")
        elif sess == "LEGS":
            if lado == "FRONTAL":
                # Cuádriceps
                c.setFillColor(AMBAR)
                c.roundRect(cx-0.9*cm*s, cy-2.3*cm*s, 0.75*cm*s, 2.3*cm*s, 0.28*cm*s, fill=1, stroke=0)
                c.roundRect(cx+0.2*cm*s, cy-2.3*cm*s, 0.75*cm*s, 2.3*cm*s, 0.28*cm*s, fill=1, stroke=0)
                self._label(c, cx-0.55*cm*s, cy-1.2*cm*s, "Cuádriceps")
            else:
                # Glúteos
                c.setFillColor(AMBAR)
                c.roundRect(cx-1.0*cm*s, cy-0.1*cm*s, 2.0*cm*s, 0.95*cm*s, 0.35*cm*s, fill=1, stroke=0)
                # Isquios
                c.setFillColor(NARANJA)
                c.roundRect(cx-0.9*cm*s, cy-2.3*cm*s, 0.75*cm*s, 2.3*cm*s, 0.28*cm*s, fill=1, stroke=0)
                c.roundRect(cx+0.2*cm*s, cy-2.3*cm*s, 0.75*cm*s, 2.3*cm*s, 0.28*cm*s, fill=1, stroke=0)
                # Gemelos
                c.setFillColor(ROJO)
                c.roundRect(cx-0.9*cm*s, cy-4.55*cm*s, 0.7*cm*s, 1.9*cm*s, 0.26*cm*s, fill=1, stroke=0)
                c.roundRect(cx+0.25*cm*s, cy-4.55*cm*s, 0.7*cm*s, 1.9*cm*s, 0.26*cm*s, fill=1, stroke=0)
                self._label(c, cx-0.4*cm*s, cy+0.45*cm*s, "Glúteo")
                self._label(c, cx-0.4*cm*s, cy-1.2*cm*s, "Isquios")
                self._label(c, cx-0.4*cm*s, cy-3.6*cm*s, "Gemelos")

        # Etiqueta lado
        c.setFillColor(GRIS_MEDIO); c.setFont(F_BOLD, 7)
        c.drawCentredString(cx, cy - 5.0*cm*s, lado)

    def _region(self, c, x, y, w, h, color, label=""):
        c.setFillColor(color); c.roundRect(x, y, w, h, 0.15*cm, fill=1, stroke=0)

    def _label(self, c, x, y, text):
        c.setFillColor(NEGRO); c.setFont(F_BOLD, 6.5)
        c.drawString(x, y, text.upper())


# ----- Iconos sencillos -----

class BarbellIcon(Flowable):
    """Icono vectorial de una mancuerna/barra."""
    def __init__(self, w=2.5*cm, h=0.9*cm, color=NEGRO):
        super().__init__(); self.w=w; self.h=h; self.color=color
    def wrap(self, *a): return (self.w, self.h)
    def draw(self):
        c = self.canv; w,h = self.w, self.h
        c.setFillColor(self.color)
        # Barra
        c.rect(w*0.2, h*0.45, w*0.6, h*0.1, fill=1, stroke=0)
        # Discos
        c.rect(w*0.05, h*0.15, w*0.12, h*0.7, fill=1, stroke=0)
        c.rect(w*0.83, h*0.15, w*0.12, h*0.7, fill=1, stroke=0)
        c.rect(w*0.18, h*0.25, w*0.04, h*0.5, fill=1, stroke=0)
        c.rect(w*0.78, h*0.25, w*0.04, h*0.5, fill=1, stroke=0)


# ----- Bloques compuestos -----

def section_banner(text, color=NARANJA, tag=None):
    """Banner ancho con marca lateral."""
    inner = [[
        Paragraph(f'<font color="white" face="{F_DISPLAY}" size="14">{text}</font>',
                  ParagraphStyle("sb", fontSize=14, leading=17)),
        Paragraph(f'<font color="white" face="{F_LIGHT}" size="9">{tag or ""}</font>',
                  ParagraphStyle("sbt", fontSize=9, leading=12, alignment=TA_RIGHT))
    ]]
    t = Table(inner, colWidths=[13*cm, 4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NEGRO),
        ("BACKGROUND", (0,0), (0,0), NEGRO),
        ("LINEBEFORE", (0,0), (0,0), 8, color),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

def variant_header(text, color):
    inner = [[Paragraph(
        f'<font color="white" face="{F_DISPLAY}" size="11.5">{text}</font>',
        ParagraphStyle("vh", fontSize=11.5, leading=14))]]
    t = Table(inner, colWidths=[17*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), color),
        ("LINEBEFORE", (0,0), (0,0), 5, NEGRO),
        ("LEFTPADDING", (0,0), (-1,-1), 11),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    return t

def kpi_strip(items):
    """Tira de tarjetas KPI [(num, label, color), ...]"""
    row = []
    for num, lab, col in items:
        cell = Table(
            [[Paragraph(f'<font color="white" face="{F_DISPLAY}" size="20">{num}</font>',
                        ParagraphStyle("k1", fontSize=20, leading=22))],
             [Paragraph(f'<font color="white" face="{F_LIGHT}" size="8">{lab}</font>',
                        ParagraphStyle("k2", fontSize=8, leading=10))]],
            colWidths=[3.9*cm], rowHeights=[1.1*cm, 0.7*cm]
        )
        cell.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), col),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        row.append(cell)
    t = Table([row], colWidths=[4.25*cm]*len(items))
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    return t


def principle_block(title, body, accent=None):
    """Bloque visual de principio: cabecera oscura con acento de color + cuerpo claro."""
    if accent is None:
        accent = NARANJA
    _ps_hd = ParagraphStyle("phd", fontName=F_DISPLAY, fontSize=10.5, leading=13.5, textColor=BLANCO)
    _ps_bd = ParagraphStyle("pbd", fontName=F_BODY,    fontSize=9.5,  leading=13.5, textColor=GRIS_OSCURO)
    tbl = Table([
        [Paragraph(title, _ps_hd)],
        [Paragraph(body,  _ps_bd)],
    ], colWidths=[17*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NEGRO),
        ("BACKGROUND",    (0,1), (-1,1), GRIS_CLARO),
        ("LINEBEFORE",    (0,0), (-1,-1), 5, accent),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
        ("TOPPADDING",    (0,0), (-1,0),  9),
        ("BOTTOMPADDING", (0,0), (-1,0),  9),
        ("TOPPADDING",    (0,1), (-1,1),  9),
        ("BOTTOMPADDING", (0,1), (-1,1), 11),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return tbl


def exercise_table(rows, accent=NARANJA):
    """
    Tabla de ejercicios con columna QR.
    rows: lista de [ejercicio, series×reps, tempo, descanso, músculos]
    """
    _ps_ex = ParagraphStyle("ex", fontName=F_BODY,  fontSize=9,   leading=12)
    _ps_mu = ParagraphStyle("mu", fontName=F_LIGHT, fontSize=8.5, leading=11)
    _ps_td = ParagraphStyle("td", fontName=F_BODY,  fontSize=9,   leading=12, alignment=TA_CENTER)
    header = ["#", "EJERCICIO", "SERIES × REPS", "TEMPO", "DESCANSO", "MÚSCULOS"]
    data = [header]
    for i, r in enumerate(rows, 1):
        ex_name = r[0]
        _name_cell = Table(
            [[fetch_exercise_image(ex_name, width=1.5*cm, height=1.1*cm),
              Paragraph(f'<font face="{F_BOLD}">{ex_name}</font>', _ps_ex)]],
            colWidths=[1.55*cm, 3.6*cm],
        )
        _name_cell.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
            ("LEFTPADDING",  (1,0), (1,0),   5),
        ]))
        data.append([
            str(i),
            _name_cell,
            Paragraph(r[1], _ps_td),
            Paragraph(r[2], _ps_td),
            Paragraph(r[3], _ps_td),
            Paragraph(r[4], _ps_mu),
        ])
    t = Table(data,
              colWidths=[0.65*cm, 5.35*cm, 2.8*cm, 1.75*cm, 2.15*cm, 4.3*cm],
              repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0,0), (-1,0), NEGRO),
        ("TEXTCOLOR", (0,0), (-1,0), BLANCO),
        ("FONTNAME", (0,0), (-1,0), F_DISPLAY),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("LINEBELOW", (0,0), (-1,0), 2, accent),
        # Body
        ("FONTNAME", (0,1), (-1,-1), F_BODY),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("TEXTCOLOR", (0,1), (-1,-1), GRIS_OSCURO),
        ("ALIGN", (0,1), (0,-1), "CENTER"),
        ("FONTNAME", (0,1), (0,-1), F_DISPLAY),
        ("TEXTCOLOR", (0,1), (0,-1), accent),
        ("ALIGN", (2,1), (4,-1), "CENTER"),
        ("LEFTPADDING", (1,1), (1,-1), 3),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
        ("BOX", (0,0), (-1,-1), 0.5, GRIS_MEDIO),
        ("INNERGRID", (0,0), (-1,-1), 0.25, GRIS_HUMO),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t

def comparative_table(rows):
    _ps_cb = ParagraphStyle("ct_b", fontName=F_BODY,    fontSize=9,   leading=12, alignment=TA_CENTER)
    _ps_cv = ParagraphStyle("ct_v", fontName=F_DISPLAY, fontSize=9,   leading=12, alignment=TA_CENTER, textColor=BLANCO)
    header = ["VARIANTE", "OBJETIVO", "VOLUMEN (series/sem)", "INTENSIDAD (rep)", "EQUIPAMIENTO"]
    proc_rows = []
    for r in rows:
        proc_rows.append([
            Paragraph(r[0], _ps_cv),
            Paragraph(r[1], _ps_cb),
            Paragraph(r[2], _ps_cb),
            Paragraph(r[3], _ps_cb),
            Paragraph(r[4], _ps_cb),
        ])
    data = [header] + proc_rows
    t = Table(data, colWidths=[2.5*cm, 2.7*cm, 3.5*cm, 3.3*cm, 5.0*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NEGRO),
        ("TEXTCOLOR", (0,0), (-1,0), BLANCO),
        ("FONTNAME", (0,0), (-1,0), F_DISPLAY),
        ("FONTSIZE", (0,0), (-1,0), 8.5),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,1), (-1,-1), F_BODY),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND", (0,1), (0,1), COL_HIPER),
        ("BACKGROUND", (0,2), (0,2), COL_FUERZA),
        ("BACKGROUND", (0,3), (0,3), COL_RESIS),
        ("TEXTCOLOR",  (0,1), (0,-1), BLANCO),
        ("FONTNAME",   (0,1), (0,-1), F_DISPLAY),
        ("ROWBACKGROUNDS", (1,1), (-1,-1), [BLANCO, GRIS_CLARO]),
        ("LINEBELOW", (0,0), (-1,0), 1.5, NARANJA),
        ("BOX", (0,0), (-1,-1), 0.5, GRIS_MEDIO),
        ("INNERGRID", (0,0), (-1,-1), 0.25, GRIS_HUMO),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    return t

def progression_box(text, color=NARANJA):
    t = Table(
        [[Paragraph(
            f'<font face="{F_DISPLAY}" color="#0B0B0E">PROGRESIÓN ▸</font> '
            f'<font face="{F_BODY}">{text}</font>',
            ParagraphStyle("pg", fontName=F_BODY, fontSize=9.5, leading=13,
                           textColor=GRIS_OSCURO))]],
        colWidths=[17*cm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), ARENA),
        ("LINEBEFORE", (0,0), (0,0), 4, color),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    return t

def warmup_block(session, color, rows):
    """
    Tarjeta de calentamiento 5 min para una sesión.
    rows: [(tiempo, ejercicio, descripción), ...]
    Total siempre 5 min.
    """
    flow = []
    # Cabecera
    head = Table(
        [[Paragraph(f'<font color="white" face="{F_DISPLAY}" size="11">CALENTAMIENTO · 5 MIN</font>',
                    ParagraphStyle("wh", fontSize=11, leading=13)),
          Paragraph(f'<font color="white" face="{F_LIGHT}" size="9">previo a sesión {session}</font>',
                    ParagraphStyle("wh2", fontSize=9, leading=12, alignment=TA_RIGHT))]],
        colWidths=[12*cm, 5*cm],
    )
    head.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NEGRO),
        ("LINEBEFORE", (0,0), (0,0), 5, color),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    flow.append(head)
    flow.append(Spacer(1, 8))
    # Filas — Paragraph para permitir ajuste de línea en la columna FOCO
    _ps_wt  = ParagraphStyle("wt",  fontName=F_DISPLAY, fontSize=9,  leading=12, textColor=color)
    _ps_we  = ParagraphStyle("we",  fontName=F_BOLD,    fontSize=9,  leading=12, alignment=TA_CENTER)
    _ps_wfo = ParagraphStyle("wfo", fontName=F_LIGHT,   fontSize=8.5, leading=11.5, textColor=GRIS_OSCURO)
    _ps_arr = ParagraphStyle("arr", fontName=F_DISPLAY, fontSize=14, leading=14, alignment=TA_CENTER, textColor=color)
    data = [["TIEMPO", "EJERCICIO", "FOCO"]]
    for r in rows:
        # Secuencia de movimiento: posición inicial → posición final
        _seq = Table(
            [[fetch_exercise_image(r[1], width=2.0*cm, height=1.4*cm, index=0),
              Paragraph("→", _ps_arr),
              fetch_exercise_image(r[1], width=2.0*cm, height=1.4*cm, index=1)]],
            colWidths=[2.05*cm, 0.5*cm, 2.05*cm],
        )
        _seq.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
        ]))
        _name_cell = Table(
            [[_seq],
             [Paragraph(r[1], _ps_we)]],
            colWidths=[4.7*cm],
        )
        _name_cell.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (0,0),   0),
            ("BOTTOMPADDING",(0,0), (0,0),   2),
            ("TOPPADDING",   (0,1), (0,1),   2),
            ("BOTTOMPADDING",(0,1), (0,1),   0),
        ]))
        data.append([
            Paragraph(r[0], _ps_wt),
            _name_cell,
            Paragraph(r[2], _ps_wfo),
        ])
    body_tbl = Table(data, colWidths=[2.2*cm, 5.5*cm, 9.3*cm], repeatRows=1)
    body_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRIS_OSCURO),
        ("TEXTCOLOR", (0,0), (-1,0), BLANCO),
        ("FONTNAME", (0,0), (-1,0), F_DISPLAY),
        ("FONTSIZE", (0,0), (-1,0), 8.5),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("ALIGN", (0,0), (0,-1), "CENTER"),
        ("FONTNAME", (0,1), (0,-1), F_DISPLAY),
        ("TEXTCOLOR", (0,1), (0,-1), color),
        ("FONTNAME", (1,1), (1,-1), F_BOLD),
        ("FONTNAME", (2,1), (2,-1), F_LIGHT),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("TEXTCOLOR", (1,1), (-1,-1), GRIS_OSCURO),
        ("LEFTPADDING", (1,1), (1,-1), 3),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
        ("LINEBELOW", (0,0), (-1,0), 1.5, color),
        ("BOX", (0,0), (-1,-1), 0.5, GRIS_MEDIO),
        ("INNERGRID", (0,0), (-1,-1), 0.25, GRIS_HUMO),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    flow.append(body_tbl)
    return flow


# ============================================================
# 5) PORTADA + HEADER/FOOTER
# ============================================================

def draw_cover(canv, doc):
    w, h = A4

    # === FONDO ===
    canv.setFillColor(NEGRO); canv.rect(0, 0, w, h, fill=1, stroke=0)

    # === CÍRCULOS DECORATIVOS — esquina superior derecha ===
    canv.setStrokeColor(colors.HexColor("#1E2029")); canv.setLineWidth(0.8)
    for _r in [2.5*cm, 5.0*cm, 7.5*cm, 10.0*cm, 12.5*cm]:
        canv.circle(w, h, _r, stroke=1, fill=0)

    # === BLOQUES DIAGONALES PRINCIPALES ===
    canv.setFillColor(NARANJA)
    p = canv.beginPath()
    p.moveTo(0, h*0.35); p.lineTo(w, h*0.565); p.lineTo(w, h*0.455); p.lineTo(0, h*0.24); p.close()
    canv.drawPath(p, fill=1, stroke=0)
    canv.setFillColor(ROJO)
    p2 = canv.beginPath()
    p2.moveTo(0, h*0.237); p2.lineTo(w, h*0.450); p2.lineTo(w, h*0.429); p2.lineTo(0, h*0.216); p2.close()
    canv.drawPath(p2, fill=1, stroke=0)
    canv.setFillColor(AMBAR)
    p3 = canv.beginPath()
    p3.moveTo(0, h*0.213); p3.lineTo(w, h*0.426); p3.lineTo(w, h*0.420); p3.lineTo(0, h*0.207); p3.close()
    canv.drawPath(p3, fill=1, stroke=0)

    # === FRANJA VERTICAL — capa final, encima de todos los bloques diagonales ===
    canv.setFillColor(NARANJA); canv.rect(0, 0, 0.45*cm, h, fill=1, stroke=0)
    canv.setFillColor(colors.HexColor("#CC4F0E")); canv.rect(0.45*cm, 0, 0.06*cm, h, fill=1, stroke=0)

    # === TAG SUPERIOR ===
    canv.setFillColor(NARANJA); canv.setFont(F_DISPLAY, 9)
    canv.drawString(1.6*cm, h - 1.95*cm, "GUÍA PROFESIONAL · RUTINA PPL 2026")
    canv.setStrokeColor(NARANJA); canv.setLineWidth(2)
    canv.line(1.6*cm, h - 2.22*cm, 11.5*cm, h - 2.22*cm)
    canv.setFillColor(BLANCO); canv.setFont(F_LIGHT, 9)
    canv.drawRightString(w - 2.2*cm, h - 1.95*cm, "ACSM · Hipertrofia · Fuerza · Resistencia")

    # === EYEBROW ===
    canv.setFillColor(GRIS_SUAVE); canv.setFont(F_LIGHT, 11)
    canv.drawString(1.6*cm, h - 5.0*cm, "PROGRAMA DE ENTRENAMIENTO")

    # === TÍTULO MEGA: RUTINA ===
    canv.setFillColor(BLANCO); canv.setFont(F_DISPLAY, 95)
    canv.drawString(1.6*cm, h - 8.9*cm, "RUTINA")

    # === PPL con bloque de color de fondo ===
    canv.setFillColor(NARANJA)
    canv.rect(1.4*cm, h - 12.35*cm, 7.2*cm, 3.15*cm, fill=1, stroke=0)
    canv.setFillColor(NEGRO); canv.setFont(F_DISPLAY, 95)
    canv.drawString(1.6*cm, h - 12.05*cm, "PPL")

    # Tres puntos de sesión a la derecha del bloque
    for _i, _c in enumerate([NARANJA, ROJO, AMBAR]):
        canv.setFillColor(_c)
        canv.circle(9.2*cm + _i*0.75*cm, h - 10.75*cm, 0.26*cm, fill=1, stroke=0)

    # Línea divisoria fina
    canv.setStrokeColor(GRIS_MEDIO); canv.setLineWidth(0.5)
    canv.line(1.6*cm, h - 12.65*cm, w - 2.2*cm, h - 12.65*cm)

    # === SUBTÍTULO ===
    canv.setFillColor(BLANCO); canv.setFont(F_DISPLAY, 22)
    canv.drawString(1.6*cm, h - 13.6*cm, "PUSH  ·  PULL  ·  LEGS")
    canv.setFillColor(GRIS_HUMO); canv.setFont(F_LIGHT, 13)
    canv.drawString(1.6*cm, h - 14.55*cm, "Hipertrofia · Fuerza · Resistencia muscular")

    # === FEATURES ===
    features = [
        "3 SESIONES · 3 VARIANTES POR SESIÓN",
        "CALENTAMIENTOS DE 5 MIN POR SESIÓN",
        "CÁPSULA DE CORE AL FINAL DE CADA SESIÓN",
        "CICLO 2 DÍAS SÍ · 1 DÍA NO · FLEXIBLE",
        "MAPAS MUSCULARES POR DÍA DE ENTRENAMIENTO",
        "VUELTA A LA CALMA Y GLOSARIO TÉCNICO",
    ]
    _fy = 5.5*cm
    for _feat in features:
        canv.setFillColor(NARANJA); canv.rect(1.6*cm, _fy + 0.05*cm, 0.17*cm, 0.17*cm, fill=1, stroke=0)
        canv.setFillColor(BLANCO); canv.setFont(F_DISPLAY, 9)
        canv.drawString(2.0*cm, _fy, _feat); _fy -= 0.58*cm

    # === MARCA VERTICAL DERECHA ===
    canv.saveState()
    canv.translate(w - 1.3*cm, 4.5*cm)
    canv.rotate(90)
    canv.setFillColor(NARANJA); canv.setFont(F_DISPLAY, 11)
    canv.drawString(0, 0, "RUTINA PPL · 2026")
    canv.restoreState()

    # === FOOTER ===
    canv.setFillColor(GRIS_SUAVE); canv.setFont(F_LIGHT, 8)
    canv.drawString(1.6*cm, 1.5*cm,
        "Basado en guías ACSM 2026 y estudios actuales de hipertrofia · uso personal")


def draw_header_footer(canv, doc):
    w, h = A4
    # Header
    canv.setFillColor(NEGRO); canv.rect(0, h - 1.35*cm, w, 1.35*cm, fill=1, stroke=0)
    canv.setFillColor(NARANJA); canv.rect(0, h - 1.45*cm, w, 0.1*cm, fill=1, stroke=0)
    canv.setFillColor(BLANCO); canv.setFont(F_DISPLAY, 10)
    canv.drawString(2*cm, h - 0.92*cm, "RUTINA PPL")
    canv.setFillColor(NARANJA); canv.setFont(F_DISPLAY, 10)
    canv.drawString(4.2*cm, h - 0.92*cm, "// PUSH · PULL · LEGS")
    # Footer
    canv.setFillColor(NEGRO); canv.rect(0, 0, w, 1.05*cm, fill=1, stroke=0)
    canv.setFillColor(NARANJA); canv.rect(0, 1.05*cm, w, 0.07*cm, fill=1, stroke=0)
    canv.setFillColor(GRIS_HUMO); canv.setFont(F_LIGHT, 8.5)
    canv.drawString(2*cm, 0.4*cm, "Guía profesional · datos basados en ACSM 2026")
    canv.setFillColor(NARANJA); canv.setFont(F_DISPLAY, 10)
    canv.drawRightString(w - 2*cm, 0.4*cm, f"PÁG. {doc.page:02d}")


# ============================================================
# 6) CONTENIDO
# ============================================================
story = []

# --- Portada (página 1, no añadimos nada al story para esa página) ---
story.append(NextPageTemplate("content"))
story.append(PageBreak())

# =========== ÍNDICE ===========
story.append(Paragraph("ÍNDICE", H1))
story.append(HRFlowable(width="100%", thickness=2.5, color=NARANJA, spaceAfter=14))

toc_rows = [
    ("01", "Resumen ejecutivo & objetivos",        "p.  3"),
    ("02", "Principios de entrenamiento (ACSM)",   "p.  4"),
    ("03", "Ritmo de entrenamiento (ciclo 2+1)",      "p.  5"),
    ("04", "Sesión PUSH · pecho · hombros · tríceps", "p.  6"),
    ("05", "Sesión PULL · espalda · bíceps",        "p. 10"),
    ("06", "Sesión LEGS · piernas completas",       "p. 13"),
    ("07", "Recuperación y seguridad",               "p. 16"),
    ("08", "Core y vuelta a la calma",               "p. 17"),
    ("09", "Glosario y notas técnicas",              "p. 18"),
]
toc = Table(
    [[Paragraph(f'<font face="{F_DISPLAY}" color="#FF6A1A" size="14">{n}</font>',
                ParagraphStyle("tn", fontSize=14, leading=18)),
      Paragraph(f'<font face="{F_BODY}" size="11">{t}</font>',
                ParagraphStyle("tt", fontSize=11, leading=15)),
      Paragraph(f'<font face="{F_LIGHT}" color="#3A3D44" size="10">{p}</font>',
                ParagraphStyle("tp", fontSize=10, leading=14, alignment=TA_RIGHT))]
     for n, t, p in toc_rows],
    colWidths=[1.6*cm, 13*cm, 2.4*cm]
)
toc.setStyle(TableStyle([
    ("LINEBELOW", (0,0), (-1,-2), 0.4, GRIS_HUMO),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
]))
story.append(toc)

story.append(Spacer(1, 14))
# Nota sobre el ciclo de entrenamiento
note = Table([[
    Paragraph(
        f'<font face="{F_DISPLAY}" color="white" size="10">CÓMO USAR ESTA GUÍA</font><br/>'
        f'<font face="{F_LIGHT}" color="white" size="9">Sigue el ciclo '
        f'<b>2 días de entrenamiento · 1 día de descanso</b> de forma continua, '
        f'sin anclar al calendario semanal. Las sesiones PPL se encadenan en orden rotatorio. '
        f'Si uno de los días activos lo tienes que saltarte (enfermedad, compromiso, poco '
        f'tiempo u otras causas) no pasa nada: continúa donde lo dejaste en la siguiente '
        f'sesión activa. Prioriza, pero sé flexible.</font>',
        ParagraphStyle("nt", fontSize=9.5, leading=13))
]], colWidths=[17*cm])
note.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), GRIS_OSCURO),
    ("LINEBEFORE", (0,0), (0,0), 5, AMBAR),
    ("LEFTPADDING", (0,0), (-1,-1), 12),
    ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ("TOPPADDING", (0,0), (-1,-1), 10),
    ("BOTTOMPADDING", (0,0), (-1,-1), 10),
]))
story.append(note)

# =========== RESUMEN EJECUTIVO ===========
story.append(PageBreak())
story.append(Paragraph("01 · RESUMEN EJECUTIVO", H1))
story.append(HRFlowable(width="100%", thickness=2.5, color=NARANJA, spaceAfter=10))

story.append(Paragraph(
    "Presentamos una rutina <b>PPL (Push-Pull-Legs)</b> optimizada para "
    "<b>hipertrofia muscular</b> (objetivo principal asumido) con variantes de "
    "<b>fuerza</b> y <b>resistencia</b>. Las pautas basadas en evidencia (ACSM 2026) "
    "destacan que lo más importante es el <b>volumen total</b> (≥10 series/semana por "
    "músculo) y la <b>sobrecarga progresiva</b>, más allá de la carga exacta (%1RM) o "
    "el tipo de equipamiento. Para fuerza se recomiendan cargas altas (≥80% 1RM), y "
    "para resistencia repeticiones elevadas con cargas moderadas. La <b>frecuencia "
    "ideal es ≥2 veces/semana</b> por músculo, aunque puede adaptarse de 3 a 6 "
    "días/semana según disponibilidad.", BODY))

story.append(Paragraph(
    "El programa se estructura en 3 sesiones principales: <b>Push</b> (pecho, hombros, "
    "tríceps), <b>Pull</b> (espalda, bíceps) y <b>Legs</b> (piernas completas). Para cada "
    "sesión se ofrecen 3 variantes (hipertrofia, fuerza o resistencia), con ejercicios "
    "clave, series, repeticiones, tempos y descansos recomendados. Incluimos progresiones "
    "semanales, alternativas para lesiones comunes (hombro, rodilla) y adaptaciones de "
    "movilidad. Tablas comparativas y el ciclo de entrenamiento 2+1 completan la guía.", BODY))

story.append(Paragraph(
    "Enfocamos la <b>seguridad y eficacia</b>: calentamiento articular dinámico (5 min "
    "específicos por sesión incluidos en esta guía), series de aproximación antes de "
    "cargas pesadas, descansos adecuados (~1–3 min según objetivo), y énfasis en técnica "
    "correcta. La <b>recuperación</b> (sueño, nutrición y días de descanso activos) es "
    "clave: los músculos se reparan en las 24–48 h posteriores.", BODY))

story.append(Spacer(1, 12))
# KPI strip
story.append(kpi_strip([
    ("≥10",  "SERIES POR MÚSCULO\nSEMANA",       NARANJA),
    ("≥80%", "1RM EN FUERZA",                    ROJO),
    ("8–12", "REP HIPERTROFIA",                  AMBAR),
    ("48 h", "RECUPERACIÓN MÍNIMA\nMUSCULAR",    GRIS_OSCURO),
]))

story.append(Spacer(1, 12))
# Tarjetas objetivo
def goal_card(title, color, body):
    t = Table([
        [Paragraph(f'<font face="{F_DISPLAY}" color="white" size="11">{title}</font>',
                   ParagraphStyle("gt", fontSize=11, leading=13))],
        [Paragraph(body,
                   ParagraphStyle("gb", fontName=F_BODY, fontSize=8.8, leading=11.5,
                                  textColor=GRIS_OSCURO))],
    ], colWidths=[5.55*cm], rowHeights=[0.75*cm, None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), color),
        ("BACKGROUND", (0,1), (0,1), GRIS_CLARO),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 9),
        ("RIGHTPADDING", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
    ]))
    return t

cards_row = Table([[
    goal_card("HIPERTROFIA", NARANJA,
              "Volumen alto. 8–12 rep. RIR 1–2 "
              "(no fallar cada serie). Énfasis en la fase excéntrica."),
    goal_card("FUERZA", ROJO,
              "Cargas ≥80% 1RM. 3–6 rep. "
              "Técnica impecable. 2–3 series por ejercicio."),
    goal_card("RESISTENCIA", AMBAR,
              "15–20 rep con cargas moderadas-bajas. "
              "Mejora la resistencia muscular local."),
]], colWidths=[5.7*cm]*3)
cards_row.setStyle(TableStyle([
    ("LEFTPADDING", (0,0), (-1,-1), 2),
    ("RIGHTPADDING", (0,0), (-1,-1), 2),
]))
story.append(cards_row)

story.append(Spacer(1, 16))
# ── Tabla resumen rápido de las 3 sesiones ──────────────────────────────────
story.append(Paragraph("Las 3 sesiones de un vistazo", H3))
story.append(Spacer(1, 6))
_ps_ov_h  = ParagraphStyle("ovh",  fontName=F_DISPLAY, fontSize=9,  leading=11, textColor=BLANCO,       alignment=TA_CENTER)
_ps_ov_b  = ParagraphStyle("ovb",  fontName=F_BODY,    fontSize=9,  leading=12, textColor=GRIS_OSCURO,  alignment=TA_CENTER)
_ps_ov_lw = ParagraphStyle("ovlw", fontName=F_DISPLAY, fontSize=10, leading=12, textColor=BLANCO,       alignment=TA_CENTER)
_ps_ov_ld = ParagraphStyle("ovld", fontName=F_DISPLAY, fontSize=10, leading=12, textColor=NEGRO,        alignment=TA_CENTER)
_ses_info = [
    ("PUSH",  NARANJA, _ps_ov_lw, "Pectoral mayor · Deltoides anterior · Tríceps braquial",  "Empuje horizontal/vertical",  "60–75 min"),
    ("PULL",  ROJO,    _ps_ov_lw, "Dorsal ancho · Trapecio · Bíceps braquial",               "Tracción y tirón",            "60–75 min"),
    ("LEGS",  AMBAR,   _ps_ov_ld, "Cuádriceps · Isquiotibiales · Glúteo mayor",              "Tren inferior completo",      "60–90 min"),
]
_ov_data = [[
    Paragraph("SESIÓN",                _ps_ov_h),
    Paragraph("MÚSCULOS PRINCIPALES",  _ps_ov_h),
    Paragraph("FUNCIÓN",               _ps_ov_h),
    Paragraph("DURACIÓN",              _ps_ov_h),
]]
for _sl, _sc, _sls, _sm, _sf, _sd in _ses_info:
    _ov_data.append([
        Paragraph(_sl, _sls),
        Paragraph(_sm, _ps_ov_b),
        Paragraph(_sf, _ps_ov_b),
        Paragraph(_sd, _ps_ov_b),
    ])
_ov_tbl = Table(_ov_data, colWidths=[2.0*cm, 7.8*cm, 4.2*cm, 3.0*cm], repeatRows=1)
_ov_style = [
    ("BACKGROUND",    (0,0), (-1,0),  NEGRO),
    ("LINEBELOW",     (0,0), (-1,0),  1.5, NARANJA),
    ("BACKGROUND",    (0,1), (0,1),   NARANJA),
    ("BACKGROUND",    (0,2), (0,2),   ROJO),
    ("BACKGROUND",    (0,3), (0,3),   AMBAR),
    ("ROWBACKGROUNDS",(1,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("BOX",           (0,0), (-1,-1), 0.5, GRIS_MEDIO),
    ("INNERGRID",     (0,0), (-1,-1), 0.25, GRIS_HUMO),
    ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ("RIGHTPADDING",  (0,0), (-1,-1), 7),
    ("TOPPADDING",    (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
]
_ov_tbl.setStyle(TableStyle(_ov_style))
story.append(_ov_tbl)

# =========== 02 PRINCIPIOS ===========
story.append(PageBreak())
story.append(Paragraph("02 · PRINCIPIOS DE ENTRENAMIENTO", H1))
story.append(HRFlowable(width="100%", thickness=2.5, color=NARANJA, spaceAfter=10))

principios = [
    ("Objetivo principal — Hipertrofia",
     "Volumen elevado. Según ACSM 2026, importa el <b>volumen total semanal</b> "
     "(≥10 series/músculo) y enfatizar la fase excéntrica. La carga relativa (30–100% 1RM) "
     "es menos relevante si el esfuerzo es alto. En las variantes de hipertrofia usamos "
     "rangos medios (8–12 rep)."),
    ("Variantes Fuerza / Resistencia",
     "Para <b>fuerza</b>: cargas ≥80% 1RM, 2–3 series por ejercicio, 3–6 rep. Para "
     "<b>resistencia</b>: repeticiones elevadas (~15–20) con cargas moderadas-bajas y "
     "descanso breve, buscando mejorar la resistencia muscular local."),
    ("Ritmo de entrenamiento",
     "Este programa usa un ciclo continuo de <b>2 días activos + 1 día de descanso</b>, "
     "independiente del calendario semanal. Las sesiones PPL se encadenan en rotación "
     "(Push → Pull → Legs → Push → …). Cada grupo muscular se trabaja "
     "<b>cada ~4–5 días</b>. Si se falla un día por enfermedad u otras causas, se "
     "continúa con la siguiente sesión; no se recupera la saltada."),
    ("Equipamiento (máximo y mínimo)",
     "Versiones en gimnasio completo (barra, rack, máquinas) y con equipamiento mínimo "
     "(barra y/o mancuernas, o peso corporal). El tipo de equipamiento <b>no limita la "
     "hipertrofia</b> si el volumen es equivalente. Ej.: banco con barra ↔ press con "
     "mancuernas o flexiones."),
    ("Duración por sesión (45–90 min)",
     "Con descansos de 1–3 min según cansancio, las sesiones duran entre 45 y 90 min aproximadamente."),
    ("Calentamiento (5 min específicos por sesión)",
     "Movilidad articular dinámica + activación con <b>banda elástica</b> + 1–2 series de "
     "aproximación al 50% 1RM del primer ejercicio. Ya llegas activo del camino: el "
     "calentamiento por sesión incluido en esta guía omite el cardio y se centra en "
     "movilidad, activación muscular específica y aproximación."),
]
_princ_accents = [NARANJA, ROJO, AMBAR, NARANJA, ROJO, AMBAR]
for (tit, txt), _acc in zip(principios, _princ_accents):
    story.append(principle_block(tit, txt, _acc))
    story.append(Spacer(1, 16))

# =========== 03 RITMO DE ENTRENAMIENTO ===========
story.append(PageBreak())
story.append(Paragraph("03 · RITMO DE ENTRENAMIENTO", H1))
story.append(HRFlowable(width="100%", thickness=2.5, color=NARANJA, spaceAfter=10))

story.append(Paragraph(
    "El programa sigue un <b>ciclo continuo de 2 días activos + 1 día de descanso</b>, "
    "sin anclarse al calendario semanal. Las sesiones Push, Pull y Legs se encadenan en "
    "rotación. El objetivo es entrenar con constancia: <b>si uno de los días de acción "
    "no puedes ir</b> (enfermedad, compromiso, poco tiempo…) simplemente continúa con la "
    "sesión siguiente cuando puedas — no recuperes la saltada, sigue adelante.", BODY))

story.append(Spacer(1, 12))

# --- KPI del ciclo ---
story.append(kpi_strip([
    ("2+1",  "DÍAS ACTIVOS\n+ DESCANSO",       NEGRO),
    ("6",    "SESIONES\nCada 9 días",           NARANJA),
    ("~4,5", "DÍAS ENTRE\nMismo músculo",       ROJO),
    ("PPL",  "ROTACIÓN\nPush · Pull · Legs",    AMBAR),
]))

story.append(Spacer(1, 16))

# --- Ciclo base visual ---
story.append(Paragraph("Ciclo base de 9 días", H3))

_ciclo = [
    ("DÍA 1",  "PUSH",    NARANJA,    BLANCO),
    ("DÍA 2",  "PULL",    ROJO,       BLANCO),
    ("DÍA 3",  "DESCANSO",GRIS_MEDIO, BLANCO),
    ("DÍA 4",  "LEGS",    AMBAR,      NEGRO),
    ("DÍA 5",  "PUSH",    NARANJA,    BLANCO),
    ("DÍA 6",  "DESCANSO",GRIS_MEDIO, BLANCO),
    ("DÍA 7",  "PULL",    ROJO,       BLANCO),
    ("DÍA 8",  "LEGS",    AMBAR,      NEGRO),
    ("DÍA 9",  "DESCANSO",GRIS_MEDIO, BLANCO),
]
_cw9 = 17.0 * cm / 9

_cps_day = ParagraphStyle("cpd", fontName=F_LIGHT, fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=GRIS_OSCURO)
_cycle_head_row = [Paragraph(d, _cps_day) for d, _, _, _ in _ciclo]

_cycle_sess_row = []
for _d, _s, _bg, _fg in _ciclo:
    _cps_s = ParagraphStyle(f"cps_{_s}", fontName=F_DISPLAY, fontSize=8, leading=10,
                             alignment=TA_CENTER, textColor=_fg)
    _ct = Table([[Paragraph(_s, _cps_s)]], colWidths=[_cw9], rowHeights=[0.82*cm])
    _ct.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), _bg),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 1),
        ("RIGHTPADDING", (0,0), (-1,-1), 1),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    _cycle_sess_row.append(_ct)

_cycle_tbl = Table(
    [_cycle_head_row, _cycle_sess_row],
    colWidths=[_cw9]*9,
    rowHeights=[0.52*cm, 0.9*cm],
)
_cycle_tbl.setStyle(TableStyle([
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 1),
    ("RIGHTPADDING", (0,0), (-1,-1), 1),
    ("TOPPADDING", (0,0), (-1,-1), 1),
    ("BOTTOMPADDING", (0,0), (-1,-1), 1),
    ("BOX", (0,1), (-1,1), 0.5, GRIS_MEDIO),
    ("INNERGRID", (0,1), (-1,1), 0.3, GRIS_HUMO),
]))
story.append(_cycle_tbl)
story.append(Spacer(1, 4))
story.append(Paragraph(
    f'<font face="{F_DISPLAY}" color="#FF6A1A">■</font> PUSH '
    f'&nbsp;&nbsp;<font face="{F_DISPLAY}" color="#E11D2C">■</font> PULL '
    f'&nbsp;&nbsp;<font face="{F_DISPLAY}" color="#F4B400">■</font> LEGS '
    f'&nbsp;&nbsp;<font face="{F_DISPLAY}" color="#9A9CA3">■</font> Descanso',
    CAPTION))

story.append(Spacer(1, 16))

# --- Reglas del ciclo ---
_reglas_ciclo = [
    ("Ciclo continuo sin día fijo",
     "No empieza el lunes ni se reinicia cada semana. Empieza cualquier día y encadena las "
     "sesiones en el orden Push → Pull → Legs, descansando tras cada 2 días activos."),
    ("Día saltado — qué hacer",
     "Si fallas uno de los 2 días activos por enfermedad, necesidad, quedada u otras causas, "
     "<b>no pasa nada</b>: continúa con la sesión siguiente cuando puedas. "
     "<b>No recuperes</b> la sesión perdida; sigue el orden normal donde lo dejaste."),
    ("Descanso extra o semana complicada",
     "Si necesitas más de 1 día de descanso (viaje, fatiga acumulada, semana dura), retoma "
     "el ciclo donde lo dejaste. Un descanso adicional no arruina el progreso."),
    ("Prioridad y constancia",
     "Prioriza siempre que puedas: incluso una sola sesión de las 2 previstas es mejor que "
     "ninguna. <b>La constancia a lo largo de semanas y meses es lo que genera resultados. "
     "La perfección no es el objetivo; la constancia sí.</b>"),
]
for _tit, _txt in _reglas_ciclo:
    story.append(Paragraph(
        f'<font face="{F_DISPLAY}" color="#CC4F0E">▸ {_tit}.</font> '
        f'<font face="{F_BODY}">{_txt}</font>', BODY))
    story.append(Spacer(1, 2))

story.append(Spacer(1, 14))

# --- Ejemplo de 3 semanas ---
story.append(Paragraph("Ejemplo en 3 semanas naturales", H3))
story.append(Paragraph(
    "El ciclo no sigue la semana natural, pero aquí se muestra cómo queda "
    "distribuido en 21 días consecutivos comenzando un lunes:", BODY_LIGHT))
story.append(Spacer(1, 6))

_sem_raw = [
    ("PUSH",    NARANJA,    BLANCO), ("PULL",    ROJO,       BLANCO),
    ("DESC",    GRIS_MEDIO, BLANCO), ("LEGS",    AMBAR,      NEGRO),
    ("PUSH",    NARANJA,    BLANCO), ("DESC",    GRIS_MEDIO, BLANCO),
    ("PULL",    ROJO,       BLANCO), ("LEGS",    AMBAR,      NEGRO),
    ("DESC",    GRIS_MEDIO, BLANCO), ("PUSH",    NARANJA,    BLANCO),
    ("PULL",    ROJO,       BLANCO), ("DESC",    GRIS_MEDIO, BLANCO),
    ("LEGS",    AMBAR,      NEGRO),  ("PUSH",    NARANJA,    BLANCO),
    ("DESC",    GRIS_MEDIO, BLANCO), ("PULL",    ROJO,       BLANCO),
    ("LEGS",    AMBAR,      NEGRO),  ("DESC",    GRIS_MEDIO, BLANCO),
    ("PUSH",    NARANJA,    BLANCO), ("PULL",    ROJO,       BLANCO),
    ("DESC",    GRIS_MEDIO, BLANCO),
]
_dias_sem = ["L", "Ma", "X", "J", "V", "S", "D"]
_sem_lbl  = ["SEM 1", "SEM 2", "SEM 3"]
_cw7h = 1.85*cm
_cw7d = (17.0*cm - _cw7h) / 7

_ps_sh = ParagraphStyle("sh", fontName=F_DISPLAY, fontSize=9,   leading=11, alignment=TA_CENTER, textColor=BLANCO)
_ps_sl = ParagraphStyle("sl", fontName=F_DISPLAY, fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=BLANCO)

_sem_data = [
    [Paragraph("", _ps_sh)] + [Paragraph(d, _ps_sh) for d in _dias_sem]
]
for _si in range(3):
    _row = [Paragraph(_sem_lbl[_si], _ps_sl)]
    for _di in range(7):
        _s, _bg, _fg = _sem_raw[_si*7 + _di]
        _ps_sc = ParagraphStyle(f"sc{_si}{_di}", fontName=F_DISPLAY, fontSize=8, leading=10,
                                alignment=TA_CENTER, textColor=_fg)
        _row.append(Paragraph(_s, _ps_sc))
    _sem_data.append(_row)

_sem_tbl = Table(_sem_data,
                 colWidths=[_cw7h] + [_cw7d]*7,
                 rowHeights=[0.72*cm] + [0.95*cm]*3)
_sem_style = [
    ("BACKGROUND", (0,0), (-1,0), NEGRO),
    ("BACKGROUND", (0,1), (0,-1), GRIS_OSCURO),
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("BOX", (0,0), (-1,-1), 0.6, GRIS_MEDIO),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRIS_HUMO),
    ("LEFTPADDING", (0,0), (-1,-1), 2),
    ("RIGHTPADDING", (0,0), (-1,-1), 2),
    ("TOPPADDING", (0,0), (-1,-1), 3),
    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
]
for _ri in range(1, 4):
    for _di in range(7):
        _s, _bg, _fg = _sem_raw[(_ri-1)*7 + _di]
        _ci = _di + 1
        _sem_style += [("BACKGROUND", (_ci,_ri), (_ci,_ri), _bg)]
_sem_tbl.setStyle(TableStyle(_sem_style))
story.append(_sem_tbl)


# ============================================================
# 7) CÁPSULA DE CORE
# ============================================================
def core_capsule(session_key, accent):
    """Bloque final de sesión: 2 ejercicios de core recomendados por día."""
    _CORE = {
        "PUSH": [
            ["Dead Bug",      "3", "8\u201310 rep/lado",  "3-1-2", "60 seg", "Transverso \u00b7 multífidos \u00b7 coordinación"],
            ["Pallof Press",  "3", "10\u201312 rep/lado", "2-2-2", "60 seg", "Oblicuos \u00b7 core lateral"],
        ],
        "PULL": [
            ["Ab Wheel Rollout",           "3", "6\u201310 rep",      "3-1-2", "75 seg", "Transverso \u00b7 recto abdominal \u00b7 latísimos"],
            ["Plancha lateral + rotación", "3", "8\u201310 rot/lado", "2-1-2", "60 seg", "Cuadrado lumbar \u00b7 oblicuos \u00b7 hombro"],
        ],
        "LEGS": [
            ["Dead Bug",      "3", "8\u201310 rep/lado",  "3-1-2", "60 seg", "Transverso \u00b7 multífidos \u00b7 coordinación"],
            ["Pallof Press",  "3", "10\u201312 rep/lado", "2-2-2", "60 seg", "Oblicuos \u00b7 core lateral"],
        ],
    }
    items = _CORE.get(session_key, [])
    _ps_th = ParagraphStyle("cc_th", fontName=F_DISPLAY, fontSize=8,   leading=10, alignment=TA_CENTER, textColor=BLANCO)
    _ps_td = ParagraphStyle("cc_td", fontName=F_BODY,    fontSize=8.5, leading=11)
    _ps_tc = ParagraphStyle("cc_tc", fontName=F_BODY,    fontSize=8.5, leading=11, alignment=TA_CENTER)
    _header = [Paragraph(h, _ps_th) for h in ["#", "EJERCICIO", "SERIES", "REPS / TIEMPO", "TEMPO", "DESCANSO", "M\u00daSCULOS"]]
    _rows = [_header]
    for i, ej in enumerate(items, 1):
        _ps_num = ParagraphStyle(f"cc_n{i}", fontName=F_DISPLAY, fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=accent)
        _name_cell = Table(
            [[fetch_exercise_image(ej[0], width=1.35*cm, height=1.0*cm),
              Paragraph(f'<font face="{F_BOLD}">{ej[0]}</font>', _ps_td)]],
            colWidths=[1.4*cm, 3.05*cm],
        )
        _name_cell.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
            ("LEFTPADDING",  (1,0), (1,0),   4),
        ]))
        _rows.append([
            Paragraph(str(i), _ps_num),
            _name_cell,
            Paragraph(ej[1], _ps_tc),
            Paragraph(ej[2], _ps_tc),
            Paragraph(ej[3], _ps_tc),
            Paragraph(ej[4], _ps_tc),
            Paragraph(ej[5], _ps_td),
        ])
    # colWidths: 0.55+4.65+1.55+2.3+1.7+2.05+4.2 = 17.0 cm
    _tbl = Table(_rows, colWidths=[0.55*cm, 4.65*cm, 1.55*cm, 2.3*cm, 1.7*cm, 2.05*cm, 4.2*cm])
    _tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  accent),
        ("LINEBELOW",     (0,0), (-1,0),  1.5, BLANCO),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
        ("ALIGN",         (0,1), (0,-1),  "CENTER"),
        ("ALIGN",         (2,1), (5,-1),  "CENTER"),
        ("LEFTPADDING",   (1,1), (1,-1),  3),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("BOX",           (0,0), (-1,-1), 0.6, GRIS_MEDIO),
        ("INNERGRID",     (0,0), (-1,-1), 0.25, GRIS_HUMO),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    _ps_cap = ParagraphStyle("cc_cap", fontName=F_DISPLAY, fontSize=10, leading=13, textColor=BLANCO)
    _ps_sub = ParagraphStyle("cc_sub", fontName=F_LIGHT,   fontSize=8.5, leading=12, textColor=GRIS_CLARO)
    _cap = Table([[
        Paragraph("C\u00c1PSULA DE CORE", _ps_cap),
        Paragraph("Haz estos 2 ejercicios al terminar la sesi\u00f3n, justo antes de la vuelta a la calma.", _ps_sub)
    ]], colWidths=[5*cm, 12*cm])
    _cap.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NEGRO),
        ("LINEBEFORE",    (0,0), (0,0),   5, accent),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    return [_cap, Spacer(1, 4), _tbl]


# ============================================================
# 8) RENDERIZADO DE SESIÓN
# ============================================================
def render_session(codigo, nombre, descripcion, session_key, color,
                   warmup_rows, variantes, tabla_comparativa):
    story.append(PageBreak())
    story.append(section_banner(f"{codigo} · SESIÓN {nombre}",
                                color=color,
                                tag=f"PPL → {nombre.split('·')[0].strip().upper()}"))
    # Foto real de la sesión (Pexels API — requiere PEXELS_API_KEY)
    _photo = fetch_section_photo(session_key, width=17*cm, height=3.5*cm)
    if _photo:
        _photo.hAlign = "CENTER"
        story.append(Spacer(1, 5))
        story.append(_photo)
    story.append(Spacer(1, 10))

    _msc = fetch_section_photo(session_key + "_msc", width=7.5*cm, height=9.5*cm)
    if _msc is None:
        _MUSCLES = {
            "PUSH": [
                ("#FF6A1A", "PRINCIPALES",  ["Pectoral mayor y menor", "Deltoides anterior"]),
                ("#9A9CA3", "SINERGISTAS",  ["Tríceps braquial", "Serrato anterior"]),
            ],
            "PULL": [
                ("#E11D2C", "PRINCIPALES",  ["Dorsal ancho", "Trapecio medio/inf."]),
                ("#9A9CA3", "SINERGISTAS",  ["Bíceps braquial", "Romboides", "Deltoides post."]),
            ],
            "LEGS": [
                ("#F4B400", "PRINCIPALES",  ["Cuádriceps", "Glúteo mayor"]),
                ("#9A9CA3", "SINERGISTAS",  ["Isquiotibiales", "Pantorrillas", "Aductores"]),
            ],
        }
        _c_hex = "#FF6A1A" if session_key == "PUSH" else ("#E11D2C" if session_key == "PULL" else "#F4B400")
        _card_rows = [[Paragraph(
            f'<font face="{F_DISPLAY}" color="white" size="10">MÚSCULOS TRABAJADOS</font>',
            ParagraphStyle("mc_hd", fontSize=10, leading=13, alignment=TA_CENTER))]]
        for _gc, _gl, _gm in _MUSCLES.get(session_key, []):
            _card_rows.append([Paragraph(
                f'<font face="{F_DISPLAY}" color="{_gc}" size="9">\u25ba {_gl}</font>',
                ParagraphStyle("mc_gp", fontSize=9, leading=14, leftIndent=4))])
            for _m in _gm:
                _card_rows.append([Paragraph(
                    f'<font face="{F_LIGHT}" color="#DCDDE1" size="9.5">     • {_m}</font>',
                    ParagraphStyle("mc_mp", fontSize=9.5, leading=13.5, leftIndent=8))])
            _card_rows.append([Paragraph(" ", ParagraphStyle("msp", fontSize=3, leading=4))])
        _msc = Table(_card_rows, colWidths=[7.5*cm])
        _msc.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), NEGRO),
            ("BACKGROUND", (0,0), (-1,0), color),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,0), 8),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("TOPPADDING", (0,1), (-1,-1), 4),
            ("BOTTOMPADDING", (0,1), (-1,-1), 2),
            ("BOX", (0,0), (-1,-1), 2, color),
        ]))
    desc = Table(
        [[Paragraph(descripcion, BODY), _msc]],
        colWidths=[9.3*cm, 7.7*cm],
    )
    desc.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(desc)
    story.append(Spacer(1, 10))

    # Calentamiento 5 min
    for f in warmup_block(nombre.split("·")[0].strip(), color, warmup_rows):
        story.append(f)
    story.append(Spacer(1, 12))

    # Variantes
    for v_nombre, v_color, v_intro, v_ejercicios, v_progresion in variantes:
        story.append(KeepTogether([
            variant_header(v_nombre, v_color),
            Spacer(1, 3),
            Paragraph(v_intro, BODY) if v_intro else Spacer(1,0),
            Spacer(1, 2),
            exercise_table(v_ejercicios, accent=v_color),
            Spacer(1, 4),
            progression_box(v_progresion, color=v_color),
        ]))
        story.append(Spacer(1, 12))

    # Tabla comparativa
    story.append(Paragraph(f"Tabla comparativa — {nombre}", H3))
    story.append(comparative_table(tabla_comparativa))

    # Cápsula de core — KeepTogether evita que el bloque se parta entre páginas
    story.append(Spacer(1, 14))
    story.append(KeepTogether(core_capsule(session_key, color)))


# ============================================================
# 8) DATOS DE LAS SESIONES
# ============================================================

# ---------- PUSH ----------
push_warmup = [
    ("0:00–1:00", "Movilidad de hombros",       "Círculos grandes de hombros + rotaciones de brazos + apertura de pecho hacia atrás · 10–15 reps cada movimiento."),
    ("1:00–2:00", "Band pull-aparts",            "2×20 con banda elástica · activa retractores escapulares y deltoides posterior."),
    ("2:00–3:00", "Rotación externa con banda",  "2×15 cada lado · banda fijada a altura de codo · activa el manguito rotador."),
    ("3:00–4:00", "Flexiones lentas",            "1×10 con 3 s de bajada · activa pectoral, estabilizadores de escápula y core."),
    ("4:00–5:00", "Serie de aproximación",       "1–2 series al 50% 1RM del press de banca · prepara el patrón motor."),
]
push_variantes = [
    ("VARIANTE 1  ·  HIPERTROFIA (volumen alto)", NARANJA,
     "Rango 8–12 rep. Descansa 1–3 min según cansancio. RIR ~1–2.",
     [
        ["Press de banca plano (barra)", "4 × 8–12",    "2-1-2", "1–3 min", "Pectoral · tríceps"],
        ["Press militar (barra/manc.)",  "3 × 8–12",    "2-0-2", "1–3 min", "Deltoides · tríceps"],
        ["Press inclinado mancuernas",   "3 × 8–12",    "2-1-2", "1–3 min", "Pectoral superior"],
        ["Aperturas (máquina/manc.)",    "2–3 × 12–15", "2-0-2", "1–3 min", "Pectorales"],
        ["Elevaciones laterales (manc.)","3 × 12–15",   "2-0-2", "1–3 min", "Deltoides lateral"],
        ["Extensión tríceps en polea",   "3 × 10–15",   "2-0-2", "1–3 min", "Tríceps"],
     ],
     "añadir 1–2 rep por semana o +2–5% de peso al alcanzar el tope de repeticiones. Dejar RIR ~1–2 (no forzar el fallo)."),
    ("VARIANTE 2  ·  FUERZA (cargas altas)", ROJO,
     "Cargas ≥80% 1RM, 3–6 rep. Descansa 1–3 min. Técnica impecable.",
     [
        ["Press de banca pesado",           "4 × 4–6",    "3-1-1", "1–3 min", "Pectoral (fuerza)"],
        ["Press militar pesado",            "3 × 4–6",    "2-1-1", "1–3 min", "Hombros"],
        ["Fondos en paralelas",             "3 × 6–8",    "2-0-2", "1–3 min", "Pectoral · tríceps"],
        ["Elevaciones laterales",         "3 × 12–15",   "2-0-2", "1–3 min", "Deltoides lateral"],
        ["Press francés (barra/manc.)",    "3 × 6–10",    "2-0-2", "1–3 min", "Tríceps (fuerza)"],
        ["Extensión tríceps mancuernas",   "3 × 6–10",   "2-0-2", "1–3 min", "Tríceps (fuerza)"],
     ],
     "aumentar carga ~5% al lograr rep máximas manteniendo técnica. Cargas ≥80% 1RM."),
    ("VARIANTE 3  ·  RESISTENCIA MUSCULAR", AMBAR,
     "Repeticiones altas (15–20) con cargas moderadas-bajas. Descansa 1–3 min.",
     [
        ["Press banca con mancuernas",    "3 × 15–20",   "2-0-2", "1–3 min", "Pectoral"],
        ["Flexiones (push-ups)",          "3 × 15–20",   "2-0-2", "1–3 min", "Pecho · hombros"],
        ["Press sentado en máquina",      "3 × 15–20",   "2-0-2", "1–3 min", "Hombros · tríceps"],
        ["Elevaciones laterales ligeras",  "3 × 15–20",   "2-0-2", "1–3 min", "Deltoides lateral"],
        ["Extensión tríceps tras nuca",   "2–3 × 15–20", "2-0-2", "1–3 min", "Tríceps (cabeza larga)"],
     ],
     "incrementar repeticiones o series gradualmente. Mantener buena forma, evitando impulsos."),
]
push_comp = [
    ["Variante 1", "Hipertrofia", "Alta (~15–18)", "Moderada (8–12 rep)", "Barra · manc. · máquina"],
    ["Variante 2", "Fuerza",       "Media (~9–12)", "Alta (3–6 rep)",      "Barra · mancuerna (pesas libres)"],
    ["Variante 3", "Resistencia",  "Alta (12–15)",  "Baja (15–20 rep)",    "Mancuernas · peso corporal · máquinas"],
]
render_session(
    "04", "PUSH  ·  Pecho · Hombros · Tríceps",
    "En <b>Push</b> trabajamos principalmente el <b>pectoral mayor</b>, los "
    "<b>deltoides anterior y lateral</b> y los <b>tríceps</b>. A continuación se "
    "muestran tres variantes con objetivos distintos. Antes de comenzar, realiza el "
    "calentamiento específico de 5 minutos.",
    "PUSH", NARANJA, push_warmup, push_variantes, push_comp
)

# ---------- PULL ----------
pull_warmup = [
    ("0:00–1:00", "Movilidad torácica",       "Cat-cow + rotaciones torácicas en cuadrupedia · 8 reps cada lado · libera la columna."),
    ("1:00–2:00", "Band pull-aparts",         "2×20 con banda elástica · activa romboides, trapecio medio y retractores escapulares."),
    ("2:00–3:00", "Face pulls con banda",     "2×15 · banda fijada a altura de cara · activa deltoides posterior y rotadores externos."),
    ("3:00–4:00", "Dead-hang colgado",        "20–30 s colgado de la barra · descomprime columna y activa agarre y dorsales."),
    ("4:00–5:00", "Aproximación al jalón",   "1–2 series ligeras al 50% 1RM · prepara el patrón de jalón."),
]
pull_variantes = [
    ("VARIANTE 1  ·  HIPERTROFIA", NARANJA,
     "Volumen alto, 8–12 rep. Descansa 1–3 min.",
     [
        ["Jalón al pecho (polea)",         "4 × 8–12",  "2-1-2", "1–3 min", "Dorsales"],
        ["Remo con barra (o T-bar)",       "3 × 8–12",  "2-1-1", "1–3 min", "Dorsal · romboides"],
        ["Remo en máquina sentado",        "3 × 8–12",  "2-0-2", "1–3 min", "Espalda media"],
        ["Curl martillo (manc.)",          "3 × 12–15", "2-0-2", "1–3 min", "Bíceps · braquial"],
        ["Curl de bíceps (barra/manc.)",   "3 × 8–12",  "2-0-2", "1–3 min", "Bíceps"],
        ["Face pulls",                     "2 × 12–15", "2-0-2", "1–3 min", "Post. hombros · trapecio"],
     ],
     "añadir 1–2 rep por semana o +2–5% de peso. RIR 1–2."),
    ("VARIANTE 2  ·  FUERZA", ROJO,
     "Cargas pesadas, 4–6 rep. Descansa 1–3 min. (El peso muerto cubre el día de piernas.)",
     [
        ["Dominadas",                       "4 × 4–6",  "2-0-2", "1–3 min", "Dorsales · bíceps"],
        ["Remo con barra pesado",           "3 × 4–6",  "2-1-1", "1–3 min", "Dorsal · romboides (fuerza)"],
        ["Remo en polea sentada (neutro)",  "3 × 6–8",  "2-0-2", "1–3 min", "Espalda media (sin carga lumbar)"],
        ["Jalón agarre estrecho (polea)",   "3 × 6–8",  "2-0-2", "1–3 min", "Dorsales · romboides"],
        ["Curl con barra Z pesado",         "3 × 6–8",  "2-0-2", "1–3 min", "Bíceps (fuerza)"],
     ],
     "elevar peso cada semana si es posible, manteniendo 2–3 rep en reserva."),
    ("VARIANTE 3  ·  RESISTENCIA", AMBAR,
     "Repeticiones altas, cargas moderadas. Descansa 1–3 min.",
     [
        ["Remo polea baja (agarre ancho)",  "3 × 15–20", "2-0-2", "1–3 min", "Espalda"],
        ["Jalón agarre neutro",             "3 × 15–20", "2-0-2", "1–3 min", "Dorsales"],
        ["Remo máquina (agarre neutro)",    "3 × 15–20", "2-0-2", "1–3 min", "Zona media espalda"],
        ["Curl bíceps alterno (manc.)",     "3 × 15–20", "2-0-2", "1–3 min", "Bíceps (resistencia)"],
        ["Jalón brazos rígidos en polea",  "2 × 15–20", "2-0-2", "1–3 min", "Dorsal · serratos"],
     ],
     "incrementar repeticiones o series gradualmente."),
]
pull_comp = [
    ["Variante 1", "Hipertrofia", "Alta (~15–18)", "Moderada (8–12 rep)", "Barra · mancuerna · polea"],
    ["Variante 2", "Fuerza",       "Media (~8–12)", "Alta (3–6 rep)",      "Barra · mancuerna"],
    ["Variante 3", "Resistencia",  "Alta (12–15)",  "Baja (15–20 rep)",    "Polea · mancuerna"],
]
render_session(
    "05", "PULL  ·  Espalda · Bíceps",
    "La sesión <b>Pull</b> enfatiza la <b>espalda</b> (dorsales, trapecio, "
    "romboides, deltoides posterior) y los <b>bíceps</b>. Ejercicios clave: jalones, "
    "remos y curl. Realiza primero el calentamiento de 5 minutos.",
    "PULL", ROJO, pull_warmup, pull_variantes, pull_comp
)

# ---------- LEGS ----------
legs_warmup = [
    ("0:00–1:00", "Movilidad de cadera",       "Balanceos de pierna adelante/atrás y laterales · 10 cada lado · libera flexores y abductores."),
    ("1:00–2:00", "Movilidad de tobillos",     "Knee-to-wall en zancada · 8 reps por lado · mejora la profundidad en sentadilla."),
    ("2:00–3:00", "Monster walks con banda",   "2×12 pasos laterales con banda elástica en rodillas · activa glúteo medio y abductores."),
    ("3:00–4:00", "Glute bridge con banda",    "2×15 · banda en rodillas · activa glúteos y cadena posterior antes de los compuestos."),
    ("4:00–5:00", "Sentadillas progresivas",   "1×10 con peso corporal + 1–2 series al 50% 1RM · prepara el patrón motor de sentadilla."),
]
legs_variantes = [
    ("VARIANTE 1  ·  HIPERTROFIA", NARANJA,
     "Rango 8–12 rep. Descansa 1–3 min.",
     [
        ["Sentadilla con barra",           "4 × 8–12",       "2-1-2", "1–3 min", "Cuádriceps · glúteos"],
        ["Peso muerto rumano",             "3 × 8–12",       "3-1-1", "1–3 min", "Isquios · glúteos"],
        ["Prensa de piernas",              "3 × 10–12",      "2-0-2", "1–3 min", "Cuádriceps · glúteos"],
        ["Zancadas con mancuernas",        "3 × 10 / pierna", "2-0-2", "1–3 min", "Cuádriceps · glúteos"],
        ["Elevación de talones",           "3 × 12–15",      "2-0-2", "1–3 min", "Gemelos"],
     ],
     "añadir 1–2 rep por semana o +2–5% de peso. RIR 1–2."),
    ("VARIANTE 2  ·  FUERZA", ROJO,
     "Cargas pesadas, técnica perfecta. Descansa 1–3 min.",
     [
        ["Sentadilla trasera pesada",      "4 × 4–6",       "3-1-1", "1–3 min", "Fuerza total piernas"],
        ["Peso muerto (estándar o sumo)",  "3 × 4–6",       "3-1-1", "1–3 min", "Cadena posterior"],
        ["Zancada búlgara (barra/manc.)",  "3 × 6–8 / pierna", "2-0-2", "1–3 min", "Cuádriceps · glúteos"],
        ["Hip Thrust con barra",           "3 × 6–8",       "2-1-1", "1–3 min", "Glúteos"],
        ["Curl femoral tumbado (máquina)", "3 × 6–8",       "2-0-2", "1–3 min", "Isquiotibiales"],
     ],
     "aumentar peso según capacidad, manteniendo técnica."),
    ("VARIANTE 3  ·  RESISTENCIA", AMBAR,
     "Repeticiones altas. Descansa 1–3 min.",
     [
        ["Sentadilla libre (cuerpo)",      "3 × 15–20",      "2-0-2", "1–3 min", "Cuádriceps · glúteos"],
        ["Step-ups (subida a banco)",      "3 × 15 / pierna", "2-0-2", "1–3 min", "Piernas · glúteos"],
        ["Puente de glúteos (hip thrust)", "3 × 15–20",      "2-0-2", "1–3 min", "Glúteos · coxales"],
        ["Prensa de piernas ligera",       "3 × 15–20",      "2-0-2", "1–3 min", "Cuádriceps"],
        ["Elevación de gemelos",           "3 × 20–25",      "2-0-2", "1–3 min", "Gemelos"],
     ],
     "incrementar repeticiones o series gradualmente."),
]
legs_comp = [
    ["Variante 1", "Hipertrofia", "Alta (~15–18)", "Moderada (8–12 rep)", "Barra · máquina · mancuerna"],
    ["Variante 2", "Fuerza",       "Media (~8–12)", "Alta (3–6 rep)",      "Barra · máquina (peso libre)"],
    ["Variante 3", "Resistencia",  "Alta (12–15)",  "Baja (15–20 rep)",    "Mancuerna · peso corporal"],
]
render_session(
    "06", "LEGS  ·  Piernas Completas",
    "La sesión <b>Legs</b> trabaja <b>cuádriceps</b>, <b>glúteos</b>, "
    "<b>isquiotibiales</b>, <b>aductores/abductores</b> y <b>gemelos</b>. Se plantean "
    "tres variantes. Calentamiento específico de 5 minutos antes de comenzar.",
    "LEGS", AMBAR, legs_warmup, legs_variantes, legs_comp
)

# ============================================================
# 9) RECUPERACIÓN Y LESIONES
# ============================================================
story.append(PageBreak())
story.append(Paragraph("07 · RECUPERACIÓN Y SEGURIDAD", H1))
story.append(HRFlowable(width="100%", thickness=2.5, color=NARANJA, spaceAfter=10))

story.append(Paragraph(
    "La <b>recuperación es esencial</b>. Tras entrenar un grupo muscular debe descansarse "
    "<b>≥48 horas</b> antes de volver a estimularlo intensamente. En días de descanso se "
    "puede realizar actividad ligera (caminar, bicicleta suave o movilidad) para mejorar "
    "la circulación. El <b>sueño (7–9 h)</b> y la <b>nutrición</b> (proteínas y calorías "
    "adecuadas) son críticos. Aplicar <b>sobrecarga progresiva</b>: aumentar peso/series "
    "poco a poco, y ajustar el plan si hay estancamiento.", BODY))

story.append(Paragraph(
    "Para <b>seguridad muscular-articular</b>, enfatiza técnica y forma adecuada (evitar "
    "hiperextensión de rodilla o lumbar, mantener espalda recta en peso muerto, etc.). "
    "<b>No es necesario entrenar al fallo</b> cada serie; detenerse con 1–2 repeticiones "
    "en reserva es suficiente. Varía el estímulo (peso, volumen o frecuencia) cada pocas "
    "semanas para seguir progresando.", BODY))

# Cierre
story.append(Spacer(1, 6))
closing = Table([[Paragraph(
    f'<font face="{F_DISPLAY}" color="white" size="13">LA CONSTANCIA Y LA PROGRESIÓN GRADUAL SON LA CLAVE</font><br/>'
    f'<font face="{F_LIGHT}" color="white" size="10">El mejor entrenamiento es el que se '
    f'mantiene en el tiempo. Con este plan PPL adaptado a tu nivel y objetivo, cubrimos '
    f'todos los músculos por sesión y ofrecemos variantes prácticas para cada situación.</font>',
    ParagraphStyle("close", fontSize=12, leading=16))]],
    colWidths=[17*cm])
closing.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), NEGRO),
    ("LINEBEFORE", (0,0), (0,0), 8, NARANJA),
    ("LEFTPADDING", (0,0), (-1,-1), 16),
    ("RIGHTPADDING", (0,0), (-1,-1), 16),
    ("TOPPADDING", (0,0), (-1,-1), 16),
    ("BOTTOMPADDING", (0,0), (-1,-1), 16),
]))
story.append(closing)

# ============================================================
# 10) VUELTA A LA CALMA
# ============================================================
story.append(PageBreak())
story.append(Paragraph("08 · VUELTA A LA CALMA", H1))
story.append(HRFlowable(width="100%", thickness=2.5, color=NARANJA, spaceAfter=10))

story.append(Paragraph(
    "La vuelta a la calma es el protocolo post-entrenamiento que acelera la recuperaci\u00f3n, "
    "reduce las agujetas (DOMS) y devuelve el sistema nervioso aut\u00f3nomo a la rama "
    "parasimpatica. <b>Aplicarla de forma sistem\u00e1tica mejora la calidad de los entrenamientos "
    "siguientes</b> m\u00e1s que cualquier suplemento. Duraci\u00f3n: ~8 minutos.", BODY))
story.append(Spacer(1, 10))

# Estilos compartidos
_vtc_th = ParagraphStyle("vtc_th", fontName=F_DISPLAY, fontSize=8,   leading=10, alignment=TA_CENTER, textColor=BLANCO)
_vtc_ca = ParagraphStyle("vtc_ca", fontName=F_BODY,    fontSize=8.5, leading=12)
_vtc_cc = ParagraphStyle("vtc_cc", fontName=F_BODY,    fontSize=8.5, leading=12, alignment=TA_CENTER)

# --- Bloque 1: Circulación activa ---
story.append(Paragraph("Bloque 1 \u00b7 Circulaci\u00f3n activa  (2 min)", H3))
story.append(Spacer(1, 4))
_vtc_circ = Table(
    [
        [Paragraph("MOVIMIENTO", _vtc_th), Paragraph("DURACI\u00d3N", _vtc_th), Paragraph("EFECTO", _vtc_th)],
        [Paragraph("Marcha en sitio + balanceo de brazos", _vtc_ca),
         Paragraph("60 seg", _vtc_cc),
         Paragraph("Reactiva el retorno venoso y elimina el lactato sin a\u00f1adir estr\u00e9s muscular", _vtc_ca)],
        [Paragraph("Cat-Cow lento en cuadrupedia (respirando)", _vtc_ca),
         Paragraph("60 seg", _vtc_cc),
         Paragraph("Moviliza toda la columna y libera erectors y mult\u00edfidos tras la carga", _vtc_ca)],
    ],
    colWidths=[5.5*cm, 2.5*cm, 9.0*cm])
_vtc_circ.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  NEGRO),
    ("LINEBELOW",     (0,0), (-1,0),  1.5, NARANJA),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("BOX",           (0,0), (-1,-1), 0.5, GRIS_MEDIO),
    ("INNERGRID",     (0,0), (-1,-1), 0.25, GRIS_HUMO),
    ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ("RIGHTPADDING",  (0,0), (-1,-1), 7),
    ("TOPPADDING",    (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(_vtc_circ)
story.append(Spacer(1, 12))

# --- Bloque 2: Estiramientos PNF ---
story.append(Paragraph("Bloque 2 \u00b7 Estiramientos PNF  (3 min)", H3))
story.append(Paragraph(
    "T\u00e9cnica contracci\u00f3n-relajaci\u00f3n: <b>contrae el m\u00fasculo 6 seg</b>, suelta, "
    "<b>profundiza el estiramiento 15\u201320 seg</b>. M\u00e1s eficaz que el estiramiento "
    "est\u00e1tico puro para restaurar la longitud del sarc\u00f3mero.", BODY_LIGHT))
story.append(Spacer(1, 6))
_vtc_pnf_ps = ParagraphStyle("vtc_pnf_s", fontName=F_DISPLAY, fontSize=9, leading=11, alignment=TA_CENTER, textColor=BLANCO)
_vtc_pnf_data = [
    [Paragraph("SESI\u00d3N", _vtc_th), Paragraph("ESTIRAMIENTO", _vtc_th),
     Paragraph("DURACI\u00d3N", _vtc_th), Paragraph("ZONA", _vtc_th)],
    [Paragraph("PUSH", _vtc_pnf_ps),
     Paragraph("Pectoral en marco de puerta (PNF)", _vtc_ca),
     Paragraph("2 \u00d7 20 seg", _vtc_cc), Paragraph("Pectoral \u00b7 deltoides anterior", _vtc_ca)],
    [Paragraph("", _vtc_pnf_ps),
     Paragraph("Estiramiento cruzado de hombro", _vtc_ca),
     Paragraph("2 \u00d7 20 seg/lado", _vtc_cc), Paragraph("Deltoides posterior \u00b7 manguito", _vtc_ca)],
    [Paragraph("", _vtc_pnf_ps),
     Paragraph("Extensi\u00f3n de mu\u00f1eca en suelo", _vtc_ca),
     Paragraph("30 seg", _vtc_cc), Paragraph("Antebrazos (tras los presses)", _vtc_ca)],
    [Paragraph("PULL", _vtc_pnf_ps),
     Paragraph("Child's pose con brazos extendidos", _vtc_ca),
     Paragraph("2 \u00d7 30 seg", _vtc_cc), Paragraph("Dorsal ancho \u00b7 columna tor\u00e1cica", _vtc_ca)],
    [Paragraph("", _vtc_pnf_ps),
     Paragraph("Estiramiento b\u00edceps contra pared", _vtc_ca),
     Paragraph("2 \u00d7 20 seg/lado", _vtc_cc), Paragraph("B\u00edceps braquial", _vtc_ca)],
    [Paragraph("", _vtc_pnf_ps),
     Paragraph("Inclinaci\u00f3n lateral de cuello + rotaci\u00f3n", _vtc_ca),
     Paragraph("30 seg/lado", _vtc_cc), Paragraph("Trapecio \u00b7 esternocleidomastoideo", _vtc_ca)],
    [Paragraph("LEGS", _vtc_pnf_ps),
     Paragraph("Pigeon pose (suelo o en banco)", _vtc_ca),
     Paragraph("45 seg/lado", _vtc_cc), Paragraph("Gl\u00fateos \u00b7 psoas \u00b7 TFL", _vtc_ca)],
    [Paragraph("", _vtc_pnf_ps),
     Paragraph("Estocada baja con rotaci\u00f3n tor\u00e1cica", _vtc_ca),
     Paragraph("30 seg/lado", _vtc_cc), Paragraph("Hip flexors \u00b7 columna tor\u00e1cica", _vtc_ca)],
    [Paragraph("", _vtc_pnf_ps),
     Paragraph("Estiramiento de gemelo en pared", _vtc_ca),
     Paragraph("30 seg/lado", _vtc_cc), Paragraph("Gastrocnemio \u00b7 s\u00f3leo", _vtc_ca)],
]
_vtc_pnf = Table(_vtc_pnf_data, colWidths=[2.0*cm, 6.5*cm, 3.0*cm, 5.5*cm])
_vtc_pnf.setStyle(TableStyle([
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ("BACKGROUND",    (0,0), (-1,0),  NEGRO),
    ("LINEBELOW",     (0,0), (-1,0),  1.5, NARANJA),
    ("BACKGROUND",    (0,1), (0,3),   NARANJA),
    ("BACKGROUND",    (0,4), (0,6),   ROJO),
    ("BACKGROUND",    (0,7), (0,9),   AMBAR),
    ("SPAN",          (0,1), (0,3)),
    ("SPAN",          (0,4), (0,6)),
    ("SPAN",          (0,7), (0,9)),
    ("ALIGN",         (0,1), (0,-1),  "CENTER"),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("BOX",           (0,0), (-1,-1), 0.5, GRIS_MEDIO),
    ("INNERGRID",     (0,0), (-1,-1), 0.25, GRIS_HUMO),
    ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ("RIGHTPADDING",  (0,0), (-1,-1), 7),
    ("TOPPADDING",    (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(_vtc_pnf)
story.append(Spacer(1, 12))

# --- Bloque 3: Reset del SNA ---
story.append(Paragraph("Bloque 3 \u00b7 Reset del sistema nervioso  (3 min)", H3))
story.append(Paragraph(
    "Paso de la rama simp\u00e1tica (activaci\u00f3n) a la parasimpatica (recuperaci\u00f3n). "
    "Reduce el cortisol circulante y abre la ventana anab\u00f3lica m\u00e1s r\u00e1pido.", BODY_LIGHT))
story.append(Spacer(1, 6))
_vtc_sna = Table(
    [
        [Paragraph("T\u00c9CNICA", _vtc_th), Paragraph("C\u00d3MO", _vtc_th), Paragraph("EFECTO", _vtc_th)],
        [Paragraph("Respiraci\u00f3n 4-6-8", _vtc_ca),
         Paragraph("Inhala 4 seg \u00b7 ret\u00e9n 6 seg \u00b7 exhala 8 seg. Repite 10 veces.", _vtc_ca),
         Paragraph("Activa el nervio vago \u2192 baja la FC y el cortisol en minutos", _vtc_ca)],
        [Paragraph("Legs-up-the-wall (piernas en la pared)", _vtc_ca),
         Paragraph("T\u00fambate en suelo con piernas apoyadas verticalmente en la pared. Brazos abiertos. 2 min.", _vtc_ca),
         Paragraph("Drena el lactato de las extremidades \u00b7 activa la respuesta de recuperaci\u00f3n del SNA", _vtc_ca)],
    ],
    colWidths=[4.0*cm, 7.0*cm, 6.0*cm])
_vtc_sna.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  NEGRO),
    ("LINEBELOW",     (0,0), (-1,0),  1.5, NARANJA),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("BOX",           (0,0), (-1,-1), 0.5, GRIS_MEDIO),
    ("INNERGRID",     (0,0), (-1,-1), 0.25, GRIS_HUMO),
    ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ("RIGHTPADDING",  (0,0), (-1,-1), 7),
    ("TOPPADDING",    (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(_vtc_sna)
story.append(Spacer(1, 12))

# --- Tips de recuperación ---
story.append(Paragraph("Tips de recuperaci\u00f3n post-entrenamiento", H3))
story.append(Spacer(1, 4))
_vtc_tips = Table(
    [
        [Paragraph("TIP", _vtc_th), Paragraph("QU\u00c9 HACER", _vtc_th), Paragraph("POR QU\u00c9 FUNCIONA", _vtc_th)],
        [Paragraph("Prote\u00edna post-entreno", _vtc_ca),
         Paragraph("20\u201340 g en los 45 min siguientes al entrenamiento.", _vtc_ca),
         Paragraph("La s\u00edntesis prote\u00edca muscular (MPS) es m\u00e1xima en esa ventana. Sin prote\u00edna no hay reparaci\u00f3n.", _vtc_ca)],
        [Paragraph("Caminata de vuelta", _vtc_ca),
         Paragraph("La caminata al salir del gimnasio ya act\u00faa como enfriamiento activo.", _vtc_ca),
         Paragraph("El movimiento ligero continuo elimina metabolitos mejor que el reposo inmediato.", _vtc_ca)],
        [Paragraph("Ducha tibia post-entreno", _vtc_ca),
         Paragraph("Ducha tibia o caliente justo despu\u00e9s. Reserva el contraste fr\u00edo/calor para d\u00edas de descanso o 4\u20136 h despu\u00e9s.", _vtc_ca),
         Paragraph("El fr\u00edo inmediato inhibe la v\u00eda mTOR (s\u00edntesis prote\u00edca). La inflamaci\u00f3n inicial es necesaria para el crecimiento.", _vtc_ca)],
        [Paragraph("Descanso activo al d\u00eda siguiente", _vtc_ca),
         Paragraph("20 min de movimiento ligero (caminar, movilidad) en los d\u00edas de descanso.", _vtc_ca),
         Paragraph("Reduce las agujetas (DOMS) mejor que el reposo total. El flujo sangu\u00edneo acelera la reparaci\u00f3n tisular.", _vtc_ca)],
        [Paragraph("Sue\u00f1o 7\u20139 h", _vtc_ca),
         Paragraph("Prioriza el sue\u00f1o especialmente en las 48 h post-entrenamiento de alta intensidad.", _vtc_ca),
         Paragraph("La mayor parte de la hormona del crecimiento y la reparaci\u00f3n muscular ocurre en sue\u00f1o profundo (NREM fase 3).", _vtc_ca)],
    ],
    colWidths=[3.5*cm, 6.5*cm, 7.0*cm])
_vtc_tips.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,0),  NEGRO),
    ("LINEBELOW",     (0,0), (-1,0),  1.5, NARANJA),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("BOX",           (0,0), (-1,-1), 0.5, GRIS_MEDIO),
    ("INNERGRID",     (0,0), (-1,-1), 0.25, GRIS_HUMO),
    ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ("RIGHTPADDING",  (0,0), (-1,-1), 7),
    ("TOPPADDING",    (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(_vtc_tips)
story.append(Spacer(1, 14))

# --- Cardio opcional ---
_vtc_cardio = Table([[Paragraph(
    f'<font face="{F_DISPLAY}" color="white" size="10">CARDIO POST-ENTRENAMIENTO \u00b7 OPCIONAL</font><br/>'
    f'<font face="{F_LIGHT}" color="white" size="9">Para cuando apetezca \u2014 nunca obligatorio. '
    f'<b>Bici est\u00e1tica o cinta caminando r\u00e1pido (~5,5 km/h)</b> durante 15\u201330 min. '
    f'Mant\u00e9n la frecuencia card\u00edaca en la zona aer\u00f3bica suave: <b>120\u2013130 ppm</b>. '
    f'Sin pantalla de la m\u00e1quina: pon el m\u00f3vil en un soporte y ve lo que quieras. '
    f'Este cardio no acumula fatiga significativa y mejora la capacidad cardiovascular '
    f'de base sin interferir con la hipertrofia si la carga total est\u00e1 controlada.</font>',
    ParagraphStyle("vtc_cardio_p", fontSize=9.5, leading=14))]], colWidths=[17*cm])
_vtc_cardio.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,-1), GRIS_OSCURO),
    ("LINEBEFORE",    (0,0), (0,0),   6, AMBAR),
    ("LEFTPADDING",   (0,0), (-1,-1), 14),
    ("RIGHTPADDING",  (0,0), (-1,-1), 14),
    ("TOPPADDING",    (0,0), (-1,-1), 12),
    ("BOTTOMPADDING", (0,0), (-1,-1), 12),
]))
story.append(_vtc_cardio)

# ============================================================
# 11) GLOSARIO
# ============================================================
story.append(PageBreak())
story.append(Paragraph("09 · GLOSARIO Y NOTAS T\u00c9CNICAS", H1))
story.append(HRFlowable(width="100%", thickness=2.5, color=NARANJA, spaceAfter=10))

glosario = [
    ("1RM",  "Una repetición máxima. La carga con la que sólo puedes hacer 1 rep con técnica correcta. "
             "Se usa como referencia para porcentajes de intensidad (ej. 80% 1RM)."),
    ("RIR",  "Repeticiones en reserva. RIR 2 = paras la serie cuando podrías hacer 2 reps más con buena técnica. "
             "Útil para regular el esfuerzo sin entrenar al fallo."),
    ("Tempo", "Cadencia de ejecución en formato A-B-C (ej. 2-1-2): A s en fase excéntrica (bajar), "
              "B s de pausa, C s en fase concéntrica (subir). El primer número es siempre la bajada."),
    ("ROM",  "Range of Motion · rango de movimiento. Reducir el ROM significa no completar la trayectoria total "
             "(p.ej. sentadilla a media profundidad)."),
    ("Volumen", "Producto de series × repeticiones × carga, o frecuentemente como series semanales por grupo muscular. "
                "≥10 series/semana por músculo es la referencia mínima ACSM 2026 para hipertrofia."),
    ("Frecuencia", "Veces por semana que se entrena un mismo grupo muscular. Frecuencia 2 = dos sesiones semanales "
                   "para ese grupo, recomendable sobre frecuencia 1."),
    ("Sobrecarga progresiva", "Incrementar gradualmente el estímulo (peso, repeticiones, series, control del tempo, "
                              "reducción de descanso) para seguir adaptándose."),
    ("Fase excéntrica", "Parte del movimiento donde el músculo se alarga bajo tensión (bajar la barra en press de banca). "
                        "Asociada a más daño muscular e hipertrofia."),
]
_ps_gk = ParagraphStyle("gk", fontName=F_DISPLAY, fontSize=10, leading=13, textColor=NARANJA)
gdata = [["TÉRMINO", "DEFINICIÓN"]]
for k, v in glosario:
    gdata.append([
        Paragraph(k, _ps_gk),
        Paragraph(v, ParagraphStyle("gl", fontName=F_BODY, fontSize=9.5, leading=13)),
    ])
gtbl = Table(gdata, colWidths=[4.2*cm, 12.8*cm], repeatRows=1)
gtbl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), NEGRO),
    ("TEXTCOLOR", (0,0), (-1,0), BLANCO),
    ("FONTNAME", (0,0), (-1,0), F_DISPLAY),
    ("FONTSIZE", (0,0), (-1,0), 9),
    ("ALIGN", (0,0), (0,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ("BOX", (0,0), (-1,-1), 0.5, GRIS_MEDIO),
    ("INNERGRID", (0,0), (-1,-1), 0.25, GRIS_HUMO),
    ("LINEBELOW", (0,0), (-1,0), 1.5, NARANJA),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
]))
story.append(gtbl)

story.append(Spacer(1, 16))
story.append(Paragraph(
    f'<font face="{F_LIGHT}" color="#3A3D44" size="9"><b>Fuentes y notas:</b> '
    f'Guía profesional basada en las directrices de la American College of Sports Medicine '
    f'(ACSM) y en literatura de entrenamiento de fuerza/hipertrofia. Los parámetros '
    f'(objetivo, frecuencia, equipamiento, repeticiones) reflejan el briefing del usuario. '
    f'Las fotos de sesión son servidas por Pexels (pexels.com) bajo licencia gratuita. '
    f'Documento de uso personal sin valor médico. '
    f'Consulta a un profesional sanitario ante cualquier dolor o lesión.</font>',
    ParagraphStyle("nt", fontSize=9, leading=12, alignment=TA_JUSTIFY)))


# ============================================================
# 11) BUILD
# ============================================================
doc = BaseDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=1.95*cm, bottomMargin=1.55*cm,
    title="Rutina PPL · Edición Premium 2026",
    author="Guía profesional de entrenamiento",
)
frame_cover = Frame(0, 0, A4[0], A4[1], leftPadding=0, rightPadding=0,
                    topPadding=0, bottomPadding=0, id="cover")
frame_content = Frame(2*cm, 1.55*cm, A4[0]-4*cm, A4[1]-3.5*cm,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                      id="content")
doc.addPageTemplates([
    PageTemplate(id="cover",   frames=[frame_cover],   onPage=draw_cover),
    PageTemplate(id="content", frames=[frame_content], onPage=draw_header_footer),
])
doc.build(story)
print(f"OK -> {OUTPUT}")
