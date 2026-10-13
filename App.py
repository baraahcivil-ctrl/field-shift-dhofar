"""
Field Shift - ظفار / Dhofar  |  عربي + English
الخطوة 1: بيانات المناخ من NASA POWER + جدول المحاصيل الحقيقية في ظفار
Step 1: NASA POWER climate data + Dhofar real crop table
تشغيل محلي (اختياري) / Local run (optional):  streamlit run app.py
"""
import calendar

import numpy as np
import pandas as pd
import requests
import streamlit as st

START_YEAR = 2005
END_YEAR = 2025

# ---------------------------------------------------------------
# مواقع في ظفار (خط العرض، خط الطول) / Dhofar sites (lat, lon)
# ---------------------------------------------------------------
SITES = {
    "salalah": (17.02, 54.09),
    "thumrait": (17.67, 54.03),
    "taqah": (17.04, 54.40),
    "mirbat": (16.99, 54.69),
}
SITE_NAMES = {
    "ar": {
        "salalah": "صلالة (السهل الساحلي والزراعي)",
        "thumrait": "ثمريت (منطقة النجد الزراعية)",
        "taqah": "طاقة",
        "mirbat": "مرباط",
        "custom": "إحداثيات أخرى",
    },
    "en": {
        "salalah": "Salalah (Coastal & Agricultural Plain)",
        "thumrait": "Thumrait (Najd Agricultural Plateau)",
        "taqah": "Taqah",
        "mirbat": "Mirbat",
        "custom": "Other coordinates",
    },
}


def bi(ar, en=None):
    """نص ثنائي اللغة. إن لم يُعطَ الإنجليزي يُستخدم نفس النص (للأرقام)."""
    return {"ar": ar, "en": ar if en is None else en}


# ---------------------------------------------------------------
# جدول المحاصيل الحقيقية في ظفار (السهل والنجد)
# Real crops grown in Dhofar (Coastal plain & Najd)
# ---------------------------------------------------------------
TROPICAL = bi("فاكهة استوائية / أشجار", "Tropical fruit / Trees")
GRASSES = bi("النجيلية (حبوب وأعلاف)", "Grasses (Cereals & Forage)")
LEGUMES = bi("البقولية", "Legumes (Fabaceae)")
ROOTS = bi("درنات وجذريات", "Root & Tuber crops")
PERENNIAL = bi("معمّر (مستديم)", "Perennial")
NO = bi("لا", "No")
YES = bi("نعم", "Yes")
LOW_ADDS = bi("منخفض (يضيف للتربة)", "Low (adds to soil)")
HIGH = bi("عالٍ", "High")
MEDIUM = bi("متوسط", "Medium")
LOW_MED = bi("منخفض إلى متوسط", "Low to medium")

CROPS = [
    {
        "name": bi("نارجيل (جوز الهند)", "Coconut"),
        "family": TROPICAL,
        "season": PERENNIAL,
        "water": bi("1200-1600 سنوياً", "1200-1600 per year"),
        "root": bi("1.5-2.5"),
        "fix": NO,
        "n_use": MEDIUM,
        "salt": HIGH,
        "ref": bi("مراجع محلية / استوائية", "Local / Tropical references"),
    },
    {
        "name": bi("موز", "Banana"),
        "family": TROPICAL,
        "season": PERENNIAL,
        "water": bi("1400-2000 سنوياً", "1400-2000 per year"),
        "root": bi("0.6-1.0"),
        "fix": NO,
        "n_use": HIGH,
        "salt": bi("منخفض", "Low"),
        "ref": bi("FAO-56", "FAO-56"),
    },
    {
        "name": bi("باباي (فافاي)", "Papaya"),
        "family": TROPICAL,
        "season": bi("300-360 (موسمي طويل)"),
        "water": bi("900-1200 سنوياً", "900-1200 per year"),
        "root": bi("0.9-1.5"),
        "fix": NO,
        "n_use": HIGH,
        "salt": bi("منخفض", "Low"),
        "ref": bi("مراجع استوائية", "Tropical references"),
    },
    {
        "name": bi("قمح (مشاريع النجد)", "Wheat (Najd farms)"),
        "family": GRASSES,
        "season": bi("120-150"),
        "water": bi("450-650"),
        "root": bi("1.0-1.5"),
        "fix": NO,
        "n_use": HIGH,
        "salt": MEDIUM,
        "ref": bi("FAO-33, FAO-56", "FAO-33, FAO-56"),
    },
    {
        "name": bi("بطاطس (مشاريع النجد)", "Potato (Najd farms)"),
        "family": bi("الباذنجانية", "Nightshades (Solanaceae)"),
        "season": bi("90-120"),
        "water": bi("500-700"),
        "root": bi("0.4-0.8"),
        "fix": NO,
        "n_use": HIGH,
        "salt": bi("منخفض", "Low"),
        "ref": bi("FAO-33, FAO-56", "FAO-33, FAO-56"),
    },
    {
        "name": bi("حشيشة رودس", "Rhodes grass"),
        "family": GRASSES,
        "season": PERENNIAL,
        "water": bi("900-1500 سنوياً", "900-1500 per year"),
        "root": bi("0.5-1.5"),
