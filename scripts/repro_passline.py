import os
from bs4 import BeautifulSoup
import re

# File name is tricky, so finding it dynamically
filename = "Passline - Líder en venta de entradas para eventos.html"
# Or just use the one I found
path = os.path.join(os.getcwd(), filename)

if not os.path.exists(path):
    print(f"File not found: {path}")
    # Try searching
    for f in os.listdir("."):
        if f.startswith("Passline") and f.endswith(".html"):
            path = f
            break

print(f"Reading {path}...")
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Select desktop cards
cards = soup.select("div.card.d-none.d-md-block")
print(f"Found {len(cards)} desktop cards.")

for i, card in enumerate(cards[:5]):
    print(f"--- Event {i+1} ---")
    
    # Title
    title_el = card.select_one("p.card-title")
    title = title_el.get_text(strip=True) if title_el else "No Title"
    print(f"Title: {title}")
    
    # Link
    link_el = card.select_one("a")
    link = link_el['href'] if link_el else "No Link"
    print(f"Link: {link}")
    
    # Venue
    venue_el = card.select_one("small.card-location")
    venue = venue_el.get_text(strip=True) if venue_el else "No Venue"
    print(f"Venue: {venue}")
    
    # Date
    date_div = card.select_one("div.event-date")
    if date_div:
        day = date_div.select_one(".fs-2").get_text(strip=True)
        month_year = date_div.select_one("span:nth-of-type(2)").get_text(strip=True)
        print(f"Date Raw: {day} {month_year}")
    
    # Time
    time_div = card.select_one("div.event-hours")
    if time_div:
        hour = time_div.select_one(".fs-2").get_text(strip=True)
        minute_unit = time_div.select_one("span:nth-of-type(2)").get_text(strip=True)
        print(f"Time Raw: {hour} {minute_unit}")

    # Image
    img = card.select_one("img")
    img_src = img['src'] if img else "No Image"
    # In local file this might be relative
    print(f"Image: {img_src}")
