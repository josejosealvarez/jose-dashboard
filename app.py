import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import yfinance as yf

# ------------------ CONFIG ------------------
NEWS_API_KEY = "YOUR_ACTUAL_NEWSAPI_KEY_HERE"  # Already set — don't change unless needed
USER_AGENT = "PersonalDashboard/1.0 (your.email@example.com)"  # Update to your email if you want
LAT, LON = 42.5378, -83.4811  # Walled Lake, MI
CITY = "Walled Lake, MI"

st.set_page_config(page_title="My Dashboard", layout="wide")

# ------------------ CACHED FETCH FUNCTIONS ------------------
@st.cache_data(ttl=300)  # 5 min
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
def get_ncaa_games(sport, division="d1"):
    today = datetime.now().strftime("%Y/%m/%d")
    url = f"https://ncaa-api.henrygd.me/scoreboard/{sport}/{division}/{today}/all-conf"
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.ok else []
        # Filter for Michigan games (home or away)
        michigan_games = []
        for g in data:
            away = g.get('away', {}).get('name', '').lower()
            home = g.get('home', {}).get('name', '').lower()
            if 'michigan' in away or 'michigan' in home or 'wolverines' in away or 'wolverines' in home:
                michigan_games.append(g)
        return michigan_games if michigan_games else data[:3]  # Michigan if any, else recent fallback
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

tab_weather, tab_sports, tab_news, tab_markets = st.tabs(["Weather (Walled Lake)", "Michigan Wolverines", "Top News", "Markets"])

with tab_weather:
    st.subheader("Current Weather & Forecast")
    point = get_nws_point()
    if point and "properties" in point:
        forecast_url = point["properties"].get("forecast")
        forecast = get_nws_forecast(forecast_url) if forecast_url else None
        if forecast and "properties" in forecast:
            for period in forecast["properties"]["periods"][:8]:
                name = period["name"]
                temp = f"{period['temperature']}°{period['temperatureUnit']}"
                wind = period["windSpeed"]
                short = period["shortForecast"]
                st.markdown(f"**{name}**: {short} — Temp {temp}, Wind {wind}")
        else:
            st.info("Forecast loading... or try refresh.")
        
        st.markdown("### Radar (NWS Detroit Local – Covers Walled Lake)")
        radar_url = "https://radar.weather.gov/ridge/standard/KDTX_loop.gif"  # Detroit radar covers Walled Lake well
        st.image(radar_url, caption="Detroit Radar Loop (refreshes often)", use_column_width=True)
        st.caption("Source: NWS KDTX – Walled Lake area radar.")
    else:
        st.error("Weather service temporarily unavailable. Refresh or check weather.gov.")

with tab_sports:
    st.subheader("University of Michigan Athletics Updates")
    
    # Football
    st.markdown("#### Football")
    fb_games = get_ncaa_games("football", "fbs")
    if fb_games:
        for g in fb_games:
            away = g.get('away', {}).get('name', 'TBD')
            home = g.get('home', {}).get('name', 'TBD')
            status = g.get('status', 'TBD')
            date_time = g.get('date', 'TBD')
            st.markdown(f"- **{away} @ {home}** | {status} | {date_time}")
    else:
        st.info("No recent football data or off-season. Check ncaa.com.")
    
    # Men's Basketball
    st.markdown("#### Men's Basketball")
    bb_games = get_ncaa_games("basketball-men")
    if bb_games:
        for g in bb_games:
            away = g.get('away', {}).get('name', 'TBD')
            home = g.get('home', {}).get('name', 'TBD')
            status = g.get('status', 'TBD')
            date_time = g.get('date', 'TBD')
            st.markdown(f"- **{away} @ {home}** | {status} | {date_time}")
    else:
        st.info("No men's basketball games today or data issue. Try refresh or check ncaa.com.")
    
    # Women's Basketball
    st.markdown("#### Women's Basketball")
    wbb_games = get_ncaa_games("basketball-women")
    if wbb_games:
        for g in wbb_games:
            away = g.get('away', {}).get('name', 'TBD')
            home = g.get('home', {}).get('name', 'TBD')
            status = g.get('status', 'TBD')
            date_time = g.get('date', 'TBD')
            st.markdown(f"- **{away} @ {home}** | {status} | {date_time}")
    else:
        st.info("No women's basketball games today or data issue. Try refresh or check ncaa.com/scoreboard/basketball-women/d1.")
    
    # Men's Hockey
    st.markdown("#### Men's Hockey")
    hk_games = get_ncaa_games("icehockey-men")
    if hk_games:
        for g in hk_games:
            away = g.get('away', {}).get('name', 'TBD')
            home = g.get('home', {}).get('name', 'TBD')
            status = g.get('status', 'TBD')
            date_time = g.get('date', 'TBD')
            st.markdown(f"- **{away} @ {home}** | {status} | {date_time}")
    else:
        st.info("No hockey games today or off-season. Check ncaa.com/scoreboard/icehockey-men/d1.")

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
        st.error("Couldn't load news. Check API key.")

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

st.caption("Data: NWS (weather), ncaa-api.henrygd.me (sports), NewsAPI, yfinance/CoinGecko • Personal use")
