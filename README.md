<p align="center">
  <a href="https://fusionproxy.net/?utm_source=github&utm_medium=scrape-html-tables-python">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-dark.png">
      <img src="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-light.png" alt="Fusion Proxy" height="52">
    </picture>
  </a>
</p>

# How to scrape HTML tables with Python (pandas and BeautifulSoup)

Tables are the easiest data to scrape: rows and columns are already there. `pandas.read_html` turns every `<table>` on a page into a DataFrame in one line; BeautifulSoup gives you full control when you need links, attributes or odd markup. [`scrape_tables.py`](scrape_tables.py) does both on Wikipedia's [list of countries by population](https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population).

```bash
pip install -r requirements.txt
python scrape_tables.py
```

```
pandas: 241 rows, columns: ['Location', 'Population', '% of world', 'Date']
     Location   Population % of world        Date
        World 8232000000.0       100% 13 Jun 2025
        India 1429404000.0      17.3%  1 Jul 2026
        China 1404890000.0      17.0% 31 Dec 2025
...
BeautifulSoup: 240 rows, first: {'location': 'India', 'wiki_link': 'https://en.wikipedia.org/wiki/Demographics_of_India', 'population': 1429404000}
```

## 1. pandas.read_html

```python
from io import StringIO
import pandas as pd
import requests

html = requests.get(url, headers={"User-Agent": "my-scraper/1.0 (me@example.com)"}, timeout=30).text
tables = pd.read_html(StringIO(html), match="Population")   # only tables containing this text
df = tables[0]
df.to_csv("population.csv", index=False)
```

- Download the page with `requests` and pass the HTML to pandas. `pd.read_html(url)` also works, but then you cannot set a User-Agent, a timeout or a proxy, and many sites (Wikipedia included) refuse the default Python client.
- Wrap the HTML in `StringIO`: newer pandas versions warn when you pass a literal HTML string.
- `match=` picks tables by text; `attrs={"id": "..."}` picks by HTML attribute.
- `read_html` needs `lxml` (or `html5lib` with BeautifulSoup) installed.

## 2. Clean the result

Real tables come with footnotes, thousands separators and multi-row headers:

```python
# multi-row headers become tuples: flatten them
df.columns = [" ".join(map(str, c)).strip() if isinstance(c, tuple) else str(c) for c in df.columns]

# drop footnote markers like [a] or [12]
df[col] = df[col].astype(str).str.replace(r"\[[^\]]*\]", "", regex=True).str.strip()

# "1,234,567" to a number (read_html often parses numbers already, so check first)
if not pd.api.types.is_numeric_dtype(df[col]):
    df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")
```

## 3. BeautifulSoup for full control

`read_html` keeps only the text of each cell. When you need the link inside a cell, a `data-` attribute, or the table markup is too irregular, walk it yourself:

```python
table = soup.select_one("table.wikitable")
for tr in table.select("tr")[1:]:
    cells = tr.find_all(["td", "th"])
    link = cells[0].find("a", href=True)
    rows.append({
        "name": cells[0].get_text(" ", strip=True),
        "link": urljoin(url, link["href"]) if link else "",
        "value": cells[1].get_text(strip=True),
    })
```

Use `urljoin` for links: Wikipedia, like many sites, uses relative `href`s such as `./India`.

## When the table is not in the HTML

If the browser shows a table but `read_html` finds none, the page builds it with JavaScript. The data is usually in an inline script or a JSON API the page calls: see [scrape-javascript-website](https://github.com/FusionProxies/scrape-javascript-website).

## Proxy

With `FUSION_USER` and `FUSION_PASS` set, the download goes through a residential proxy. Useful when you collect tables from many pages of one site, or need the version of a page shown in another country.

## Related

- [python-web-scraping](https://github.com/FusionProxies/python-web-scraping): requests + BeautifulSoup basics
- [scrape-sitemap-python](https://github.com/FusionProxies/scrape-sitemap-python): get every URL of a site first

[Fusion Proxy residential proxies](https://fusionproxy.net/proxies/residential?utm_source=github&utm_medium=scrape-html-tables-python) from $2.95/GB, with a [free trial](https://fusionproxy.net/free-trial?utm_source=github&utm_medium=scrape-html-tables-python).

## License

MIT, see [LICENSE](LICENSE).
