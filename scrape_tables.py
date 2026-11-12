"""Scrape HTML tables with Python: pandas.read_html, and BeautifulSoup when you need more control.

    pip install -r requirements.txt
    python scrape_tables.py
"""
import os
import random
import re
from io import StringIO
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"
UA = "Mozilla/5.0 (compatible; table-scraper-tutorial/1.0; +https://github.com/FusionProxies/scrape-html-tables-python)"


def get_html(url: str) -> str:
    """Download with requests (custom User-Agent, timeout, optional proxy), then hand the HTML to pandas."""
    proxies = {}
    user, password = os.environ.get("FUSION_USER"), os.environ.get("FUSION_PASS")
    if user and password:
        sid = random.randint(1000000, 9999999)
        p = f"http://{user}-country-us-sessid-{sid}-sessTime-600s:{password}@resi.fusionproxy.net:12286"
        proxies = {"http": p, "https": p}
    r = requests.get(url, headers={"User-Agent": UA}, proxies=proxies, timeout=30)
    r.raise_for_status()
    return r.text


def with_pandas(html: str) -> pd.DataFrame:
    # match= keeps only tables whose text contains this string
    tables = pd.read_html(StringIO(html), match="Population")
    df = tables[0]
    df.columns = [" ".join(map(str, c)).strip() if isinstance(c, tuple) else str(c) for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    # clean: drop footnote markers like [a] and turn "1,234,567" into numbers
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(str).str.replace(r"\[[^\]]*\]", "", regex=True).str.strip()
    pop_col = next(c for c in df.columns if "Population" in c)
    if not pd.api.types.is_numeric_dtype(df[pop_col]):  # read_html often parses numbers already
        df[pop_col] = pd.to_numeric(df[pop_col].str.replace(",", ""), errors="coerce")
    return df


def with_beautifulsoup(html: str) -> list[dict]:
    """Manual parsing: keeps links and works when read_html cannot (odd markup, data in attributes)."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.wikitable")
    headers = [th.get_text(" ", strip=True) for th in table.select("tr th")][:3]
    rows = []
    for tr in table.select("tr")[1:]:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 3:
            continue
        # the country's article link (skip flag images and footnotes); hrefs can be relative
        link = next((a for a in cells[0].find_all("a", href=True) if "File:" not in a["href"] and not a["href"].startswith("#")), None)
        rows.append({
            "location": cells[0].get_text(" ", strip=True),
            "wiki_link": urljoin(URL, link["href"]) if link else "",
            "population": int(re.sub(r"[^\d]", "", cells[1].get_text()) or 0),
        })
    print("BeautifulSoup headers:", headers)
    return rows


if __name__ == "__main__":
    html = get_html(URL)

    df = with_pandas(html)
    print(f"pandas: {len(df)} rows, columns: {list(df.columns)[:4]}")
    print(df.head(5).to_string(index=False))
    df.to_csv("population.csv", index=False)

    rows = with_beautifulsoup(html)
    print(f"\nBeautifulSoup: {len(rows)} rows, first: {rows[1]}")
