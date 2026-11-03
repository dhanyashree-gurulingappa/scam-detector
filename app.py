import re
import joblib
import streamlit as st
from textutils import normalize

st.set_page_config(page_title="Scam SMS Detector", page_icon="🛡️", layout="centered")

CSS = """
<style>
.block-container {max-width: 720px; padding-top: 2.2rem;}
.hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #38bdf8 100%);
    border-radius: 18px; padding: 28px 26px; color: #ffffff; margin-bottom: 22px;
}
.hero h1 {color: #ffffff; font-size: 1.9rem; margin: 0 0 6px 0; padding: 0;}
.hero p {color: #e0f2fe; margin: 0; font-size: 1rem;}
.langs {margin-top: 12px;}
.pill {
    display: inline-block; background: rgba(255,255,255,0.18); color: #ffffff;
    border-radius: 999px; padding: 3px 12px; font-size: 0.8rem; margin-right: 6px;
}
.verdict {border-radius: 16px; padding: 22px 22px 18px 22px; margin-top: 18px; color: #1f2937;}
.verdict .big {font-size: 1.6rem; font-weight: 800; margin-bottom: 4px;}
.verdict .sub {font-size: 1rem; margin-bottom: 14px; color: #374151;}
.bar-bg {background: rgba(0,0,0,0.10); border-radius: 999px; height: 10px; width: 100%;}
.bar-fill {height: 10px; border-radius: 999px;}
.conf {font-size: 0.85rem; color: #4b5563; margin-top: 6px;}
.scam {background: #fdecec; border: 2px solid #e5484d;}
.scam .big {color: #b42318;}
.scam .bar-fill {background: #e5484d;}
.maybe {background: #fff6e5; border: 2px solid #f5a524;}
.maybe .big {color: #b54708;}
.maybe .bar-fill {background: #f5a524;}
.safe {background: #eaf7ee; border: 2px solid #30a46c;}
.safe .big {color: #067647;}
.safe .bar-fill {background: #30a46c;}
.advice {
    border-radius: 14px; padding: 16px 20px; margin-top: 14px;
    background: #f3f4f6; color: #1f2937; border: 1px solid #e5e7eb;
}
.advice h4 {margin: 0 0 8px 0; color: #111827; font-size: 1.05rem;}
.advice ul {margin: 0; padding-left: 20px;}
.advice li {margin-bottom: 5px; color: #1f2937;}
.warnbox {
    border-radius: 14px; padding: 14px 18px; margin-top: 14px;
    background: #fff1f2; border: 1px solid #fecdd3; color: #9f1239; font-weight: 600;
}
.okbox {
    border-radius: 14px; padding: 14px 18px; margin-top: 14px;
    background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; font-weight: 600;
}
.foot {color: #6b7280; font-size: 0.82rem; margin-top: 26px; line-height: 1.5;}
div.stButton > button {
    width: 100%; background: #2563eb; color: #ffffff; border: none; border-radius: 12px;
    padding: 0.7rem 1rem; font-size: 1.05rem; font-weight: 700;
}
div.stButton > button:hover {background: #1d4ed8; color: #ffffff; border: none;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
<div class="hero">
  <h1>🛡️ Scam SMS Detector</h1>
  <p>Got a suspicious message? Paste it below and find out if it is safe.</p>
  <div class="langs">
    <span class="pill">English</span><span class="pill">ಕನ್ನಡ</span>
    <span class="pill">हिन्दी</span><span class="pill">Mixed</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_model():
    return joblib.load("model.joblib")


model = load_model()
clf = model.steps[-1][1]
scam_idx = list(clf.classes_).index("scam")

LINK_RE = re.compile(r"<URL>")
OTP_RE = re.compile(r"(?i)\b(otp|pin|cvv|password)\b|ओटीपी|ಒಟಿಪಿ")
URGENT_RE = re.compile(
    r"(?i)\b(urgent|immediately|expires?|expired|blocked|suspended|hurry|final notice|deactivated|disconnected)\b"
    r"|तुरंत|अभी|ತಕ್ಷಣ|ಈಗಲೇ|ಇಂದು"
)
PRIZE_RE = re.compile(
    r"(?i)\b(lottery|prize|winner|won|reward|refund|cashback|loan|free)\b"
    r"|लॉटरी|इनाम|रिफंड|ಬಹುಮಾನ|ಲಾಟರಿ|ರಿಫಂಡ್"
)


def risk_reasons(raw_text, clean_text):
    reasons = []
    if LINK_RE.search(clean_text):
        reasons.append("It contains a link. Scammers use links to steal your details.")
    if OTP_RE.search(raw_text):
        reasons.append("It mentions an OTP, PIN or password. Real banks never ask for these.")
    if URGENT_RE.search(raw_text):
        reasons.append("It tries to rush you with threats or deadlines.")
    if PRIZE_RE.search(raw_text):
        reasons.append("It talks about prizes, refunds, loans or free offers.")
    if not reasons:
        reasons.append("The wording is very similar to known scam messages.")
    return reasons


def verdict_card(css_class, title, subtitle, pct, label):
    return f"""
