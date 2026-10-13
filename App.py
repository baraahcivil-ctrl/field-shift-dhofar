"""
Field Shift - ظفار / Dhofar  |  عربي + English
الخطوة 1: بيانات المناخ من NASA POWER + جدول المحاصيل
Step 1: NASA POWER climate data + crop table
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
# شبكة NASA POWER دقتها تقريباً 0.5 درجة، فالمواقع القريبة تتشابه.
# ---------------------------------------------------------------
SITES = {
    "salalah": (17.02, 54.09),
    "thumrait": (17.67, 54.03),
    "taqah": (17.04, 54.40),
    "mirbat": (16.99, 54.69),
}
SITE_NAMES = {
    "ar": {
        "salalah": "صلالة (السهل الساحلي)",
        "thumrait": "ثمريت (الهضبة)",
        "taqah": "طاقة",
        "mirbat": "مرباط",
        "custom": "إحداثيات أخرى",
    },
    "en": {
        "salalah": "Salalah (coastal plain)",
        "thumrait": "Thumrait (plateau)",
        "taqah": "Taqah",
        "mirbat": "Mirbat",
        "custom": "Other coordinates",
    },
}


def bi(ar, en=None):
    """نص ثنائي اللغة. إن لم يُعطَ الإنجليزي يُستخدم نفس النص (للأرقام)."""
    return {"ar": ar, "en": ar if en is None else en}


# ---------------------------------------------------------------
# جدول المحاصيل - قيم تقريبية من مراجع الفاو، ويجب مراجعتها قبل العرض
# Crop table - approximate values from FAO references; verify before use
# FAO-56 = Allen et al. 1998 | FAO-33 = Doorenbos & Kassam 1979 | FAO-29 = Ayers & Westcot 1985
# ---------------------------------------------------------------
# المحاصيل المحلية في سهل صلالة (مصادر: Oman Observer، Britannica، وزارة الزراعة)
FAM = {
    "poaceae": bi("النجيلية", "Grasses (Poaceae)"),
    "fabaceae": bi("البقولية", "Legumes (Fabaceae)"),
    "solanaceae": bi("الباذنجانية", "Nightshades (Solanaceae)"),
    "cucurbitaceae": bi("القرعيات", "Cucurbits (Cucurbitaceae)"),
    "asteraceae": bi("المركّبة", "Daisy family (Asteraceae)"),
    "convolvulaceae": bi("العليقيات", "Morning-glory family (Convolvulaceae)"),
}
YES = bi("نعم", "Yes")
NO = bi("لا", "No")
REF = bi("FAO-56, FAO-29 (قيم تقريبية)", "FAO-56, FAO-29 (approximate values)")
CROPS = [
    {"id": "sorghum",     "name": bi("ذرة رفيعة", "Sorghum")},
    {"id": "maize",       "name": bi("ذرة شامية", "Maize (corn)")},
    {"id": "cowpea",      "name": bi("لوبيا (من البقوليات)", "Cowpea (a legume)")},
    {"id": "tomato",      "name": bi("طماطم", "Tomato")},
    {"id": "pepper",      "name": bi("فلفل", "Pepper")},
    {"id": "eggplant",    "name": bi("باذنجان", "Eggplant")},
    {"id": "cucumber",    "name": bi("خيار", "Cucumber")},
    {"id": "zucchini",    "name": bi("كوسا", "Zucchini")},
    {"id": "lettuce",     "name": bi("خس", "Lettuce")},
    {"id": "sweetpotato", "name": bi("بطاطا حلوة", "Sweet potato")},
    {"id": "alfalfa",     "name": bi("برسيم حجازي (جت)", "Alfalfa (lucerne)")},
    {"id": "rhodes",      "name": bi("حشيشة رودس", "Rhodes grass")},
]

# ---------------------------------------------------------------
# نصوص الواجهة / UI strings
# ---------------------------------------------------------------
STR = {
    "ar": {
        "place": "ظفار",
        "marquee": [
            "بيانات مناخية حقيقية من NASA POWER",
            "ظفار: صلالة · ثمريت · طاقة · مرباط",
            "أرقام المحاصيل تقريبية من مراجع الفاو",
            "نموذج أولي لهاكاثون ناسا Space Apps",
        ],
        "hero_sub": "أداة دعم قرار تساعد مزارعي ظفار على استكشاف الدورات الزراعية التي تحمي التربة وتوفّر المياه، اعتماداً على بيانات ناسا.",
        "tag_step": "الخطوة 1: المناخ والمحاصيل",
        "site_title": "اختر موقع الحقل",
        "site_intro": "حدّد المنطقة في ظفار لنسحب بياناتها المناخية من ناسا.",
        "site_label": "الموقع",
        "lat": "خط العرض",
        "lon": "خط الطول",
        "coords": "الإحداثيات",
        "spinner": "جاري سحب البيانات من NASA POWER...",
        "error": "تعذّر سحب البيانات من NASA POWER. تأكد من الاتصال بالإنترنت وأعد المحاولة.",
        "clim_title": "ملخص المناخ",
        "clim_intro": "متوسطات {s}–{e}. موسم الخريف في ظفار (الأشهر 6 إلى 9) هو معظم أمطار السنة.",
        "k_temp": "متوسط الحرارة",
        "k_rain": "الأمطار السنوية",
        "k_et0": "التبخر-نتح (تقدير)",
        "k_def": "العجز المائي",
        "u_c": "°م",
        "u_mm": "ملم",
        "cap_bar": "الأمطار مقابل التبخر-نتح حسب الشهر (ملم)",
        "s_rain": "الأمطار",
        "s_et0": "التبخر-نتح",
        "trend_title": "اتجاه المناخ",
        "trend_intro": "كيف تغيّر المناخ في هذا الموقع خلال السنوات الماضية.",
        "t_temp": "الحرارة",
        "t_rain": "الأمطار",
        "t_def": "العجز المائي",
        "u_c_dec": "°م لكل عقد",
        "u_mm_dec": "ملم لكل عقد",
        "cap_temp": "متوسط الحرارة السنوي (°م)",
        "cap_rain": "الأمطار السنوية (ملم)",
        "trend_note": "الأمطار في ظفار متذبذبة جداً من سنة لأخرى، فالاتجاه الخطي للاستئناس فقط وليس حكماً قطعياً.",
        "crops_title": "المحاصيل",
        "crops_intro": "محاصيل مزروعة في سهل صلالة وظفار حسب تقارير منشورة. الأرقام الزراعية تقريبية وتحتاج مراجعة.",
        "r_season": "مدة الموسم (يوم)",
        "r_kc": "معامل المحصول Kc (تقريبي)",
        "r_root": "عمق الجذور (م)",
        "r_fix": "يثبّت النيتروجين",
        "r_nuse": "استهلاك النيتروجين",
        "r_salt": "تحمّل الملوحة",
        "notes_title": "من أين جاءت الأرقام؟",
        "notes_intro": "الشفافية في المصادر جزء من قوة المشروع.",
        "notes": [
            ("المناخ", "من NASA POWER (مجاني ومفتوح)، بدقة شبكة تقريباً 0.5 درجة، فالمواقع المتقاربة تتشابه."),
            ("التبخر-نتح", "تقدير بمعادلة هارجريفز المعتمدة على الإشعاع الشمسي، وليس قياساً مباشراً."),
            ("المحاصيل", "القائمة مأخوذة من تقارير منشورة عن سهل صلالة. أرقام الموسم والجذور والملوحة تقريبية من مراجع الفاو (FAO-56, FAO-29) وتتغير حسب الصنف والإدارة."),
            ("الأعلاف", "تقارير صحفية عمانية تشير إلى توجه لنقل زراعة الأعلاف من سهل صلالة إلى النجد لتخفيف استنزاف المياه الجوفية والملوحة."),
            ("النموذج", "نموذج أولي جاهز للتحقق منه مع الخبراء الزراعيين المحليين."),
        ],
        "footer": "نموذج أولي لهاكاثون NASA Space Apps<br>البيانات المناخية: NASA POWER",
    },
    "en": {
        "place": "Dhofar",
        "marquee": [
            "Real climate data from NASA POWER",
            "Dhofar: Salalah · Thumrait · Taqah · Mirbat",
            "Crop figures are approximate, from FAO references",
            "Prototype for the NASA Space Apps hackathon",
        ],
        "hero_sub": "A decision-support tool that helps Dhofar farmers explore crop rotations that protect soil and save water, using NASA data.",
        "tag_step": "Step 1: Climate & crops",
        "site_title": "Choose your field location",
        "site_intro": "Pick an area in Dhofar and we'll pull its climate data from NASA.",
        "site_label": "Location",
        "lat": "Latitude",
        "lon": "Longitude",
        "coords": "Coordinates",
        "spinner": "Fetching data from NASA POWER...",
        "error": "Could not fetch data from NASA POWER. Check your connection and try again.",
        "clim_title": "Climate summary",
        "clim_intro": "Averages for {s}–{e}. Dhofar's khareef (monsoon) season, months 6 to 9, brings most of the year's rain.",
        "k_temp": "Mean temperature",
        "k_rain": "Annual rainfall",
        "k_et0": "Evapotranspiration (est.)",
        "k_def": "Water deficit",
        "u_c": "°C",
        "u_mm": "mm",
        "cap_bar": "Rainfall vs evapotranspiration by month (mm)",
        "s_rain": "Rainfall",
        "s_et0": "Evapotranspiration",
        "trend_title": "Climate trend",
        "trend_intro": "How the climate at this location has changed over the past years.",
        "t_temp": "Temperature",
        "t_rain": "Rainfall",
        "t_def": "Water deficit",
        "u_c_dec": "°C per decade",
        "u_mm_dec": "mm per decade",
        "cap_temp": "Annual mean temperature (°C)",
        "cap_rain": "Annual rainfall (mm)",
        "trend_note": "Rainfall in Dhofar varies a lot from year to year, so the linear trend is only indicative, not a firm conclusion.",
        "crops_title": "Crops",
        "crops_intro": "Crops grown on the Salalah Plain and in Dhofar, based on published reports. The agronomic figures are approximate and need verification.",
        "r_season": "Season (days)",
        "r_kc": "Crop coefficient Kc (approx.)",
        "r_root": "Root depth (m)",
        "r_fix": "Fixes nitrogen",
        "r_nuse": "Nitrogen demand",
        "r_salt": "Salinity tolerance",
        "notes_title": "Where do the numbers come from?",
        "notes_intro": "Being open about sources is part of what makes this project credible.",
        "notes": [
            ("Climate", "From NASA POWER (free and open), on a grid of roughly 0.5°, so nearby locations look alike."),
            ("Evapotranspiration", "An estimate from the radiation-based Hargreaves equation, not a direct measurement."),
            ("Crops", "The list comes from published reports on the Salalah Plain. Season, root and salinity figures are approximate, from FAO references (FAO-56, FAO-29), and vary with variety and management."),
            ("Fodder", "Omani press reports mention a policy to move fodder farming from the Salalah Plain to Al Najd, to ease groundwater depletion and salinity."),
            ("The model", "A prototype, ready to be verified with local agricultural experts."),
        ],
        "footer": "Prototype for the NASA Space Apps hackathon<br>Climate data: NASA POWER",
    },
}

# ---------------------------------------------------------------
# معاملات المحاصيل لمحرك التوصية (تقريبية - راجعها قبل العرض)
# Crop parameters for the recommendation engine (approximate - verify)
# days: مدة الموسم (المعمّرات 360 = سنة كاملة) | kc: معامل المحصول المتوسط (FAO-56، تقريبي)
# root: عمق الجذور المتوسط (م) | salt: تحمّل الملوحة 1 منخفض ... 3 عالٍ
# fix: يثبّت النيتروجين | n: احتياج النيتروجين 0 يضيف، 1 متوسط، 2 عالٍ
# ---------------------------------------------------------------
CROP_IDS = [c["id"] for c in CROPS]
CROP_PARAMS = {
    "sorghum":     dict(days=120, kc=0.85, root=1.5,  salt=3.0, fix=False, n=1, fam="poaceae"),
    "maize":       dict(days=120, kc=0.90, root=1.35, salt=1.5, fix=False, n=2, fam="poaceae"),
    "cowpea":      dict(days=90,  kc=0.75, root=0.8,  salt=2.0, fix=True,  n=0, fam="fabaceae"),
    "tomato":      dict(days=150, kc=0.85, root=1.1,  salt=1.5, fix=False, n=2, fam="solanaceae"),
    "pepper":      dict(days=135, kc=0.85, root=0.75, salt=1.5, fix=False, n=2, fam="solanaceae"),
    "eggplant":    dict(days=130, kc=0.85, root=0.95, salt=1.5, fix=False, n=2, fam="solanaceae"),
    "cucumber":    dict(days=100, kc=0.75, root=0.95, salt=1.5, fix=False, n=1, fam="cucurbitaceae"),
    "zucchini":    dict(days=95,  kc=0.80, root=0.85, salt=2.0, fix=False, n=1, fam="cucurbitaceae"),
    "lettuce":     dict(days=75,  kc=0.85, root=0.4,  salt=1.5, fix=False, n=1, fam="asteraceae"),
    "sweetpotato": dict(days=140, kc=0.90, root=1.2,  salt=1.5, fix=False, n=1, fam="convolvulaceae"),
    "alfalfa":     dict(days=360, kc=0.95, root=1.5,  salt=1.5, fix=True,  n=0, fam="fabaceae"),
    "rhodes":      dict(days=360, kc=0.90, root=1.0,  salt=2.5, fix=False, n=2, fam="poaceae"),
}
CROP_NAME = {c["id"]: c["name"] for c in CROPS}

MONTHS = {
    "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
           "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}

STR2 = {
    "ar": {
        "rec_title": "أي دورة زراعية أنسب لحقلك؟",
        "rec_intro": "اختر المحصول السابق وشهر الزراعة وأولوياتك، وسنرتّب لك المحاصيل التالية الأنسب مع السبب.",
        "in_prev": "المحصول الذي زرعته الموسم الماضي",
        "in_month": "شهر الزراعة القادم",
        "in_sal": "ملوحة الماء أو التربة",
        "in_scn": "سيناريو المناخ",
        "scn_now": "المناخ الحالي",
        "scn_stress": "أحرّ وأجفّ (اختبار إجهاد)",
        "sal_low": "منخفضة (ماء وتربة عذبة)",
        "sal_med": "متوسطة",
        "sal_high": "عالية (قرب الساحل أو آبار مالحة)",
        "pri_title": "ما الأهم لك؟ (0 غير مهم، 10 مهم جداً)",
        "p_water": "توفير المياه",
        "p_soil": "صحة التربة",
        "p_salt": "تحمّل الملوحة",
        "res_title": "أفضل 3 دورات زراعية لك",
        "res_intro": "بعد {prev}، هذه المحاصيل الأنسب لموقعك وأولوياتك:",
        "of100": "من 100",
        "b_water": "المياه",
        "b_soil": "التربة",
        "b_salt": "الملوحة",
        "sum_best": "ريّ الخيار الأول",
        "sum_prev": "ريّ المحصول السابق",
        "sum_diff": "التوفير المتوقع",
        "u_mm_season": "ملم للموسم",
        "others": "باقي الخيارات",
        "stress_note": "في سيناريو الإجهاد: التبخر-نتح +10% والأمطار -15%. هذا اختبار توضيحي وليس توقعاً.",
        "disclaimer": "الدرجات أداة مساعدة مبنية على قواعد مبسطة ومعاملات الفاو التقريبية، وليست توقعاً للإنتاج. الدخل غير داخل في الحساب لعدم توفر أسعار محلية موثقة.",
        "why": {
            "ir": "يحتاج ريّاً بنحو {ir} ملم خلال الموسم (تبخر-نتح ناسا مطروحاً منه المطر الفعّال).",
            "ir_less": "ريّه أقل من {prev} بنحو {d} ملم.",
            "ir_more": "ريّه أكثر من {prev} بنحو {d} ملم.",
            "fam_diff": "من عائلة نباتية مختلفة عن {prev}، فيقل تراكم الآفات والأمراض.",
            "fam_same": "من نفس عائلة {prev}، فيزيد خطر تراكم الآفات والأمراض.",
            "fix": "يثبّت النيتروجين في التربة، وقد يقلل احتياج السماد.",
            "after_legume": "يستفيد من النيتروجين الذي تركه {prev}.",
            "double_n": "محصول نهم للنيتروجين بعد {prev} النهم أيضاً، فيرهق التربة.",
            "root": "جذوره بعمق مختلف عن {prev}، فيستفيد من طبقات تربة أخرى.",
            "salt_ok": "يتحمل مستوى الملوحة الذي اخترته.",
            "salt_bad": "حساس للملوحة عند المستوى الذي اخترته.",
        },
    },
    "en": {
        "rec_title": "Which rotation suits your field?",
        "rec_intro": "Choose your previous crop, planting month and priorities, and we'll rank the best next crops with the reasons.",
        "in_prev": "Crop you grew last season",
        "in_month": "Next planting month",
        "in_sal": "Water or soil salinity",
        "in_scn": "Climate scenario",
        "scn_now": "Current climate",
        "scn_stress": "Hotter and drier (stress test)",
        "sal_low": "Low (fresh water and soil)",
        "sal_med": "Medium",
        "sal_high": "High (near the coast or saline wells)",
        "pri_title": "What matters most to you? (0 = not important, 10 = very important)",
        "p_water": "Water saving",
        "p_soil": "Soil health",
        "p_salt": "Salinity tolerance",
        "res_title": "Your top 3 rotations",
        "res_intro": "After {prev}, these crops fit your location and priorities best:",
        "of100": "out of 100",
        "b_water": "Water",
        "b_soil": "Soil",
        "b_salt": "Salinity",
        "sum_best": "Irrigation, top pick",
        "sum_prev": "Irrigation, previous crop",
        "sum_diff": "Expected saving",
        "u_mm_season": "mm per season",
        "others": "Other options",
        "stress_note": "In the stress scenario: evapotranspiration +10% and rainfall -15%. This is an illustrative test, not a forecast.",
        "disclaimer": "Scores are a decision aid built on simplified rules and approximate FAO coefficients, not a yield forecast. Income is not included because no verified local prices are available.",
        "why": {
            "ir": "Needs roughly {ir} mm of irrigation over the season (NASA evapotranspiration minus effective rain).",
            "ir_less": "Needs about {d} mm less irrigation than {prev}.",
            "ir_more": "Needs about {d} mm more irrigation than {prev}.",
            "fam_diff": "Different plant family from {prev}, which reduces pest and disease buildup.",
            "fam_same": "Same plant family as {prev}, which raises pest and disease risk.",
            "fix": "Fixes nitrogen in the soil, which can reduce fertilizer needs.",
            "after_legume": "Benefits from the nitrogen left by {prev}.",
            "double_n": "A nitrogen-hungry crop after {prev}, also nitrogen-hungry, which drains the soil.",
            "root": "Roots at a different depth than {prev}, so it uses other soil layers.",
            "salt_ok": "Tolerates the salinity level you chose.",
            "salt_bad": "Sensitive to salinity at the level you chose.",
        },
    },
}
for _lg in STR:
    STR[_lg].update(STR2[_lg])


# ---------------------------------------------------------------
# بيانات NASA POWER
# ---------------------------------------------------------------
def parse_power(parameters: dict, units: dict = None) -> pd.DataFrame:
    """يحوّل استجابة NASA POWER الشهرية إلى جدول (سنة، شهر، متغيرات)."""
    rows = {}
    for var, series in parameters.items():
        for key, val in series.items():
            year, month = int(key[:4]), int(key[4:])
            if month == 13:  # الشهر 13 = المتوسط السنوي، نتجاهله
                continue
            rows.setdefault((year, month), {})[var] = val
    df = pd.DataFrame(
        [{"year": y, "month": m, **v} for (y, m), v in rows.items()]
    ).sort_values(["year", "month"])
    df = df.replace(-999, np.nan).reset_index(drop=True)

    days = df.apply(lambda r: calendar.monthrange(int(r.year), int(r.month))[1], axis=1)
    df["rain_mm"] = df["PRECTOTCORR"] * days
    # تقدير التبخر-نتح المرجعي (Hargreaves المعتمد على الإشعاع الشمسي)
    # وحدة الإشعاع تُقرأ من استجابة ناسا نفسها: kWh -> ميغاجول، أما MJ فتبقى كما هي
    rs_unit = ((units or {}).get("ALLSKY_SFC_SW_DWN") or "MJ/m^2/day").lower()
    rs_factor = 3.6 if "kw" in rs_unit else 1.0
    rs_mj = df["ALLSKY_SFC_SW_DWN"] * rs_factor
    et0_day = 0.0135 * (df["T2M"] + 17.8) * rs_mj / 2.45
    df["et0_mm"] = et0_day * days
    return df


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_power(lat: float, lon: float) -> pd.DataFrame:
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": START_YEAR,
        "end": END_YEAR,
        "format": "JSON",
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    js = r.json()
    units = {k: v.get("units", "") for k, v in js.get("parameters", {}).items()}
    return parse_power(js["properties"]["parameter"], units)


def annual_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("year")
    out = pd.DataFrame(
        {
            "temp_c": g["T2M"].mean(),
            "rain_mm": g["rain_mm"].sum(min_count=12),
            "et0_mm": g["et0_mm"].sum(min_count=12),
        }
    )
    out["deficit_mm"] = out["et0_mm"] - out["rain_mm"]
    return out.dropna()


def monthly_climatology(df: pd.DataFrame) -> pd.DataFrame:
    m = df.groupby("month")[["rain_mm", "et0_mm", "T2M"]].mean()
    m.index.name = "الشهر"
    return m


def decade_trend(series: pd.Series) -> float:
    """الميل بالوحدة لكل عقد (10 سنوات)."""
    s = series.dropna()
    if len(s) < 5:
        return float("nan")
    return float(np.polyfit(s.index.values, s.values, 1)[0] * 10)



# ---------------------------------------------------------------
# محرك التوصية / Recommendation engine
# ---------------------------------------------------------------
def peff_month(p: float) -> float:
    """المطر الفعّال الشهري (صيغة USDA-SCS المستخدمة في الفاو)."""
    return max(0.0, 0.6 * p - 10) if p <= 70 else 0.8 * p - 24


def season_water(clim: pd.DataFrame, params: dict, start_month: int, scenario: str = "now"):
    """احتياج الريّ = (Kc × التبخر-نتح من ناسا) - المطر الفعّال، على امتداد موسم المحصول."""
    et_f, rain_f = (1.10, 0.85) if scenario == "stress" else (1.0, 1.0)
    remaining, m = float(params["days"]), int(start_month)
    etc = peff = 0.0
    while remaining > 0:
        frac = min(1.0, remaining / 30.4)
        etc += params["kc"] * clim.loc[m, "et0_mm"] * et_f * frac
        peff += peff_month(clim.loc[m, "rain_mm"] * rain_f) * frac
        remaining -= 30.4
        m = m % 12 + 1
    return etc, peff, max(0.0, etc - peff)


def soil_score(prev_id: str, cid: str):
    """درجة التربة من قواعد التناوب. ترجع (الدرجة، قائمة الأسباب)."""
    prev, cur = CROP_PARAMS[prev_id], CROP_PARAMS[cid]
    score, why = 50.0, []
    if cur["fam"] == prev["fam"]:
        score -= 35
        why.append(("warn", "fam_same"))
    else:
        score += 10
        why.append(("good", "fam_diff"))
    if cur["fix"]:
        score += 20
        why.append(("good", "fix"))
    if prev["fix"] and cur["n"] == 2:
        score += 15
        why.append(("good", "after_legume"))
    if prev["n"] == 2 and cur["n"] == 2:
        score -= 15
        why.append(("warn", "double_n"))
    if abs(cur["root"] - prev["root"]) >= 0.4:
        score += 10
        why.append(("good", "root"))
    return max(0.0, min(100.0, score)), why


def salt_score(cid: str, level: float) -> float:
    tol = CROP_PARAMS[cid]["salt"]
    return 100.0 if tol >= level else max(0.0, 100.0 - (level - tol) * 50)


def recommend(clim, prev_id, start_month, sal_level, weights, scenario="now"):
    """يرتّب المحاصيل التالية. weights = (مياه، تربة، ملوحة)."""
    water = {cid: season_water(clim, p, start_month, scenario)[2] for cid, p in CROP_PARAMS.items()}
    prev_ir = water[prev_id]
    annual = [v for cid, v in water.items() if CROP_PARAMS[cid]["days"] < 360]
    lo, hi = min(annual), max(annual)
    w_sum = float(sum(weights)) or 3.0
    w = weights if sum(weights) else (1, 1, 1)
    out = []
    for cid in CROP_IDS:
        ir = water[cid]
        s_w = 100.0 if hi == lo else 100.0 * (1 - (ir - lo) / (hi - lo))
        s_w = max(0.0, min(100.0, s_w))
        s_s, soil_why = soil_score(prev_id, cid)
        s_t = salt_score(cid, sal_level)
        total = (w[0] * s_w + w[1] * s_s + w[2] * s_t) / w_sum
        why = [("good", "ir", {"ir": int(round(ir, -1))})]
        if cid != prev_id:
            d = prev_ir - ir
            if d >= 20:
                why.append(("good", "ir_less", {"d": int(round(d, -1))}))
            elif d <= -20:
                why.append(("warn", "ir_more", {"d": int(round(-d, -1))}))
        why += [(k, c, {}) for k, c in soil_why]
        why.append(("good", "salt_ok", {}) if s_t >= 100 else ("warn", "salt_bad", {}))
        out.append(
            {
                "id": cid,
                "score": int(round(total)),
                "water": int(round(s_w)),
                "soil": int(round(s_s)),
                "salt": int(round(s_t)),
                "ir": ir,
                "why": why,
            }
        )
    out.sort(key=lambda r: (r["score"], r["soil"]), reverse=True)
    return out, prev_ir


# ---------------------------------------------------------------
# الواجهة / UI - بنمط Arva
# ---------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Cormorant+Garamond:wght@300;500;600&family=Amiri:wght@400;700&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');
:root{
  --forest:#07503f; --lime:#e8fe85; --bone:#f1efdf; --white:#ffffff; --ash:#efefef;
  --charcoal:#212529; --graphite:#353535; --pewter:#6d6d6d;
  --sky:#b2cee7; --peach:#fceace; --sage:#e6ecd5; --moss:#c3cda7;
}
html, body, .stApp, [data-testid="stAppViewContainer"]{
  background:var(--bone) !important; color:var(--charcoal);
  font-family:'Inter','IBM Plex Sans Arabic',sans-serif; color-scheme:light;
}
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer{display:none !important;}
.block-container{max-width:1200px !important; padding:16px 20px 60px !important;}
[data-testid="stMain"], .block-container{direction:__DIR__;}
.serif{font-family:'Cormorant Garamond','Amiri',serif; letter-spacing:-0.012em; font-variant-numeric:lining-nums;}

/* شريط ليموني متحرك */
.marquee{background:var(--lime); border-radius:100px; overflow:hidden; padding:9px 0; direction:ltr;}
.marquee-track{display:inline-flex; white-space:nowrap; animation:scrollx 40s linear infinite;}
.marquee-item{display:inline-flex; align-items:center; gap:12px; padding:0 20px; font-size:13px; color:var(--charcoal); letter-spacing:.025em;}
.chk{width:16px; height:16px; border:1.5px solid var(--charcoal); border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:9px; line-height:1;}
@keyframes scrollx{from{transform:translateX(0)} to{transform:translateX(-50%)}}

/* البانر الرئيسي */
.hero{background:var(--forest); color:#fff; border-radius:30px; padding:56px 30px; margin:16px 0 0; text-align:center;}
.hero-kicker{font-size:13px; letter-spacing:.12em; opacity:.8; margin-bottom:14px; direction:ltr;}
.hero-title{font-family:'Cormorant Garamond','Amiri',serif; font-weight:300; font-size:clamp(38px,8vw,64px); line-height:1.1; letter-spacing:-0.012em; color:#fff; margin-bottom:16px;}
.hero-sub{max-width:60ch; margin:0 auto 26px; font-size:17px; line-height:1.7; color:#fff; opacity:.92;}
.pill-tag{display:inline-block; border:1px solid rgba(255,255,255,.75); color:#fff; border-radius:100px; padding:8px 20px; font-size:14px; margin:4px;}
.pill-tag.solid{background:#fff; color:var(--forest); border-color:#fff; font-weight:500;}

/* عناوين الأقسام */
.sec{margin:50px 0 24px;}
.sec-title{font-family:'Cormorant Garamond','Amiri',serif; font-weight:500; font-size:clamp(30px,5vw,45px); line-height:1.15; letter-spacing:-0.012em; color:var(--charcoal);}
.sec-intro{font-size:17px; line-height:1.7; max-width:60ch; color:var(--graphite); margin-top:10px;}
.small-note{font-size:14px; color:var(--pewter); margin-top:10px; line-height:1.6;}
.chart-cap{font-family:'Cormorant Garamond','Amiri',serif; font-size:24px; font-weight:500; color:var(--charcoal); margin:24px 0 6px;}

/* بطاقات الباستيل */
.grid{display:grid; gap:24px; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));}
.grid-wide{display:grid; gap:24px; grid-template-columns:repeat(auto-fit,minmax(290px,1fr));}
.card{border-radius:20px; padding:30px;}
.sky{background:var(--sky)} .peach{background:var(--peach)} .sage{background:var(--sage)} .ash{background:var(--ash)}
.kpi-label{font-size:14px; letter-spacing:.025em; color:var(--graphite);}
.kpi-value{font-family:'Cormorant Garamond','Amiri',serif; font-weight:500; font-size:clamp(36px,6vw,50px); line-height:1.1; margin-top:8px; color:var(--charcoal); font-variant-numeric:lining-nums;}
.kpi-unit{font-size:14px; color:var(--graphite); margin-top:2px;}

/* بطاقات المحاصيل */
.crop-name{font-family:'Cormorant Garamond','Amiri',serif; font-weight:600; font-size:30px; line-height:1.15; color:var(--charcoal);}
.tag{display:inline-block; background:#fff; border-radius:100px; padding:4px 14px; font-size:13px; margin:10px 0 14px;}
.row{display:flex; justify-content:space-between; gap:14px; padding:9px 0; border-top:1px solid rgba(7,80,63,.18); font-size:14px; line-height:1.5;}
.row span:first-child{color:var(--graphite);}
.row span:last-child{font-weight:500; text-align:end;}
.ref{margin-top:12px; font-size:12px; color:var(--pewter); unicode-bidi:plaintext;}

/* قسم أخضر داكن */
.forest{background:var(--forest); color:#fff; border-radius:30px; padding:50px 30px; margin:50px 0 24px;}
.forest .sec-title{color:#fff;}
.forest .sec-intro{color:#fff; opacity:.9;}
.benefits{display:grid; gap:30px; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); margin-top:30px;}
.benefit{display:flex; gap:16px; align-items:flex-start;}
.ico{flex:0 0 40px; width:40px; height:40px; border-radius:50%; border:1px solid rgba(255,255,255,.55); background:rgba(255,255,255,.12); display:flex; align-items:center; justify-content:center; font-size:15px;}
.benefit-title{font-weight:600; font-size:15px; margin-bottom:4px;}
.benefit-body{font-size:14px; line-height:1.7; opacity:.92;}
.footer{background:var(--forest); color:#fff; border-radius:30px; padding:30px; margin-top:24px; text-align:center; font-size:14px; line-height:1.8;}
.footer .brand{font-family:'Cormorant Garamond','Amiri',serif; font-size:28px; font-weight:500;}

/* عناصر الإدخال */
[data-testid="stWidgetLabel"] p{font-weight:500; font-size:14px; color:var(--charcoal);}
[data-baseweb="select"] > div, [data-baseweb="input"]{
  background:#fff !important; border:1px solid var(--moss) !important; border-radius:33px !important; min-height:48px;
}
[data-baseweb="base-input"]{background:transparent !important; border:none !important;}
[data-baseweb="select"] *, [data-baseweb="input"] input{color:var(--charcoal) !important;}
[data-testid="stSelectbox"] [data-baseweb="select"] div, [data-testid="stNumberInput"] div{background-color:#fff !important; color:#212529 !important;}
[data-testid="stSelectbox"] svg, [data-testid="stNumberInput"] svg{fill:#212529 !important;}
[data-baseweb="popover"] *, [data-baseweb="menu"] *{background-color:#fff !important; color:#212529 !important;}
[data-baseweb="menu"] li:hover, [data-baseweb="menu"] li:hover *{background-color:var(--sage) !important;}
[data-testid="stAlert"]{border-radius:20px;}
/* مبدّل اللغة */
[data-testid="stRadio"] [role="radiogroup"]{gap:8px;}
[data-testid="stRadio"] label{background:#fff; border:1px solid var(--moss); border-radius:100px; padding:6px 20px !important; margin:0 !important;}
[data-testid="stRadio"] label > div:first-child{display:none;}
[data-testid="stRadio"] label:has(input:checked){background:var(--forest); border-color:var(--forest);}
[data-testid="stRadio"] label:has(input:checked) *{color:#fff !important;}
[data-testid="stRadio"] label *{font-size:14px;}
/* بطاقات التوصية */
.rank{display:inline-block; background:var(--forest); color:#fff; border-radius:100px; padding:4px 14px; font-size:13px; margin-bottom:10px;}
.score{font-family:'Cormorant Garamond','Amiri',serif; font-weight:500; font-size:clamp(44px,8vw,60px); line-height:1; margin:4px 0 14px; font-variant-numeric:lining-nums;}
.score small{font-family:'Inter','IBM Plex Sans Arabic',sans-serif; font-size:14px; color:var(--graphite); font-weight:400;}
.bars{margin:6px 0 16px;}
.bar{display:flex; align-items:center; gap:10px; font-size:13px; margin:7px 0;}
.bar-l{flex:0 0 62px; color:var(--graphite);}
.bar-track{flex:1; height:8px; background:#fff; border-radius:100px; overflow:hidden;}
.bar-fill{height:100%; background:var(--forest); border-radius:100px;}
.bar-v{flex:0 0 30px; text-align:end; font-weight:500;}
.why{display:flex; gap:10px; align-items:flex-start; font-size:14px; line-height:1.6; padding:7px 0; border-top:1px solid rgba(7,80,63,.18);}
.mk{flex:0 0 18px; width:18px; height:18px; border:1.5px solid var(--forest); border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:10px; line-height:1; margin-top:3px; color:var(--forest);}
.why.warn .mk{border-color:var(--charcoal); color:var(--charcoal);}
.others{font-size:14px; color:var(--graphite); margin-top:20px; line-height:1.9;}
.others b{color:var(--charcoal); font-weight:600;}
</style>
"""

