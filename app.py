import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import yfinance as yf

# ------------------ CONFIG ------------------
NEWS_API_KEY = "YOUR_ACTUAL_NEWSAPI_KEY_HERE"  # Keep as-is
USER_AGENT = "PersonalDashboard/1.0 (your.email@example.com)"
LAT, LON = 42.5378, -83.4811  # Walled Lake, MI
CITY = "Walled Lake, MI"

st.set_page_config(page_title="My Dashboard", layout="wide")

# ------------------ CACHED FETCH FUNCTIONS ------------------
@st.cache_data(ttl=300)
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
def get_ncaa_games(sport, division="d1", date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y/%m/%d")
    url = f"https://ncaa-api.henrygd.me/scoreboard/{sport}/{division}/{date_str}/all-conf"
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.ok else []
        michigan_games = [g for g in data if 'mich' in str(g).lower()]  # Broader filter: mich, michigan, wolverines
        return michigan_games if michigan_games else data[:5]
    except:
        return []

@st.cache_data(ttl=3600)  # Longer cache for schedule
def get_ncaa_schedule(sport, division="d1", year=None):
    if year is None:
        year = datetime.now().strftime("%Y")
    url = f"https://ncaa-api.henrygd.me/schedule/{sport}/{division}/{year}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json() if r.ok else []
        # Filter upcoming Michigan games (simple: future dates with 'mich')
        upcoming = [g for g in data if 'mich' in str(g).lower() and 'date' in g and g['date'] > datetime.now().isoformat()]
        return upcoming[:5]  # Top 5 upcoming
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
        for coin, info in cg.items():
            data[coin.capitalize()] = f"${info['usd']:,.0f} ({info['usd_24h_change']:+.2f}%)"
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
                st.markdown(f"**{period['name']}**: {period['shortForecast']} — Temp {period['temperature']}°{period['temperatureUnit']}, Wind {period['windSpeed']}")
        else:
            st.info("Forecast loading... or try refresh.")
        
        st.markdown("### Radar (NWS Detroit Local – Covers Walled Lake)")
        radar_url = "https://radar.weather.gov/ridge/standard/KDTX_loop.gif"
        st.image(radar_url, caption="Detroit Radar Loop (refreshes often)", width=600, use_column_width=False)  # Smaller size!
        st.caption("Source: NWS KDTX – resized for better fit.")
    else:
        st.error("Weather unavailable. Refresh or check weather.gov.")

with tab_sports:
    st.subheader("University of Michigan Athletics Updates")
    
    today_str = datetime.now().strftime("%Y/%m/%d")
    
    def display_section(title, sport, div, is_schedule_fallback=False):
        st.markdown(f"#### {title}")
        games = get_ncaa_games(sport, div, today_str)
        st.caption(f"Fetched {len(games)} games today for {sport}")
        if games:
            for g in games:
                away = g.get('away', {}).get('name', 'TBD')
                home = g.get('home', {}).get('name', 'TBD')
                status = g.get('status', 'TBD')
                date_time = g.get('date', 'TBD')
                st.markdown(f"- **{away} @ {home}** | {status} | {date_time}")
        else:
            st.info(f"No games today for {title}.")
            if not is_schedule_fallback:
                upcoming = get_ncaa_schedule(sport, div)
                if upcoming:
                    st.markdown("**Upcoming games (next few):**")
                    for u in upcoming:
                        st.markdown(f"- {u.get('date', 'TBD')}: {u.get('away', {}).get('name', 'TBD')} @ {u.get('home', {}).get('name', 'TBD')}")
                else:
                    st.info("No upcoming schedule data. Check ncaa.com directly.")

    display_section("Football", "football", "fbs")
    display_section("Men's Basketball", "basketball-men", "d1")
    display_section("Women's Basketball", "basketball-women", "d1")
    display_section("Men's Hockey", "icehockey-men", "d1")

with tab_news:
    st.subheader("Major National & International Headlines")
    articles = get_top_news()
    if articles:
        for a in articles:
            st.markdown(f"**{a.get('title')}**  \n{a.get('description')}  \n*Source: {a.get('source', {}).get('name')}* — [Read]({a.get('url')})")
    else:
        st.error("News load failed. Check API key.")

with tab_markets:
    st.subheader("Stocks & Crypto Snapshot")
    markets = get_markets()
    if markets:
        df = pd.DataFrame.from_dict(markets, orient="index", columns=["Current (Change)"])
        st.table(df.style.set_properties(**{'text-align': 'right'}))
    else:
        st.warning("Markets unavailable. Refresh.")

st.markdown("---")
if st.button("🔄 Refresh Dashboard Now", type="primary"):
    st.rerun()

st.caption("Sports via free ncaa-api.henrygd.me (best free option) • Other data: NWS, NewsAPI, yfinance/CoinGecko")
