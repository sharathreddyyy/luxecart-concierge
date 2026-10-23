"""LuxeCart Concierge - Streamlit interface (Assignment 6A)."""
import csv, html, io, os
from datetime import datetime

import streamlit as st

import concierge as C

HERE = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="LuxeCart Concierge", page_icon="✦", layout="centered")


@st.cache_data
def load_data():
    return C.load_catalog(os.path.join(HERE, "data", "catalog.csv")), C.load_vocab(os.path.join(HERE, "data", "vocab.json"))


def secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.environ.get(name, default)


CATALOG, VOCAB = load_data()
API_KEY = secret("GEMINI_API_KEY")
MODELS = [m.strip() for m in secret("GEMINI_MODELS", "gemini-3.1-flash-lite,gemini-3.8-flash").split(",") if m.strip()]
SIZE_OPTIONS = {
    "Not sure / not needed": None,
    "XS": "XS", "S": "S", "M": "M", "L": "L", "XL": "XL",
    "US 6": "6", "US 7": "7", "US 8": "8", "US 9": "9", "US 10": "10", "US 11": "11",
    "One size (bags, watches, jewellery, sunglasses)": "One Size",
}
EXAMPLES = [
    ("Wedding guest dress", "Something elegant for a winter wedding, a dress I can actually dance in", 120, "M"),
    ("Office watch", "A classic watch for my first week at a new office job, nothing too loud", 300, "One size (bags, watches, jewellery, sunglasses)"),
    ("Graduation gift", "Earrings as a gift for my sister's graduation", 100, "One size (bags, watches, jewellery, sunglasses)"),
]
MAX_REQUESTS_PER_VISIT = 25

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,600&family=Source+Sans+3:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Source Sans 3', 'Segoe UI', sans-serif; }
h1, h2, h3 { font-family: 'Bodoni Moda', Georgia, serif !important; color: #1F2A44 !important; font-weight: 600 !important; }
.lc-mark { letter-spacing: .38em; font-size: .72rem; color: #A88B5A; font-weight: 700; }
.lc-sub { color: #5B6170; font-size: 1.02rem; margin-top: -.4rem; }
.lc-card { border: 1px solid #E2DED6; border-top: 3px solid #1F2A44; border-radius: 4px; padding: 1rem 1.15rem; margin: .7rem 0; background: #fff; }
.lc-row { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
.lc-rank { font-family: 'Bodoni Moda', Georgia, serif; color: #A88B5A; font-size: 1.9rem; line-height: 1; min-width: 1.6rem; }
.lc-name { font-weight: 700; color: #1F2A44; font-size: 1.08rem; }
.lc-facts { color: #5B6170; font-size: .9rem; margin: .15rem 0 .5rem; }
.lc-facts b { color: #1E1B18; }
.lc-note { font-family: Georgia, serif; font-style: italic; font-size: 1.02rem; color: #1E1B18; }
.lc-why { color: #6B6760; font-size: .85rem; margin-top: .45rem; }
.lc-score { text-align: right; color: #6B6760; font-size: .75rem; min-width: 3.4rem; }
.lc-score b { display: block; font-family: 'Bodoni Moda', Georgia, serif; font-size: 1.6rem; color: #1F2A44; }
.lc-stock-low { color: #9A6212; font-weight: 600; }
.stButton>button[kind="primary"], .stFormSubmitButton>button { background: #1F2A44; border-color: #1F2A44; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="lc-mark">LUXECART CONCIERGE</div>', unsafe_allow_html=True)
st.title("Your personal stylist, online")
st.markdown('<p class="lc-sub">Describe what you need in your own words. We suggest up to three pieces that are in stock, in your size and within your budget.</p>', unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
for k, v in (("req_text", ""), ("req_budget", 150), ("req_size", "Not sure / not needed")):
    if k not in st.session_state:
        st.session_state[k] = v


def use_example(i):
    _, t, b, s = EXAMPLES[i]
    st.session_state.req_text, st.session_state.req_budget, st.session_state.req_size = t, b, s


tab_find, tab_carry, tab_history = st.tabs(["Find pieces", "What we carry", "Your requests"])

with tab_find:
    st.caption("Not sure how to start? Try an example:")
    cols = st.columns(len(EXAMPLES))
    for i, (label, *_rest) in enumerate(EXAMPLES):
        cols[i].button(label, key=f"ex{i}", on_click=use_example, args=(i,), use_container_width=True)

    with st.form("request"):
        text = st.text_area("What are you shopping for?", key="req_text", height=90,
                            placeholder='For example: "An understated dress for a winter wedding, nothing flashy"',
                            help="Mention the kind of piece and the occasion. Style words like understated, bold or classic help too.")
        c1, c2 = st.columns(2)
        budget = c1.number_input("Your maximum budget (USD)", key="req_budget", min_value=0, max_value=100000, step=10,
                                 help="We never show anything above this amount.")
        size_label = c2.selectbox("Your size", list(SIZE_OPTIONS.keys()), key="req_size",
                                  help="Clothing uses XS to XL, shoes use US sizes. Bags, watches, jewellery and sunglasses are one size.")
        submitted = st.form_submit_button("Find my pieces", type="primary", use_container_width=True)

    if submitted:
        size = SIZE_OPTIONS[size_label]
        problems = C.validate_request(text, budget, size)
        if len(st.session_state.history) >= MAX_REQUESTS_PER_VISIT:
            problems.append("You have reached the limit of requests for this visit. Please refresh the page to start again.")
        if problems:
            st.error("We need a little more information before we can help:\n\n" + "\n".join(f"- {p}" for p in problems))
        else:
            with st.spinner("Our stylist is reading your request and checking what is in stock..."):
                res = C.run_concierge(text, budget, size, CATALOG, VOCAB, API_KEY, MODELS)
            st.session_state.history.append({
                "time": datetime.now().strftime("%H:%M"), "request": text.strip(), "budget_usd": budget,
                "size": size or "-", "outcome": {"ok": "Pieces found", "needs_clarification": "Question asked",
                                                  "no_match": "Nothing fits", "error": "Service busy"}[res.status],
                "pieces": "; ".join(f"{p['name']} (${p['price_usd']:g})" for p in res.picks),
                "seconds": res.seconds})

            for n in res.notes:
                st.caption(n)
            if res.status == "ok":
                st.success(f"{res.message} Every piece below is in stock, in your size and within ${budget:,.0f}.")
                for i, p in enumerate(res.picks, 1):
                    stock = f'<span class="lc-stock-low">{p["stock"]}</span>' if p["stock"] != "In stock" else "In stock"
                    brand = html.escape(p["brand"]) + " · " if p["brand"] else ""
                    color = " · " + html.escape(p["color"]) if p["color"] else ""
                    st.markdown(f"""
<div class="lc-card"><div class="lc-row">
  <div class="lc-rank">{i}</div>
  <div style="flex:1">
    <div class="lc-name">{html.escape(p['name'])}</div>
    <div class="lc-facts">{brand}{html.escape(p['category'].title())}{color} · <b>${p['price_usd']:,.2f}</b> · Size {html.escape(p['size'])} · {stock}</div>
    <div class="lc-note">&ldquo;{html.escape(p['note'])}&rdquo;</div>
    <div class="lc-why">Why we chose it: {html.escape(p['reason'])}</div>
  </div>
  <div class="lc-score"><b>{p['match_score']}</b>match</div>
</div></div>""", unsafe_allow_html=True)
            elif res.status == "needs_clarification":
                st.info("**One quick question before we choose:** " + res.message)
            elif res.status == "no_match":
                st.warning("**Nothing fits all your limits yet.** " + res.message)
                if res.near_misses:
                    st.markdown("**Closest pieces we have.** These do not meet every limit you set, so check the note on each:")
                    for p in res.near_misses:
                        color = " · " + html.escape(p["color"]) if p["color"] else ""
                        st.markdown(f"""
<div class="lc-card" style="border-top-color:#A88B5A"><div class="lc-name">{html.escape(p['name'])}</div>
<div class="lc-facts">{html.escape(p['category'].title())}{color} · <b>${p['price_usd']:,.2f}</b></div>
<div class="lc-why" style="color:#9A6212;font-weight:600">Heads up: {html.escape(p['why_not'])}</div></div>""", unsafe_allow_html=True)
                st.caption("You can also open the \"What we carry\" tab to see every category and price range.")
            else:
                st.error(res.message + " Nothing was saved or charged.")

            if res.intent or res.checks:
                with st.expander("How we chose these"):
                    if res.intent:
                        it = res.intent
                        st.markdown(f"**What we understood:** {html.escape(it.get('summary') or '-')}  \n"
                                    f"**Looking for:** {it.get('category', '-')} · **Occasion:** {it.get('occasion') or '-'} · "
                                    f"**Style:** {', '.join(it.get('style_tags', [])) or '-'}")
                    for c in res.checks:
                        st.markdown(f"- {c}")
                    st.caption(f"Answered in {res.seconds} s. Prices, sizes and stock come from our catalog, never from the AI's wording.")

with tab_carry:
    st.subheader("What we carry")
    st.write("The concierge only recommends pieces from this catalog. If we do not carry something, it will tell you instead of inventing it.")
    rows = {}
    for p in CATALOG:
        r = rows.setdefault(p["category"], {"Category": p["category"].title(), "Pieces in stock": 0, "From": 1e9, "Up to": 0})
        if p["in_stock"]:
            r["Pieces in stock"] += 1
            r["From"], r["Up to"] = min(r["From"], p["price_usd"]), max(r["Up to"], p["price_usd"])
    table = [{**r, "From": f"${r['From']:,.2f}", "Up to": f"${r['Up to']:,.2f}"} for r in sorted(rows.values(), key=lambda r: r["Category"])]
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.caption("Demo catalog of 47 pieces built from public test data (Assignment 3). Clothing sizes XS to XL, shoes US 6 to 11; bags, watches, jewellery and sunglasses are one size.")

with tab_history:
    st.subheader("Your requests this visit")
    if not st.session_state.history:
        st.write("Nothing yet. Your requests and their outcomes will appear here, so you can compare or download them.")
    else:
        st.dataframe(st.session_state.history, hide_index=True, use_container_width=True)
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(st.session_state.history[0].keys()))
        w.writeheader(); w.writerows(st.session_state.history)
        st.download_button("Download as a spreadsheet (CSV)", buf.getvalue(), file_name="luxecart_requests.csv", mime="text/csv")

st.divider()
st.caption("LuxeCart Concierge · a student project (INFO 7375). Your request is sent to Google's Gemini service to understand it; please do not include personal details. Prices are demo prices.")
