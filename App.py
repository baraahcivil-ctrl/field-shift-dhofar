"""
Field Shift - ظفار / Dhofar  |  عربي + English
الخطوة 1: بيانات المناخ من NASA POWER + جدول المحاصيل
Step 1: NASA POWER climate data + crop table
تشغيل محلي (اختياري) / Local run (optional):  streamlit run app.py
"""
import calendar
import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st

START_YEAR = 2005
END_YEAR = datetime.date.today().year - 1  # آخر سنة كاملة / latest complete year

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
        "k_et0": "الماء الذي يسحبه الهواء (تقدير)",
        "k_def": "العجز المائي",
        "u_c": "°م",
        "u_mm": "ملم",
        "cap_bar": "الأمطار مقابل الماء الذي يسحبه الهواء حسب الشهر (ملم)",
        "s_rain": "الأمطار",
        "s_et0": "طلب التبخر",
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
        "r_kc": "معامل استهلاك الماء (تقريبي)",
        "r_root": "عمق الجذور (م)",
        "r_fix": "يثبّت النيتروجين",
        "r_nuse": "استهلاك النيتروجين",
        "r_salt": "تحمّل الملوحة",
        "notes_title": "من أين جاءت الأرقام؟",
        "notes_intro": "الشفافية في المصادر جزء من قوة المشروع.",
        "notes": [
            ("المناخ", "من NASA POWER (مجاني ومفتوح)، بدقة شبكة تقريباً 0.5 درجة، فالمواقع المتقاربة تتشابه."),
            ("التبخر", "تقدير بمعادلة هارجريفز المعتمدة على الإشعاع الشمسي، وليس قياساً مباشراً."),
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
        "k_et0": "Water the air takes (est.)",
        "k_def": "Water deficit",
        "u_c": "°C",
        "u_mm": "mm",
        "cap_bar": "Rainfall vs water the air takes, by month (mm)",
        "s_rain": "Rainfall",
        "s_et0": "Evaporation demand",
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
        "r_kc": "Water-use factor (approx.)",
        "r_root": "Root depth (m)",
        "r_fix": "Fixes nitrogen",
        "r_nuse": "Nitrogen demand",
        "r_salt": "Salinity tolerance",
        "notes_title": "Where do the numbers come from?",
        "notes_intro": "Being open about sources is part of what makes this project credible.",
        "notes": [
            ("Climate", "From NASA POWER (free and open), on a grid of roughly 0.5°, so nearby locations look alike."),
            ("Evaporation", "An estimate from the radiation-based Hargreaves equation, not a direct measurement."),
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
        "u_mm_season": "م³ للهكتار في الموسم",
        "others": "باقي الخيارات",
        "stress_note": "في سيناريو الإجهاد: التبخر-نتح +10% والأمطار -15%. هذا اختبار توضيحي وليس توقعاً.",
        "disclaimer": "الدرجات أداة مساعدة مبنية على قواعد مبسطة ومعاملات الفاو التقريبية، وليست توقعاً للإنتاج. الدخل غير داخل في الحساب لعدم توفر أسعار محلية موثقة.",
        "why": {
            "ir": "يحتاج ريّاً بنحو {ir} م³ للهكتار خلال الموسم (من بيانات ناسا المناخية مطروحاً منها المطر المفيد).",
            "ir_less": "ريّه أقل من {prev} بنحو {d} م³ للهكتار.",
            "ir_more": "ريّه أكثر من {prev} بنحو {d} م³ للهكتار.",
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
        "u_mm_season": "m³ per hectare per season",
        "others": "Other options",
        "stress_note": "In the stress scenario: evapotranspiration +10% and rainfall -15%. This is an illustrative test, not a forecast.",
        "disclaimer": "Scores are a decision aid built on simplified rules and approximate FAO coefficients, not a yield forecast. Income is not included because no verified local prices are available.",
        "why": {
            "ir": "Needs roughly {ir} m³ of irrigation per hectare over the season (NASA climate data minus usable rain).",
            "ir_less": "Needs about {d} m³ per hectare less irrigation than {prev}.",
            "ir_more": "Needs about {d} m³ per hectare more irrigation than {prev}.",
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



STR3 = {
    "ar": {
        "scn_future": "نظرة مستقبلية (2040)",
        "future_note": "نظرة 2040: الحرارة {dt} °م (امتداد اتجاه ناسا حتى 2040)، والأمطار بلا تغيير لأنها متذبذبة جداً، وملوحة المنطقة حسب توقعات الدراسة لعام 2040. تقدير وليس تنبؤاً.",
        "zone_label": "أين يقع حقلك في السهل؟",
        "z_coast": "الشريط الساحلي",
        "z_injection": "حزام آبار الحقن (1–2 كم من الساحل)",
        "z_central": "وسط السهل (منطقة المياه العذبة)",
        "z_mountain": "أطراف الجبل (سفوح جبل القرى)",
        "z_manual": "سأحدد الملوحة بنفسي",
        "zone_outside": "المناطق مأخوذة من دراسة عن سهل صلالة، فتنطبق على صلالة وطاقة فقط. لهذا الموقع حدّد الملوحة بنفسك.",
        "z_tds": "ملوحة المياه الجوفية المحسوبة بالنموذج: {now} ppm (2020) و{fut} ppm (2040).",
        "z_tds_nofut": "ملوحة المياه الجوفية المحسوبة بالنموذج: {now} ppm. لا توقعات لعام 2040 لهذه المنطقة في الدراسة.",
        "z_level": "مستوى الملوحة المستخدم في الحساب: {lvl}",
        "z_src": "المصدر: Al-Hadhrami وآخرون (2024)، قيم نموذجية لا قياسات. تحويلها إلى مستويات تقدير منا ويحتاج مراجعة خبير.",
        "lvl_1": "منخفضة", "lvl_2": "متوسطة", "lvl_3": "عالية", "lvl_4": "عالية جداً",
        "wt_shallow": "تحذير: المياه الجوفية قريبة من السطح هنا (0 م عند الساحل حسب الدراسة). قد تصعد الأملاح إلى الجذور وقد يحدث تشبّع بالماء، فتأكد من الصرف.",
        "wt_central": "المياه الجوفية أعمق في وسط السهل (حتى حوالي 9 م حسب الدراسة)، وهذا يقلل خطر صعود الأملاح عادةً.",
        "sal_warn4": "الملوحة هنا أعلى مما تتحمله أي من المحاصيل المدرجة، فكل الخيارات معرّضة للخطر. فكّر في مياه أقل ملوحة أو محاصيل شديدة التحمل.",
        "u_m3": "م³",
        "head_less": "أقل ماءً للهكتار مقارنة بـ{prev}",
        "head_more": "أكثر ماءً للهكتار مقارنة بـ{prev}",
        "head_same": "احتياج مياه مماثل تقريباً لـ{prev}",
        "head_detail": "{top}: {a} م³ للهكتار | {prev}: {b} م³ للهكتار",
        "how_title": "كيف تُحسب الدرجات؟",
        "how": [
            ("احتياج الريّ", "irrigation = max(0, water-use factor × evaporation − usable rain)", "طريقة الفاو القياسية على بيانات ناسا لأشهر موسم المحصول. التبخر مقدّر من الحرارة والإشعاع الشمسي (هارجريفز)."),
            ("درجة المياه", "100 × (1 − (irrigation − lowest) / (highest − lowest))", "تقارن المحاصيل ببعضها، فتتغير إذا تغيرت قائمة المحاصيل."),
            ("درجة التربة", "start 50 | new family +10 | same family −35 | fixes N +20 | N-hungry after legume +15 | two N-hungry −15 | roots differ ≥ 0.4 m +10", "افتراض: نقاط تقريبية من قواعد عملية، لم يتم التحقق منها."),
            ("درجة الملوحة", "100 if tolerance ≥ level, else 100 − 50 × (level − tolerance)", "افتراض: خطوة 50 نقطة قاعدة تقريبية، وتحمّل المحاصيل تقريبي."),
            ("الدرجة النهائية", "(w1×water + w2×soil + w3×salinity) / (w1 + w2 + w3)", "w1 وw2 وw3 هي أوزان المنزلقات الثلاثة التي تختارها."),
            ("ملوحة المناطق", "ppm: ≤700 low | ≤2,100 medium | ≤3,000 high | above very high", "قيم المناطق نتائج نموذج من دراسة Al-Hadhrami وآخرون (2024). تحويلها إلى مستويات تقدير منا ويحتاج مراجعة خبير."),
            ("النظرة المستقبلية", "evaporation × (T + warming + 17.8) / (T + 17.8)", "الاحترار = اتجاه حرارة ناسا لكل عقد × السنوات حتى 2040. لا نتوقع الأمطار لأنها تتذبذب كثيراً بين السنوات."),
        ],
    },
    "en": {
        "scn_future": "Future view (2040)",
        "future_note": "2040 view: temperature {dt} °C (the NASA trend extended to 2040), rainfall unchanged because it varies too much between years, and zone salinity from the study's 2040 projection. An estimate, not a forecast.",
        "zone_label": "Where is your field on the plain?",
        "z_coast": "Coastal strip",
        "z_injection": "Injection-well belt (1–2 km from the shore)",
        "z_central": "Central plain (freshwater zone)",
        "z_mountain": "Mountain edge (Jabal Al Qara foothills)",
        "z_manual": "I'll enter the salinity myself",
        "zone_outside": "The zones come from a study of the Salalah Plain, so they apply to Salalah and Taqah only. For this location, enter the salinity yourself.",
        "z_tds": "Modeled groundwater salinity: {now} ppm (2020) and {fut} ppm (2040).",
        "z_tds_nofut": "Modeled groundwater salinity: {now} ppm. The study gives no 2040 projection for this zone.",
        "z_level": "Salinity level used in the calculation: {lvl}",
        "z_src": "Source: Al-Hadhrami et al. (2024). These are modeled values, not measurements. Converting them to levels is our own estimate and needs expert review.",
        "lvl_1": "Low", "lvl_2": "Medium", "lvl_3": "High", "lvl_4": "Very high",
        "wt_shallow": "Warning: groundwater is close to the surface here (0 m at the coast, per the study). Salts can rise to the roots and the soil can become waterlogged, so check drainage.",
        "wt_central": "Groundwater is deeper in the central plain (up to about 9 m, per the study), which usually lowers the risk of salts rising.",
        "sal_warn4": "Salinity here is higher than any listed crop can tolerate, so every option is at risk. Consider less saline water or very salt-tolerant crops.",
        "u_m3": "m³",
        "head_less": "less water per hectare than {prev}",
        "head_more": "more water per hectare than {prev}",
        "head_same": "about the same water as {prev}",
        "head_detail": "{top}: {a} m³ per hectare | {prev}: {b} m³ per hectare",
        "how_title": "How the scores work",
        "how": [
            ("Irrigation need", "irrigation = max(0, water-use factor × evaporation − usable rain)", "Standard FAO method applied to NASA data over the crop's growing months. Evaporation is estimated from temperature and sunlight (Hargreaves)."),
            ("Water score", "100 × (1 − (irrigation − lowest) / (highest − lowest))", "Compares crops with each other, so it changes if the crop list changes."),
            ("Soil score", "start 50 | new family +10 | same family −35 | fixes N +20 | N-hungry after legume +15 | two N-hungry −15 | roots differ ≥ 0.4 m +10", "Assumption: rule-of-thumb points, not validated."),
            ("Salinity score", "100 if tolerance ≥ level, else 100 − 50 × (level − tolerance)", "Assumption: the 50-point step is a rule of thumb, and crop tolerances are approximate."),
            ("Final score", "(w1×water + w2×soil + w3×salinity) / (w1 + w2 + w3)", "w1, w2 and w3 are your three sliders."),
            ("Zone salinity", "ppm: ≤700 low | ≤2,100 medium | ≤3,000 high | above very high", "Zone values are modeled results from Al-Hadhrami et al. (2024). Converting them to levels is our own estimate and needs expert review."),
            ("Future view", "evaporation × (T + warming + 17.8) / (T + 17.8)", "Warming = the NASA temperature trend per decade × years to 2040. Rainfall is not projected because it varies too much between years."),
        ],
    },
}
for _lg in STR:
    STR[_lg].update(STR3[_lg])

STR4 = {
    "ar": {
        "tag_step": "مخطط الدورات الزراعية",
        "use_title": "كيف تستخدمه؟",
        "use_steps": ["اختر موقعك والجزء الذي يقع فيه حقلك", "أخبرنا بمحصولك السابق وشهر الزراعة وما يهمك", "اقرأ أفضل المحاصيل للزراعة التالية والماء الذي توفّره"],
        "inputs_title": "أخبرنا عن حقلك",
        "inputs_intro": "بضع اختيارات سريعة، ولا تحتاج معرفة تقنية.",
        "h_zone": "اختر جزء السهل الذي يقع فيه حقلك. هو الذي يحدد ملوحة المياه.",
        "h_prev": "المحصول الذي حصدته آخر مرة.",
        "h_month": "الشهر الذي تنوي الزراعة فيه.",
        "h_prio": "يغيّر ترتيب المحاصيل.",
        "h_future": "يعرض ظروف 2040: مناخاً أدفأ وتوقعات الدراسة للملوحة.",
        "in_prio": "ما الأهم لك؟",
        "prio_water": "توفير المياه", "prio_soil": "حماية التربة", "prio_bal": "متوازن",
        "future_toggle": "عرض توقعات 2040",
        "ans_less": "بعد {prev}، الأنسب أن تزرع {top} في {month}: ماء أقل بنحو {n} م³ للهكتار.",
        "ans_more": "بعد {prev}، الأنسب أن تزرع {top} في {month}. يحتاج ماءً أكثر بنحو {n} م³ للهكتار، لكن الترتيب يراعي التربة والملوحة أيضاً.",
        "ans_same": "بعد {prev}، الأنسب أن تزرع {top} في {month}، بنفس احتياج المياه تقريباً.",
        "fit_strong": "ملاءمة قوية", "fit_good": "ملاءمة جيدة", "fit_weak": "ملاءمة ضعيفة",
        "res_title": "أفضل 3 محاصيل للزراعة التالية",
        "clim_title2": "المناخ في موقعك",
        "clim_intro2": "بيانات ناسا، متوسط {s}–{e}.",
        "f_warm": "اتجاه الحرارة",
        "exp_crops": "معلومات عن المحاصيل",
        "final": ("الدرجة النهائية", "(w1×water + w2×soil + w3×salinity) / (w1 + w2 + w3)", "الأوزان (مياه/تربة/ملوحة) تحددها أولويتك: توفير المياه 8/3/4، حماية التربة 3/8/4، متوازن 5/5/5."),
    },
    "en": {
        "tag_step": "Crop rotation planner",
        "use_title": "How to use it",
        "use_steps": ["Pick your location and the part of the plain where your field is", "Tell us your last crop, planting month and what matters most", "Read the best crops to plant next and the water you save"],
        "inputs_title": "Tell us about your field",
        "inputs_intro": "A few quick choices. No technical knowledge needed.",
        "h_zone": "Pick the part of the plain where your field is. It sets the water salinity.",
        "h_prev": "The crop you harvested last.",
        "h_month": "The month you plan to plant.",
        "h_prio": "Changes how the crops are ranked.",
        "h_future": "Shows 2040 conditions: a warmer climate and the study's salinity projection.",
        "in_prio": "What matters most to you?",
        "prio_water": "Save water", "prio_soil": "Protect soil", "prio_bal": "Balanced",
        "future_toggle": "Show the 2040 outlook",
        "ans_less": "After {prev}, plant {top} in {month}: about {n} m³ less water per hectare.",
        "ans_more": "After {prev}, plant {top} in {month}. It needs about {n} m³ more water per hectare, but the ranking also weighs soil and salinity.",
        "ans_same": "After {prev}, plant {top} in {month}, with about the same water need.",
        "fit_strong": "Strong fit", "fit_good": "Good fit", "fit_weak": "Weak fit",
        "res_title": "Best 3 crops to plant next",
        "clim_title2": "Climate at your location",
        "clim_intro2": "NASA data, averages for {s}–{e}.",
        "f_warm": "Temperature trend",
        "exp_crops": "Crop information",
        "final": ("Final score", "(w1×water + w2×soil + w3×salinity) / (w1 + w2 + w3)", "The weights (water / soil / salinity) come from your priority: Save water 8/3/4, Protect soil 3/8/4, Balanced 5/5/5."),
    },
}
for _lg in STR:
    STR[_lg].update(STR4[_lg])
    STR[_lg]["how"][4] = STR4[_lg]["final"]
PRIO = {"water": (8, 3, 4), "soil": (3, 8, 4), "bal": (5, 5, 5)}  # أوزان (مياه، تربة، ملوحة)


# مناطق سهل صلالة من دراسة Al-Hadhrami وآخرون (2024)، قيم نموذجية (ppm)
ZONE_IDS = ["coast", "injection", "central", "mountain"]
ZONES = {  # متوسط آبار الدراسة / mean of the study's wells
    "coast": {"now": 2520, "future": 28898},
    "injection": {"now": 2756, "future": 5895},
    "central": {"now": 658, "future": 1165},
    "mountain": {"now": 650, "future": 650},
}
ZONE_TXT = {  # كما في الدراسة / as reported
    "coast": ("2,520", "28,898"),
    "injection": ("2,520–2,992", "5,631–6,160"),
    "central": ("586–775", "995–1,468"),
    "mountain": ("500–800", None),
}


def tds_to_level(tds: float) -> int:
    """تحويل التقدير: ≤700 منخفضة، ≤2100 متوسطة، ≤3000 عالية، غير ذلك عالية جداً (تقدير منا)."""
    return 1 if tds <= 700 else 2 if tds <= 2100 else 3 if tds <= 3000 else 4

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


def season_water(clim: pd.DataFrame, params: dict, start_month: int, delta_t: float = 0.0):
    """احتياج الريّ = (معامل الماء × التبخر) - المطر المفيد، على امتداد موسم المحصول."""
    remaining, m = float(params["days"]), int(start_month)
    etc = peff = 0.0
    while remaining > 0:
        frac = min(1.0, remaining / 30.4)
        t = clim.loc[m, "T2M"]
        et0 = clim.loc[m, "et0_mm"] * (t + delta_t + 17.8) / (t + 17.8)
        etc += params["kc"] * et0 * frac
        peff += peff_month(clim.loc[m, "rain_mm"]) * frac
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


def recommend(clim, prev_id, start_month, sal_level, weights, delta_t=0.0):
    """يرتّب المحاصيل التالية. weights = (مياه، تربة، ملوحة)."""
    water = {cid: season_water(clim, p, start_month, delta_t)[2] for cid, p in CROP_PARAMS.items()}
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
        why = [("good", "ir", {"ir": int(round(ir * 10, -2))})]
        if cid != prev_id:
            d = prev_ir - ir
            if d >= 20:
                why.append(("good", "ir_less", {"d": int(round(d * 10, -2))}))
            elif d <= -20:
                why.append(("warn", "ir_more", {"d": int(round(-d * 10, -2))}))
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
.headline{background:var(--forest); color:#fff; border-radius:30px; padding:30px; margin-top:24px;}
.hl-num{font-family:'Cormorant Garamond','Amiri',serif; font-size:clamp(46px,9vw,68px); line-height:1.05; font-weight:500; font-variant-numeric:lining-nums;}
.hl-num small{font-family:'Inter','IBM Plex Sans Arabic',sans-serif; font-size:20px; opacity:.85; font-weight:400;}
.hl-txt{font-size:18px; margin-top:6px;}
.hl-det{font-size:14px; opacity:.85; margin-top:12px;}
.fx{direction:ltr; text-align:left; font-family:ui-monospace,Menlo,Consolas,monospace; font-size:13px; background:#fff; border-radius:12px; padding:10px 14px; margin:8px 0 4px; line-height:1.6;}
.hl-sentence{font-family:'Cormorant Garamond','Amiri',serif; font-size:clamp(26px,5vw,38px); line-height:1.25; font-weight:500;}
.fit{font-size:16px; font-weight:600; margin:6px 0 14px;}
.fit small{font-weight:400; color:var(--graphite); font-size:14px;}
.hint{font-size:13px; color:var(--pewter); margin-top:-8px; line-height:1.5;}
.rise{animation:rise .5s ease both;}
@keyframes rise{from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:none;}}
@media (prefers-reduced-motion:reduce){.rise{animation:none;}}
.how{padding:12px 0; border-top:1px solid rgba(7,80,63,.18);}
[data-testid="stExpander"]{border:1px solid var(--moss) !important; border-radius:20px !important; background:#fff;}
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


def pick_reasons(why, n=3):
    ir = [w for w in why if w[1] == "ir"]
    warns = [w for w in why if w[0] == "warn"]
    rest = [w for w in why if w[0] == "good" and w[1] != "ir"]
    return (ir + warns + rest)[:n]


def rec_cards_html(results, lang, S, prev_id) -> str:
    prev_name = CROP_NAME[prev_id][lang]
    tones = ["sage", "sky", "peach"]
    cards = []
    for i, r in enumerate(results):
        whys = "".join(
            f'<div class="why {kind}"><span class="mk">{"✓" if kind == "good" else "!"}</span>'
            f'<span>{S["why"][code].format(prev=prev_name, **params)}</span></div>'
            for kind, code, params in pick_reasons(r["why"])
        )
        fit = S["fit_strong"] if r["score"] >= 75 else S["fit_good"] if r["score"] >= 55 else S["fit_weak"]
        cards.append(
            f'<div class="card {tones[i % 3]} rise"><span class="rank">#{i + 1}</span>'
            f'<div class="crop-name">{CROP_NAME[r["id"]][lang]}</div>'
            f'<div class="fit">{fit} <small>· {r["score"]}/100</small></div>{whys}</div>'
        )
    return f'<div class="grid-wide">{"".join(cards)}</div>'


def sources_html(S) -> str:
    return "".join(
        f'<div class="how"><div class="benefit-title">{t}</div><div class="small-note">{x}</div></div>'
        for t, x in S["notes"]
    )


def zone_info_html(zone, S, scenario) -> str:
    now, fut = ZONE_TXT[zone]
    lvl = tds_to_level(ZONES[zone]["future" if scenario == "future" else "now"])
    txt = S["z_tds"].format(now=now, fut=fut) if fut else S["z_tds_nofut"].format(now=now)
    out = (
        f'<div class="card sage" style="margin-top:16px"><div class="kpi-label">{S["z_level"].format(lvl=S["lvl_%d" % lvl])}</div>'
        f'<div class="small-note" style="margin-top:6px">{txt}</div><div class="small-note">{S["z_src"]}</div></div>'
    )
    wt = {"coast": "wt_shallow", "injection": "wt_shallow", "central": "wt_central"}.get(zone)
    notes = [(wt, "warn" if wt == "wt_shallow" else "good")] if wt else []
    if lvl >= 4:
        notes.append(("sal_warn4", "warn"))
    for key, kind in notes:
        out += (
            f'<div class="card {"peach" if kind == "warn" else "ash"}" style="margin-top:16px">'
            f'<div class="why {kind}" style="border-top:none;padding:0"><span class="mk">{"!" if kind == "warn" else "i"}</span>'
            f'<span>{S[key]}</span></div></div>'
        )
    return out


def how_html(S) -> str:
    return "".join(
        f'<div class="how"><div class="benefit-title">{t}</div><div class="fx">{f}</div>'
        f'<div class="small-note">{x}</div></div>'
        for t, f, x in S["how"]
    )


def hint(col, text):
    col.markdown(f'<div class="hint">{text}</div>', unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Field Shift · ظفار / Dhofar", layout="wide")

    pick = st.radio(
        "Language / اللغة", ["العربية", "English"], horizontal=True,
        label_visibility="collapsed", key="lang",
    )
    lang = "ar" if pick == "العربية" else "en"
    S = STR[lang]
    st.markdown(CSS.replace("__DIR__", "rtl" if lang == "ar" else "ltr"), unsafe_allow_html=True)
    st.markdown(hero_html(S), unsafe_allow_html=True)

    # كيف تستخدمه / how to use
    steps = "".join(
        f'<div class="card {tone}"><div class="kpi-value" style="font-size:38px">{i}</div>'
        f'<div class="small-note" style="font-size:15px;color:var(--charcoal)">{txt}</div></div>'
        for i, (tone, txt) in enumerate(zip(["sage", "sky", "peach"], S["use_steps"]), 1)
    )
    st.markdown(section_html(S["use_title"]) + f'<div class="grid">{steps}</div>', unsafe_allow_html=True)

    # المدخلات / inputs
    st.markdown(section_html(S["inputs_title"], S["inputs_intro"]), unsafe_allow_html=True)
    site = st.selectbox(
        S["site_label"], list(SITES.keys()) + ["custom"],
        format_func=lambda k: SITE_NAMES[lang][k], key="site",
    )
    if site == "custom":
        c1, c2 = st.columns(2)
        lat = c1.number_input(S["lat"], value=17.02, format="%.3f", key="lat")
        lon = c2.number_input(S["lon"], value=54.09, format="%.3f", key="lon")
    else:
        lat, lon = SITES[site]

    r1a, r1b = st.columns(2)
    zone = "manual"
    if site in ("salalah", "taqah"):
        zone = r1a.selectbox(
            S["zone_label"], ZONE_IDS + ["manual"], index=2,
            format_func=lambda k: S["z_" + k], key="zone",
        )
        hint(r1a, S["h_zone"])
    else:
        r1a.markdown(f'<div class="hint" style="margin-top:0">{S["zone_outside"]}</div>', unsafe_allow_html=True)
    if zone == "manual":
        sal_key = r1a.selectbox(
            S["in_sal"], ["low", "med", "high"], index=1,
            format_func=lambda k: S["sal_" + k], key="sal",
        )
    prev_id = r1b.selectbox(
        S["in_prev"], CROP_IDS, format_func=lambda k: CROP_NAME[k][lang], key="prev"
    )
    hint(r1b, S["h_prev"])

    r2a, r2b = st.columns(2)
    month = r2a.selectbox(
        S["in_month"], list(range(1, 13)), index=9,
        format_func=lambda m: MONTHS[lang][m - 1], key="month",
    )
    hint(r2a, S["h_month"])
    prio = r2b.radio(
        S["in_prio"], ["water", "soil", "bal"], index=2, horizontal=True,
        format_func=lambda k: S["prio_" + k], key="prio",
    )
    hint(r2b, S["h_prio"])
    future = st.toggle(S["future_toggle"], key="future")
    hint(st, S["h_future"])
    scenario = "future" if future else "now"

    if zone == "manual":
        level = {"low": 1.0, "med": 2.0, "high": 3.0}[sal_key]
    else:
        level = float(tds_to_level(ZONES[zone]["future" if future else "now"]))
        st.markdown(zone_info_html(zone, S, scenario), unsafe_allow_html=True)

    with st.spinner(S["spinner"]):
        try:
            df = fetch_power(lat, lon)
        except Exception as e:
            st.error(S["error"])
            st.code(str(e))
            st.stop()
    ann = annual_summary(df)
    clim = monthly_climatology(df)
    t_trend = decade_trend(ann["temp_c"])
    delta_t = 0.0
    if future and not np.isnan(t_trend):
        delta_t = t_trend * max(0, 2040 - END_YEAR) / 10

    # النتيجة / result
    results, prev_ir = recommend(clim, prev_id, month, level, PRIO[prio], delta_t)
    top = results[:3]
    prev_name, top_name = CROP_NAME[prev_id][lang], CROP_NAME[top[0]["id"]][lang]
    saving = (prev_ir - top[0]["ir"]) * 10  # م³/هكتار: 1 ملم = 10 م³/هكتار
    kind = "ans_less" if saving >= 200 else "ans_more" if saving <= -200 else "ans_same"
    answer = S[kind].format(
        prev=prev_name, top=top_name, month=MONTHS[lang][month - 1],
        n=f"{abs(int(round(saving, -2))):,}",
    )
    detail = S["head_detail"].format(
        top=top_name, a=f"{int(round(top[0]['ir'] * 10, -2)):,}",
        prev=prev_name, b=f"{int(round(prev_ir * 10, -2)):,}",
    )
    st.markdown(section_html(S["res_title"]), unsafe_allow_html=True)
    st.markdown(
        f'<div class="headline rise"><div class="hl-sentence">{answer}</div>'
        f'<div class="hl-det">{detail}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    st.markdown(rec_cards_html(top, lang, S, prev_id), unsafe_allow_html=True)
    if future:
        st.markdown(
            f'<div class="small-note">{S["future_note"].format(dt=f"{delta_t:+.1f}")}</div>',
            unsafe_allow_html=True,
        )
    st.markdown(f'<div class="small-note">{S["disclaimer"]}</div>', unsafe_allow_html=True)

    # المناخ / climate (3 facts + 1 chart)
    st.markdown(
        section_html(S["clim_title2"], S["clim_intro2"].format(s=START_YEAR, e=END_YEAR)),
        unsafe_allow_html=True,
    )
    facts = "".join(
        [
            kpi_card(S["k_rain"], fmt(ann["rain_mm"].mean()), S["u_mm"], "sky"),
            kpi_card(S["k_et0"], fmt(ann["et0_mm"].mean()), S["u_mm"], "sage"),
            kpi_card(S["f_warm"], fmt(t_trend, 2, True), S["u_c_dec"], "peach"),
        ]
    )
    st.markdown(f'<div class="grid">{facts}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-cap">{S["cap_bar"]}</div>', unsafe_allow_html=True)
    st.bar_chart(
        clim[["rain_mm", "et0_mm"]].rename(columns={"rain_mm": S["s_rain"], "et0_mm": S["s_et0"]}),
        color=["#07503f", "#6d6d6d"], height=300,
    )
    st.markdown(f'<div class="small-note">{S["trend_note"]}</div>', unsafe_allow_html=True)

    # تفاصيل قابلة للطي / details
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    with st.expander(S["exp_crops"]):
        st.markdown(crop_cards_html(lang, S), unsafe_allow_html=True)
    with st.expander(S["how_title"]):
        st.markdown(how_html(S), unsafe_allow_html=True)
    with st.expander(S["notes_title"]):
        st.markdown(sources_html(S), unsafe_allow_html=True)
    st.markdown(footer_html(S), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