TONES = ["sky", "peach", "sage", "ash"]


def fmt(x, nd=0, sign=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def marquee_html(S) -> str:
    one = "".join(
        f'<span class="marquee-item"><span class="chk">✓</span>{t}</span>'
        for t in S["marquee"]
    )
    return f'<div class="marquee"><div class="marquee-track">{one}{one}</div></div>'


def hero_html(S) -> str:
    return (
        '<div class="hero">'
        '<div class="hero-kicker">NASA SPACE APPS · FIELD SHIFT</div>'
        f'<div class="hero-title">Field Shift · {S["place"]}</div>'
        f'<div class="hero-sub">{S["hero_sub"]}</div>'
        '<span class="pill-tag solid">NASA POWER</span>'
        f'<span class="pill-tag">{START_YEAR}–{END_YEAR}</span>'
        f'<span class="pill-tag">{S["tag_step"]}</span>'
        "</div>"
    )


def section_html(title: str, intro: str = "") -> str:
    intro_html = f'<div class="sec-intro">{intro}</div>' if intro else ""
    return f'<div class="sec"><div class="sec-title">{title}</div>{intro_html}</div>'


def kpi_card(label: str, value: str, unit: str, tone: str) -> str:
    return (
        f'<div class="card {tone}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-unit">{unit}</div></div>'
    )


SALT_LABEL = {
    1.0: bi("منخفض", "Low"),
    1.5: bi("منخفض إلى متوسط", "Low to medium"),
    2.0: bi("متوسط", "Medium"),
    2.5: bi("متوسط إلى عالٍ", "Medium to high"),
    3.0: bi("عالٍ", "High"),
}
N_LABEL = {
    0: bi("منخفض (يضيف للتربة)", "Low (adds to soil)"),
    1: bi("متوسط", "Medium"),
    2: bi("عالٍ", "High"),
}
PERENNIAL = bi("معمّر (قصّات متعددة)", "Perennial (multiple cuts)")


def crop_cards_html(lang, S) -> str:
    cards = []
    for i, c in enumerate(CROPS):
        p = CROP_PARAMS[c["id"]]
        vals = [
            (S["r_season"], PERENNIAL[lang] if p["days"] >= 360 else str(p["days"])),
            (S["r_kc"], f'{p["kc"]:.2f}'),
            (S["r_root"], f'{p["root"]:.1f}'),
            (S["r_fix"], (YES if p["fix"] else NO)[lang]),
            (S["r_nuse"], N_LABEL[p["n"]][lang]),
            (S["r_salt"], SALT_LABEL[p["salt"]][lang]),
        ]
        rows = "".join(
            f'<div class="row"><span>{label}</span><span>{val}</span></div>' for label, val in vals
        )
        cards.append(
            f'<div class="card {TONES[i % 4]}">'
            f'<div class="crop-name">{c["name"][lang]}</div>'
            f'<span class="tag">{FAM[p["fam"]][lang]}</span>{rows}'
            f'<div class="ref">{REF[lang]}</div></div>'
        )
    return f'<div class="grid-wide">{"".join(cards)}</div>'


def notes_html(S) -> str:
    blocks = "".join(
        f'<div class="benefit"><div class="ico">{i}</div><div>'
        f'<div class="benefit-title">{t}</div><div class="benefit-body">{b}</div></div></div>'
        for i, (t, b) in enumerate(S["notes"], 1)
    )
    return (
        '<div class="forest">'
        f'<div class="sec-title">{S["notes_title"]}</div>'
        f'<div class="sec-intro">{S["notes_intro"]}</div>'
        f'<div class="benefits">{blocks}</div></div>'
    )


def footer_html(S) -> str:
    return (
        f'<div class="footer"><div class="brand">Field Shift · {S["place"]}</div>'
        f'{S["footer"]}</div>'
    )


def rec_cards_html(results, lang, S, prev_id) -> str:
    prev_name = CROP_NAME[prev_id][lang]
    tones = ["sage", "sky", "peach"]
    cards = []
    for i, r in enumerate(results):
        bars = "".join(
            f'<div class="bar"><span class="bar-l">{S[k]}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{r[v]}%"></div></div>'
            f'<span class="bar-v">{r[v]}</span></div>'
            for k, v in [("b_water", "water"), ("b_soil", "soil"), ("b_salt", "salt")]
        )
        whys = "".join(
            f'<div class="why {kind}"><span class="mk">{"✓" if kind == "good" else "!"}</span>'
            f'<span>{S["why"][code].format(prev=prev_name, **params)}</span></div>'
            for kind, code, params in r["why"]
        )
        cards.append(
            f'<div class="card {tones[i % 3]}">'
            f'<span class="rank">#{i + 1}</span>'
            f'<div class="crop-name">{CROP_NAME[r["id"]][lang]}</div>'
            f'<div class="score">{r["score"]} <small>{S["of100"]}</small></div>'
            f'<div class="bars">{bars}</div>{whys}</div>'
        )
    return f'<div class="grid-wide">{"".join(cards)}</div>'


def main():
    st.set_page_config(page_title="Field Shift · ظفار / Dhofar", page_icon="🌾", layout="wide")

    # مبدّل اللغة / language switch
    pick = st.radio(
        "Language / اللغة",
        ["العربية", "English"],
        horizontal=True,
        label_visibility="collapsed",
        key="lang",
    )
    lang = "ar" if pick == "العربية" else "en"
    S = STR[lang]

    st.markdown(CSS.replace("__DIR__", "rtl" if lang == "ar" else "ltr"), unsafe_allow_html=True)
    st.markdown(marquee_html(S), unsafe_allow_html=True)
    st.markdown(hero_html(S), unsafe_allow_html=True)

    # 1) الموقع / location
    st.markdown(section_html(S["site_title"], S["site_intro"]), unsafe_allow_html=True)
    site = st.selectbox(
        S["site_label"],
        list(SITES.keys()) + ["custom"],
        format_func=lambda k: SITE_NAMES[lang][k],
        key="site",
    )
    if site == "custom":
        c1, c2 = st.columns(2)
        lat = c1.number_input(S["lat"], value=17.02, format="%.3f", key="lat")
        lon = c2.number_input(S["lon"], value=54.09, format="%.3f", key="lon")
    else:
        lat, lon = SITES[site]
        st.markdown(
            f'<div class="small-note">{S["coords"]}: {lat}, {lon}</div>', unsafe_allow_html=True
        )

    with st.spinner(S["spinner"]):
        try:
            df = fetch_power(lat, lon)
        except Exception as e:
            st.error(S["error"])
            st.code(str(e))
            st.stop()

    ann = annual_summary(df)
    clim = monthly_climatology(df)

    # 2) التوصية / recommendation (قلب المشروع)
    st.markdown(section_html(S["rec_title"], S["rec_intro"]), unsafe_allow_html=True)
    a1, a2 = st.columns(2)
    prev_id = a1.selectbox(
        S["in_prev"], CROP_IDS, format_func=lambda k: CROP_NAME[k][lang], key="prev"
    )
    month = a2.selectbox(
        S["in_month"], list(range(1, 13)), index=9,
        format_func=lambda m: MONTHS[lang][m - 1], key="month",
    )
    b1, b2 = st.columns(2)
    sal_key = b1.selectbox(
        S["in_sal"], ["low", "med", "high"], index=1,
        format_func=lambda k: S["sal_" + k], key="sal",
    )
    scenario = b2.radio(
        S["in_scn"], ["now", "stress"], horizontal=True,
        format_func=lambda k: S["scn_" + k], key="scn",
    )
    st.markdown(f'<div class="small-note">{S["pri_title"]}</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    w_water = p1.slider(S["p_water"], 0, 10, 5, key="w_water")
    w_soil = p2.slider(S["p_soil"], 0, 10, 5, key="w_soil")
    w_salt = p3.slider(S["p_salt"], 0, 10, 5, key="w_salt")

    results, prev_ir = recommend(
        clim, prev_id, month, {"low": 1.0, "med": 2.0, "high": 3.0}[sal_key],
        (w_water, w_soil, w_salt), scenario,
    )
    top = results[:3]
    st.markdown(
        section_html(S["res_title"], S["res_intro"].format(prev=CROP_NAME[prev_id][lang])),
        unsafe_allow_html=True,
    )
    st.markdown(rec_cards_html(top, lang, S, prev_id), unsafe_allow_html=True)

    saving = prev_ir - top[0]["ir"]
    sum_cards = "".join(
        [
            kpi_card(S["sum_best"], fmt(top[0]["ir"]), S["u_mm_season"], "sage"),
            kpi_card(S["sum_prev"], fmt(prev_ir), S["u_mm_season"], "ash"),
            kpi_card(S["sum_diff"], fmt(saving, 0, True), S["u_mm_season"], "peach"),
        ]
    )
    st.markdown(f'<div class="grid" style="margin-top:24px">{sum_cards}</div>', unsafe_allow_html=True)

    others = " · ".join(
        f'<b>{CROP_NAME[r["id"]][lang]}</b> {r["score"]}' for r in results[3:]
    )
    if others:
        st.markdown(
            f'<div class="others">{S["others"]}: {others}</div>', unsafe_allow_html=True
        )
    if scenario == "stress":
        st.markdown(f'<div class="small-note">{S["stress_note"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="small-note">{S["disclaimer"]}</div>', unsafe_allow_html=True)

    # 3) ملخص المناخ / climate summary
    st.markdown(
        section_html(S["clim_title"], S["clim_intro"].format(s=START_YEAR, e=END_YEAR)),
        unsafe_allow_html=True,
    )
    cards = "".join(
        [
            kpi_card(S["k_temp"], fmt(ann["temp_c"].mean(), 1), S["u_c"], "peach"),
            kpi_card(S["k_rain"], fmt(ann["rain_mm"].mean()), S["u_mm"], "sky"),
            kpi_card(S["k_et0"], fmt(ann["et0_mm"].mean()), S["u_mm"], "sage"),
            kpi_card(S["k_def"], fmt(ann["deficit_mm"].mean()), S["u_mm"], "ash"),
        ]
    )
    st.markdown(f'<div class="grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="chart-cap">{S["cap_bar"]}</div>', unsafe_allow_html=True)
    st.bar_chart(
        clim[["rain_mm", "et0_mm"]].rename(columns={"rain_mm": S["s_rain"], "et0_mm": S["s_et0"]}),
        color=["#07503f", "#6d6d6d"],
        height=320,
    )

    # 4) الاتجاه / trend
    st.markdown(section_html(S["trend_title"], S["trend_intro"]), unsafe_allow_html=True)
    trend_cards = "".join(
        [
            kpi_card(S["t_temp"], fmt(decade_trend(ann["temp_c"]), 2, True), S["u_c_dec"], "peach"),
            kpi_card(S["t_rain"], fmt(decade_trend(ann["rain_mm"]), 0, True), S["u_mm_dec"], "sky"),
            kpi_card(S["t_def"], fmt(decade_trend(ann["deficit_mm"]), 0, True), S["u_mm_dec"], "sage"),
        ]
    )
    st.markdown(f'<div class="grid">{trend_cards}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-cap">{S["cap_temp"]}</div>', unsafe_allow_html=True)
    st.line_chart(ann[["temp_c"]].rename(columns={"temp_c": S["t_temp"]}), color="#07503f", height=260)
    st.markdown(f'<div class="chart-cap">{S["cap_rain"]}</div>', unsafe_allow_html=True)
    st.line_chart(ann[["rain_mm"]].rename(columns={"rain_mm": S["t_rain"]}), color="#07503f", height=260)
    st.markdown(f'<div class="small-note">{S["trend_note"]}</div>', unsafe_allow_html=True)

    # 5) المحاصيل / crops
    st.markdown(section_html(S["crops_title"], S["crops_intro"]), unsafe_allow_html=True)
    st.markdown(crop_cards_html(lang, S), unsafe_allow_html=True)

    st.markdown(notes_html(S), unsafe_allow_html=True)
    st.markdown(footer_html(S), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
