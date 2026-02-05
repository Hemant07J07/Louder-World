import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests
from .utils import parse_datetime


def fetch_url(url, timeout=20, headers=None):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (compatible; EventScraper/1.0)"
    }
    if headers:
        default_headers.update(headers)
    resp = requests.get(url, headers=default_headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _first_text(tag):
    if not tag:
        return None
    txt = tag.get_text(" ", strip=True)
    return txt or None


def _abs_url(base_url: str, href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(base_url.rstrip("/") + "/", href)


def _extract_overview_text(soup: BeautifulSoup) -> str | None:
    overview_heading = soup.find(
        lambda t: t.name in {"h2", "h3"} and t.get_text(strip=True).lower() == "overview"
    )
    if not overview_heading:
        return None

    parts: list[str] = []
    for sib in overview_heading.find_all_next():
        if sib == overview_heading:
            continue
        if sib.name in {"h2", "h3"}:
            break
        if sib.name == "p":
            txt = _first_text(sib)
            if txt:
                parts.append(txt)
        if len(" ".join(parts)) > 800:
            break
    joined = "\n\n".join(parts).strip()
    return joined or None


def _extract_first_image_url(soup: BeautifulSoup, prefer_contains: str | None = None) -> str | None:
    imgs = soup.find_all("img")
    for img in imgs:
        src = img.get("src")
        if not src:
            continue
        if prefer_contains and prefer_contains in src:
            return src
    for img in imgs:
        src = img.get("src")
        if src:
            return src
    return None


def _parse_date_range_start(text: str | None):
    if not text:
        return None
    cleaned = " ".join(text.split())
    if " to " in cleaned:
        cleaned = cleaned.split(" to ", 1)[0].strip()
    return parse_datetime(cleaned)


def parse_cityofsydney_event_detail(html: str, base_url: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = _first_text(soup.find("h1"))

    # Heuristic: the page text contains a clear "Where" and "When" block.
    page_text = soup.get_text("\n", strip=True)
    venue = None
    start_time = None

    # Venue: try to find the first venue link under the "Where" section.
    where_label = soup.find(string=lambda s: isinstance(s, str) and s.strip() == "Where")
    if where_label:
        container = where_label.parent
        venue_link = container.find_next("a") if container else None
        venue = _first_text(venue_link)

    # When: grab the date range line if present.
    m = re.search(r"\b([A-Za-z]+\s+\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+to\s+([A-Za-z]+\s+\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", page_text)
    if m:
        start_time = parse_datetime(m.group(1))

    description = None
    # The main content paragraphs usually appear after "Cost"; fall back to first few paragraphs.
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paragraphs = [p for p in paragraphs if p]
    if paragraphs:
        description = "\n\n".join(paragraphs[:3]).strip() or None

    image_url = _extract_first_image_url(soup)

    return {
        "title": title,
        "start_time": start_time,
        "venue": venue,
        "description": description,
        "image_url": image_url,
        "source_url": source_url,
    }


def parse_cityofsydney_whats_on_listing(html: str, base_url: str, max_items: int = 20):
    soup = BeautifulSoup(html, "html.parser")

    # Collect distinct event detail URLs.
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.startswith("/events/"):
            continue
        full = _abs_url(base_url, href)
        if full and full not in urls:
            urls.append(full)
        if len(urls) >= max_items:
            break

    items = []
    for url in urls:
        try:
            detail_html = fetch_url(url)
            items.append(parse_cityofsydney_event_detail(detail_html, base_url, url))
        except Exception:
            # Skip bad pages but keep overall scrape going.
            continue
    return items


def parse_sydneycom_event_detail(html: str, base_url: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = _first_text(soup.find("h1"))
    overview = _extract_overview_text(soup)

    page_text = soup.get_text("\n", strip=True)

    # Date range on detail pages looks like: Fri 06 Feb '26 – Sat 28 Feb '26
    start_time = None
    m = re.search(
        r"\b([A-Za-z]{3}\s+\d{2}\s+[A-Za-z]{3}\s+'\d{2})\s*[–-]\s*([A-Za-z]{3}\s+\d{2}\s+[A-Za-z]{3}\s+'\d{2})\b",
        page_text,
    )
    if m:
        start_time = parse_datetime(m.group(1))

    # Venue/address: try to use the "Location" section.
    venue = None
    loc_heading = soup.find(
        lambda t: t.name in {"h2", "h3"} and t.get_text(strip=True).lower() == "location"
    )
    if loc_heading:
        # First non-empty line after the heading.
        for sib in loc_heading.find_all_next():
            if sib == loc_heading:
                continue
            if sib.name in {"h2", "h3"}:
                break
            txt = _first_text(sib)
            if txt and txt.lower() not in {"get directions", "open in a new window"}:
                venue = txt
                break

    image_url = _extract_first_image_url(soup, prefer_contains="assets.atdw-online.com.au")

    return {
        "title": title,
        "start_time": start_time,
        "venue": venue,
        "description": overview,
        "image_url": image_url,
        "source_url": source_url,
    }


def parse_sydneycom_events_listing(html: str, base_url: str, max_items: int = 20):
    soup = BeautifulSoup(html, "html.parser")

    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "/events/" not in href:
            continue
        if href.startswith("/" ):
            full = _abs_url(base_url, href)
        elif href.startswith("http"):
            full = href
        else:
            full = _abs_url(base_url, href)
        if not full:
            continue
        # keep it on sydney.com
        if "sydney.com/" not in full:
            continue
        if full not in urls:
            urls.append(full)
        if len(urls) >= max_items:
            break

    items = []
    for url in urls:
        try:
            detail_html = fetch_url(url)
            items.append(parse_sydneycom_event_detail(detail_html, base_url, url))
        except Exception:
            continue
    return items

def parse_generic_event_page(html, base_url):
    """
    Example: given HTML for a listing page, return list of dicts:
    { title, start_time, venv, description, image_url, source_url}
    You must adapt the CSS selector per site
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select(".event-card"):
        title = card.select_one(".event-title")
        title = title.get_text(strip=True) if title else None

        time = card.select_one(".event-time")
        start_time = parse_datetime(time.get_text(strip=True)) if time else None

        venue = card.select_one(".event-venue")
        venue = venue.get_text(strip=True) if venue else None

        desc = card.select_one(".event-desc")
        desc = desc.get_text(strip=True) if desc else None

        a = card.select_one("a.event-link")
        source_url = a["href"] if a and a.has_attr("href") else None
        if source_url and source_url.startswith("/"):
            source_url = base_url.rstrip("/") + source_url

        img = card.select_one("img")
        image_url = img["src"] if img and img.has_attr("src") else None

        items.append({
            "title": title,
            "start_time": start_time,
            "venue": venue,
            "description": desc,
            "image_url": image_url,
            "source_url": source_url
        })
    return items