<div class="verdict {css_class}">
  <div class="big">{title}</div>
  <div class="sub">{subtitle}</div>
  <div class="bar-bg"><div class="bar-fill" style="width:{pct}%"></div></div>
  <div class="conf">{label}: {pct}%</div>
</div>
"""


def advice_box(heading, items):
    li = "".join(f"<li>{i}</li>" for i in items)
    return f'<div class="advice"><h4>{heading}</h4><ul>{li}</ul></div>'


text = st.text_area(
    "Paste the message here",
    height=150,
    placeholder="Example: Your KYC has expired. Click this link to update now...",
)

if st.button("Check message"):
    if not text.strip():
        st.warning("Please paste a message first.")
    else:
        clean = normalize(text)
        p_scam = float(model.predict_proba([clean])[0][scam_idx])
        has_link = bool(LINK_RE.search(clean))

        if p_scam >= 0.75:
            st.markdown(
                verdict_card(
                    "scam", "⚠️ Likely a SCAM",
                    "This message looks like a fraud attempt.",
                    round(p_scam * 100), "Scam confidence",
                ),
                unsafe_allow_html=True,
            )
            if has_link:
                st.markdown(
                    '<div class="warnbox">🚫 Do NOT open the link in this message. '
                    "It may be harmful and can steal your money or personal details.</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(advice_box("Why this looks risky", risk_reasons(text, clean)), unsafe_allow_html=True)
            st.markdown(
                advice_box(
                    "What you should do",
                    [
                        "Do not click any link or call any number in the message.",
                        "Never share your OTP, PIN, CVV or password with anyone.",
                        "Do not reply to the sender.",
                        "If it claims to be from your bank, open the official app or call the number on your card.",
                        "Report it at <b>cybercrime.gov.in</b> or call the cyber crime helpline <b>1930</b>.",
                    ],
                ),
                unsafe_allow_html=True,
            )

        elif p_scam >= 0.5:
            st.markdown(
                verdict_card(
                    "maybe", "🤔 Looks SUSPICIOUS",
                    "We are not fully sure. Treat this message with caution.",
                    round(p_scam * 100), "Scam likelihood",
                ),
                unsafe_allow_html=True,
            )
            if has_link:
                st.markdown(
                    '<div class="warnbox">⚠️ Do not open the link until you have confirmed who sent it. '
                    "It may be harmful.</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(advice_box("Why it looks suspicious", risk_reasons(text, clean)), unsafe_allow_html=True)
            st.markdown(
                advice_box(
                    "What you should do",
                    [
                        "Check the sender. Real companies usually send from a named sender ID, not a random number.",
                        "Confirm the offer or notice by opening the official app or website yourself.",
                        "Never share your OTP, PIN or password.",
                    ],
                ),
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                verdict_card(
                    "safe", "✅ Looks SAFE",
                    "This message does not look like a scam.",
                    round((1 - p_scam) * 100), "Safe confidence",
                ),
                unsafe_allow_html=True,
            )
            if has_link:
                st.markdown(
                    '<div class="warnbox">⚠️ It has a link. Even if the message looks safe, only open '
                    "the link if you know and trust the sender.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="okbox">👍 No suspicious links or requests were found in this message.</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                advice_box(
                    "Stay safe anyway",
                    [
                        "No tool is perfect. If something feels wrong, double-check with the sender.",
                        "Never share your OTP, PIN or password with anyone, even if they sound genuine.",
                        "For bank or payment messages, use the official app instead of tapping links.",
                    ],
                ),
                unsafe_allow_html=True,
            )

st.markdown(
    '<div class="foot">This tool gives an estimate, not a guarantee. '
    "Always verify important messages through official apps or websites. "
    "Built as a student project using machine learning.</div>",
    unsafe_allow_html=True,
)
