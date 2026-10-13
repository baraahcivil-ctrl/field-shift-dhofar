"""
Field Shift - ظفار | الخطوة 1: بيانات المناخ من NASA POWER + جدول المحاصيل
تشغيل محلي (اختياري):  streamlit run app.py
"""
import calendar

import numpy as np
import pandas as pd
import requests
import streamlit as st

START_YEAR = 2005
END_YEAR = 2025

# ---------------------------------------------------------------
# مواقع في ظفار (خط العرض، خط الطول)
# ملاحظة: شبكة NASA POWER دقتها تقريباً 0.5 درجة، فالمواقع القريبة تتشابه.
# ---------------------------------------------------------------
SITES = {
    "صلالة (السهل الساحلي)": (17.02, 54.09),
    "ثمريت (الهضبة)": (17.67, 54.03),
    "طاقة": (17.04, 54.40),
    "مرباط": (16.99, 54.69),
}

# ---------------------------------------------------------------
# جدول المحاصيل - قيم تقريبية من مراجع الفاو، ويجب مراجعتها قبل العرض
# FAO-56  = Allen et al. 1998 (Crop evapotranspiration)
# FAO-33  = Doorenbos & Kassam 1979 (Yield response to water)
# FAO-29  = Ayers & Westcot 1985 (Water quality for agriculture)
# ---------------------------------------------------------------
CROPS = [
    {
        "المحصول": "ذرة رفيعة",
        "العائلة النباتية": "النجيلية",
        "مدة الموسم (يوم)": "100-140",
        "احتياج المياه (ملم/موسم)": "450-650",
        "عمق الجذور (م)": "1.0-2.0",
        "يثبّت النيتروجين": "لا",
        "استهلاك النيتروجين": "متوسط",
        "تحمّل الملوحة": "عالٍ",
        "المرجع": "FAO-33, FAO-56, FAO-29",
    },
    {
        "المحصول": "حشيشة رودس",
        "العائلة النباتية": "النجيلية",
        "مدة الموسم (يوم)": "معمّر (قصّات متعددة)",
        "احتياج المياه (ملم/موسم)": "900-1500 سنوياً (تقديري)",
        "عمق الجذور (م)": "0.5-1.5 (تقديري)",
        "يثبّت النيتروجين": "لا",
        "استهلاك النيتروجين": "عالٍ",
        "تحمّل الملوحة": "متوسط إلى عالٍ",
        "المرجع": "FAO-29, FAO-56 (تقديري)",
    },
    {
        "المحصول": "برسيم حجازي (جت)",
        "العائلة النباتية": "البقولية",
        "مدة الموسم (يوم)": "معمّر (قصّات متعددة)",
        "احتياج المياه (ملم/موسم)": "800-1600 سنوياً",
        "عمق الجذور (م)": "1.0-2.0",
        "يثبّت النيتروجين": "نعم",
        "استهلاك النيتروجين": "منخفض (يضيف للتربة)",
        "تحمّل الملوحة": "منخفض إلى متوسط",
        "المرجع": "FAO-33, FAO-56, FAO-29",
    },
    {
        "المحصول": "لوبيا",
        "العائلة النباتية": "البقولية",
        "مدة الموسم (يوم)": "70-110",
        "احتياج المياه (ملم/موسم)": "300-500",
        "عمق الجذور (م)": "0.6-1.0",
        "يثبّت النيتروجين": "نعم",
        "استهلاك النيتروجين": "منخفض (يضيف للتربة)",
        "تحمّل الملوحة": "متوسط",
        "المرجع": "FAO-33, FAO-56 (قيم الفاصوليا الجافة)",
    },
    {
        "المحصول": "طماطم",
        "العائلة النباتية": "الباذنجانية",
        "مدة الموسم (يوم)": "135-180",
        "احتياج المياه (ملم/موسم)": "400-800",
        "عمق الجذور (م)": "0.7-1.5",
        "يثبّت النيتروجين": "لا",
        "استهلاك النيتروجين": "عالٍ",
        "تحمّل الملوحة": "منخفض إلى متوسط",
        "المرجع": "FAO-33, FAO-56, FAO-29",
    },
    {
        "المحصول": "بطيخ",
        "العائلة النباتية": "القرعيات",
        "مدة الموسم (يوم)": "80-110",
        "احتياج المياه (ملم/موسم)": "400-600",
        "عمق الجذور (م)": "0.8-1.5",
        "يثبّت النيتروجين": "لا",
        "استهلاك النيتروجين": "متوسط",
        "تحمّل الملوحة": "منخفض إلى متوسط (تقديري)",
        "المرجع": "FAO-33, FAO-56",
    },
]


