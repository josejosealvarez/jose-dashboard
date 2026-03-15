import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import yfinance as yf

# ------------------ CONFIG ------------------
NEWS_API_KEY = "77e397d092b1465398b20f7301b09643"  # <-- Replace this line with your real key!
USER_AGENT = "PersonalDashboard/1.0 (jose.jose.alvarez@gmail.com)"  # Change to your real email
LAT, LON = 42.5378, -83.4810  # Walled Lake, MI
CITY = "Walled Lake, MI"

st.set_page_config(page_title="My Dashboard", layout="wide")

# ------------------ CACHED FETCH FUNCTIONS ------------------
@st.cache_data(ttl=300)  # 5 min cache
def get_nws_point():
    url = f"https://api.weather.gov/points/{LAT},{LON}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.json() if r.ok else None
    except:
        return None

@st.cache_data(ttl=300)
def get_nws_forecast(forecast_url):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    try:
        r = requests.get(forecast_url, headers=headers, timeout=10)
        return r.json() if r.ok else None
    except:
        return None

@st.cache_data(ttl=60)
def get_michigan_scores():
    today = datetime.now().strftime("%Y/%m/%d")
    url = f"https://ncaa-api.henrygd.me/scoreboard/football/fbs/{today}/all-conf"  # Start with football; we can add basketball/more
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.ok else []
        # Filter for Michigan games
        michigan_games = [g for g in data if 'michigan' in str(g).lower()]  # Simple keyword filter; improve later
        return michigan_games or data[:5]  # Show Michigan if any, else recent
    except:
        return []

@st.cache_data(ttl=300)
def get_top_news():
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("articles", [])[:8] if r.ok else []
    except:
        return []

@st.cache_data(ttl=60)
def get_markets():
    tickers = {"S&P 500": "^GSPC", "Dow": "^DJI", "Nasdaq": "^IXIC"}
    crypto = {"Bitcoin": "bitcoin", "Ethereum": "ethereum"}
    data = {}
    
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="2d")
            if len(df) >= 2:
                close = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                pct = (close - prev) / prev * 100
                data[name] = f"{close:,.2f} ({pct:+.2f}%)"
        except:
            pass
    
    try:
        cg = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true", timeout=5).json()
        for coin in crypto:
            info = cg.get(crypto[coin], {})
            data[coin] = f"${info.get('usd', 'N/A'):,.0f} ({info.get('usd_24h_change', 0):+.2f}%)"
    except:
        pass
    
    return data

# ------------------ MAIN APP ------------------
st.title("My Personal Dashboard – Jose")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')} | Location: {CITY} | Refresh for latest")

tab_weather, tab_sports, tab_news, tab_markets = st.tabs(["Weather (Milford)", "Michigan Wolverines", "Top News", "Markets"])

with tab_weather:
    st.subheader("Current Weather & Forecast")
    point = get_nws_point()
    if point and "properties" in point:
        forecast_url = point["properties"].get("forecast")
        forecast = get_nws_forecast(forecast_url) if forecast_url else None
        if forecast and "properties" in forecast:
            for period in forecast["properties"]["periods"][:8]:  # Next day or so
                name = period["name"]
                temp = f"{period['temperature']}°{period['temperatureUnit']}"
                wind = period["windSpeed"]
                short = period["shortForecast"]
                st.markdown(f"**{name}**: {short} — Temp {temp}, Wind {wind}")
        else:
            st.info("Forecast loading... or try refresh.")
        
        st.markdown("### Radar (NWS Public)")
        # Simple public NWS radar embed link (regional; adjust zoom if needed)
        radar_url = "https://radar.weather.gov/ridge/standard/CONUS_loop.gif"  # National loop; or find local
        st.image(radar_url, caption="National Radar Loop (updates frequently)", use_column_width=True)
        st.caption("For local Milford view, check https://radar.weather.gov/station/KDTX/ or NWS Detroit site.")
    else:
        st.error("Weather service temporarily unavailable. Refresh or check weather.gov.")

with tab_sports:
    st.subheader("University of Michigan Athletics")
    games = get_michigan_scores()
    if games:
        st.success("Found recent/upcoming Michigan-related games!")
        for g in games:
            st.markdown(f"- **{g.get('away', {}).get('name', 'TBD')} @ {g.get('home', {}).get('name', 'TBD')}**  \n{g.get('status', 'Status')} | {g.get('date', 'Date')}")
        st.caption("Data from public NCAA proxy. Shows football today; expand to basketball/news later.")
    else:
        st.warning("No games today or data issue. Check ncaa.com/scoreboard or refresh. Off-season? Try schedules tab later.")

with tab_news:
    st.subheader("Major National & International Headlines")
    articles = get_top_news()
    if articles:
        for a in articles:
            title = a.get("title", "No title")
            desc = a.get("description", "")
            src = a.get("source", {}).get("name", "Unknown")
            link = a.get("url", "#")
            st.markdown(f"**{title}**  \n{desc}  \n*Source: {src}* — [Read full article]({link})")
    else:
        st.error("Couldn't load news. Double-check your NewsAPI key in the code.")

with tab_markets:
    st.subheader("Stocks & Crypto Snapshot")
    markets = get_markets()
    if markets:
        df = pd.DataFrame.from_dict(markets, orient="index", columns=["Current (Change)"])
        st.table(df.style.set_properties(**{'text-align': 'right'}))
    else:
        st.warning("Market data fetch failed. Refresh.")

st.markdown("---")
if st.button("🔄 Refresh Dashboard Now", type="primary"):
    st.rerun()

st.caption("Built with Streamlit • Data from NWS, NCAA public API, NewsAPI, yfinance, CoinGecko • Personal use only")
