# -*- coding: utf-8 -*-
"""Convierte las Rondana OTF (CFF) a TTF (glyf) para usarlas con ReportLab."""
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from cu2qu.pens import Cu2QuPen
import os

PAIRS = [
    ("Rondana Black.otf",       "Rondana-Black.ttf"),
    ("Rondana Regular.otf",     "Rondana-Regular.ttf"),
    ("Rondana Light.otf",       "Rondana-Light.ttf"),
    ("Rondana Ultra Light.otf", "Rondana-UltraLight.ttf"),
]

def otf_to_ttf(src, dst, max_err=1.0):
    font = TTFont(src)
    glyph_order = font.getGlyphOrder()
    cff_table = font["CFF "]
    top_dict = cff_table.cff[cff_table.cff.fontNames[0]]
    cs = top_dict.CharStrings

    glyf_glyphs = {}
    for gname in glyph_order:
        pen = TTGlyphPen(None)
        quad_pen = Cu2QuPen(pen, max_err=max_err, reverse_direction=True)
        cs[gname].draw(quad_pen)
        glyf_glyphs[gname] = pen.glyph()

    new = TTFont(sfntVersion="\x00\x01\x00\x00")
    for tag in ["head", "hhea", "OS/2", "name", "cmap", "post", "hmtx"]:
        if tag in font:
            new[tag] = font[tag]
    new.setGlyphOrder(glyph_order)

    glyf = newTable("glyf")
    glyf.glyphs = glyf_glyphs
    new["glyf"] = glyf
    new["loca"] = newTable("loca")

    maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(glyph_order)
    max_pts = 0
    max_cnt = 0
    for g in glyf_glyphs.values():
        if hasattr(g, "coordinates") and g.coordinates is not None:
            max_pts = max(max_pts, len(g.coordinates))
        if hasattr(g, "endPtsOfContours") and g.endPtsOfContours is not None:
            max_cnt = max(max_cnt, len(g.endPtsOfContours))
    maxp.maxPoints = max_pts
    maxp.maxContours = max_cnt
    maxp.maxCompositePoints = 0
    maxp.maxCompositeContours = 0
    maxp.maxZones = 2
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = 0
    maxp.maxComponentDepth = 0
    new["maxp"] = maxp

    new["post"].formatType = 3.0
    new["head"].indexToLocFormat = 0
    new["head"].glyphDataFormat = 0

    new.save(dst)
    print(f"  {src}  ->  {dst}")

if __name__ == "__main__":
    for src, dst in PAIRS:
        if os.path.exists(src):
            otf_to_ttf(src, dst)
    print("Conversion lista.")