# ---------------------------------------------------------------
# بيانات NASA POWER
# ---------------------------------------------------------------
def parse_power(parameters: dict) -> pd.DataFrame:
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
    rs_mj = df["ALLSKY_SFC_SW_DWN"] * 3.6  # كيلوواط ساعة -> ميغاجول
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
    return parse_power(r.json()["properties"]["parameter"])


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
# الواجهة - بنمط Arva: خلفية كريمية، أخضر غابي، بطاقات باستيل، أزرار كبسولة
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
[data-testid="stMain"], .block-container{direction:rtl;}
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
.row span:last-child{font-weight:500; text-align:left;}
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
[data-testid="stAlert"]{border-radius:20px;}
</style>
"""

MARQUEE_ITEMS = [
    "بيانات مناخية حقيقية من NASA POWER",
    "ظفار: صلالة · ثمريت · طاقة · مرباط",
    "أرقام المحاصيل تقريبية من مراجع الفاو",
    "نموذج أولي لهاكاثون ناسا Space Apps",
]
TONES = ["sky", "peach", "sage", "ash"]


def fmt(x, nd=0, sign=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def marquee_html() -> str:
    one = "".join(
        f'<span class="marquee-item"><span class="chk">✓</span>{t}</span>'
        for t in MARQUEE_ITEMS
    )
    return f'<div class="marquee"><div class="marquee-track">{one}{one}</div></div>'


def hero_html() -> str:
    return (
        '<div class="hero">'
        '<div class="hero-kicker">NASA SPACE APPS · FIELD SHIFT</div>'
        '<div class="hero-title">Field Shift: ظفار</div>'
        '<div class="hero-sub">أداة دعم قرار تساعد مزارعي ظفار على استكشاف الدورات الزراعية '
        "التي تحمي التربة وتوفّر المياه، اعتماداً على بيانات ناسا.</div>"
        '<span class="pill-tag solid">NASA POWER</span>'
        f'<span class="pill-tag">{START_YEAR}–{END_YEAR}</span>'
        '<span class="pill-tag">الخطوة 1: المناخ والمحاصيل</span>'
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


def crop_cards_html() -> str:
    fields = [
        ("مدة الموسم (يوم)", "مدة الموسم"),
        ("احتياج المياه (ملم/موسم)", "احتياج المياه (ملم)"),
        ("عمق الجذور (م)", "عمق الجذور (م)"),
        ("يثبّت النيتروجين", "يثبّت النيتروجين"),
        ("استهلاك النيتروجين", "استهلاك النيتروجين"),
        ("تحمّل الملوحة", "تحمّل الملوحة"),
    ]
    cards = []
    for i, c in enumerate(CROPS):
        rows = "".join(
            f'<div class="row"><span>{label}</span><span>{c[key]}</span></div>'
            for key, label in fields
        )
        cards.append(
            f'<div class="card {TONES[i % 4]}">'
            f'<div class="crop-name">{c["المحصول"]}</div>'
            f'<span class="tag">{c["العائلة النباتية"]}</span>{rows}'
            f'<div class="ref">{c["المرجع"]}</div></div>'
        )
    return f'<div class="grid-wide">{"".join(cards)}</div>'


def notes_html() -> str:
    items = [
        ("المناخ", "من NASA POWER (مجاني ومفتوح)، بدقة شبكة تقريباً 0.5 درجة، فالمواقع المتقاربة تتشابه."),
        ("التبخر-نتح", "تقدير بمعادلة هارجريفز المعتمدة على الإشعاع الشمسي، وليس قياساً مباشراً."),
        ("المحاصيل", "أرقام تقريبية من مراجع الفاو (FAO-56, FAO-33, FAO-29) وتتغير حسب الصنف والإدارة."),
        ("النموذج", "نموذج أولي جاهز للتحقق منه مع الخبراء الزراعيين المحليين."),
    ]
    blocks = "".join(
        f'<div class="benefit"><div class="ico">{i}</div><div>'
        f'<div class="benefit-title">{t}</div><div class="benefit-body">{b}</div></div></div>'
        for i, (t, b) in enumerate(items, 1)
    )
    return (
        '<div class="forest">'
        '<div class="sec-title">من أين جاءت الأرقام؟</div>'
        '<div class="sec-intro">الشفافية في المصادر جزء من قوة المشروع.</div>'
        f'<div class="benefits">{blocks}</div></div>'
    )


def footer_html() -> str:
    return (
        '<div class="footer"><div class="brand">Field Shift · ظفار</div>'
        "نموذج أولي لهاكاثون NASA Space Apps<br>البيانات المناخية: NASA POWER</div>"
    )


def main():
    st.set_page_config(page_title="Field Shift ظفار", page_icon="🌾", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(marquee_html(), unsafe_allow_html=True)
    st.markdown(hero_html(), unsafe_allow_html=True)

    # 1) الموقع
    st.markdown(
        section_html("اختر موقع الحقل", "حدّد المنطقة في ظفار لنسحب بياناتها المناخية من ناسا."),
        unsafe_allow_html=True,
    )
    choice = st.selectbox("الموقع", list(SITES.keys()) + ["إحداثيات أخرى"])
    if choice == "إحداثيات أخرى":
        c1, c2 = st.columns(2)
        lat = c1.number_input("خط العرض", value=17.02, format="%.3f")
        lon = c2.number_input("خط الطول", value=54.09, format="%.3f")
    else:
        lat, lon = SITES[choice]
        st.markdown(
            f'<div class="small-note">الإحداثيات: {lat}, {lon}</div>', unsafe_allow_html=True
        )

    with st.spinner("جاري سحب البيانات من NASA POWER..."):
        try:
            df = fetch_power(lat, lon)
        except Exception as e:
            st.error("تعذّر سحب البيانات من NASA POWER. تأكد من الاتصال بالإنترنت وأعد المحاولة.")
            st.code(str(e))
            st.stop()

    ann = annual_summary(df)
    clim = monthly_climatology(df)

    # 2) ملخص المناخ
    st.markdown(
        section_html(
            "ملخص المناخ",
            f"متوسطات {START_YEAR}–{END_YEAR}. موسم الخريف في ظفار (الأشهر 6 إلى 9) هو معظم أمطار السنة.",
        ),
        unsafe_allow_html=True,
    )
    cards = "".join(
        [
            kpi_card("متوسط الحرارة", fmt(ann["temp_c"].mean(), 1), "°م", "peach"),
            kpi_card("الأمطار السنوية", fmt(ann["rain_mm"].mean()), "ملم", "sky"),
            kpi_card("التبخر-نتح (تقدير)", fmt(ann["et0_mm"].mean()), "ملم", "sage"),
            kpi_card("العجز المائي", fmt(ann["deficit_mm"].mean()), "ملم", "ash"),
        ]
    )
    st.markdown(f'<div class="grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-cap">الأمطار مقابل التبخر-نتح حسب الشهر (ملم)</div>', unsafe_allow_html=True)
    st.bar_chart(
        clim[["rain_mm", "et0_mm"]].rename(columns={"rain_mm": "الأمطار", "et0_mm": "التبخر-نتح"}),
        color=["#07503f", "#6d6d6d"],
        height=320,
    )

    # 3) الاتجاه
    st.markdown(
        section_html("اتجاه المناخ", "كيف تغيّر المناخ في هذا الموقع خلال السنوات الماضية."),
        unsafe_allow_html=True,
    )
    trend_cards = "".join(
        [
            kpi_card("الحرارة", fmt(decade_trend(ann["temp_c"]), 2, True), "°م لكل عقد", "peach"),
            kpi_card("الأمطار", fmt(decade_trend(ann["rain_mm"]), 0, True), "ملم لكل عقد", "sky"),
            kpi_card("العجز المائي", fmt(decade_trend(ann["deficit_mm"]), 0, True), "ملم لكل عقد", "sage"),
        ]
    )
    st.markdown(f'<div class="grid">{trend_cards}</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-cap">متوسط الحرارة السنوي (°م)</div>', unsafe_allow_html=True)
    st.line_chart(ann[["temp_c"]].rename(columns={"temp_c": "الحرارة"}), color="#07503f", height=260)
    st.markdown('<div class="chart-cap">الأمطار السنوية (ملم)</div>', unsafe_allow_html=True)
    st.line_chart(ann[["rain_mm"]].rename(columns={"rain_mm": "الأمطار"}), color="#07503f", height=260)
    st.markdown(
        '<div class="small-note">الأمطار في ظفار متذبذبة جداً من سنة لأخرى، فالاتجاه الخطي للاستئناس فقط وليس حكماً قطعياً.</div>',
        unsafe_allow_html=True,
    )

    # 4) المحاصيل
    st.markdown(
        section_html("المحاصيل", "ستة محاصيل مناسبة لظفار. الأرقام تقريبية ومرجعها مكتوب في كل بطاقة."),
        unsafe_allow_html=True,
    )
    st.markdown(crop_cards_html(), unsafe_allow_html=True)

    st.markdown(notes_html(), unsafe_allow_html=True)
    st.markdown(footer_html(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
