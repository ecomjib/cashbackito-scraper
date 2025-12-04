#!/usr/bin/env python3
"""
Cashbackito Scraper DEBUG
Affiche le contenu exact des pages pour identifier les faux positifs
"""

import requests
from bs4 import BeautifulSoup
import time

MERCHANTS = [
    ("AliExpress", "aliexpress", "aliexpress", 6325),
    ("Cdiscount", "cdiscount", "cdiscount", 104),
    ("Rakuten", "rakuten", "rakuten", 305),
    ("Fnac", "fnac", "fnac", 58),
    ("Darty", "darty", "darty", 846),
    ("Boulanger", "boulanger", "boulanger", 993),
    ("Samsung", "samsung", "samsung", 4498),
    ("ASOS", "asos", "asos", 3419),
    ("SHEIN", "shein", "shein", 7494),
    ("Zalando", "zalando", "zalando", 3601),
    ("La Redoute", "la-redoute", "la-redoute", 56),
    ("Showroomprive", "showroomprive", "showroomprive", 1498),
    ("Nike", "nike", "nike", 1145),
    ("Adidas", "adidas", "adidas", 1356),
    ("Decathlon", "decathlon", "decathlon", 880),
    ("Sephora", "sephora", "sephora", 683),
    ("Nocibe", "nocibe", "nocibe", 1863),
    ("Yves Rocher", "yves-rocher", "yves-rocher", 117),
    ("Booking", "booking", "booking-com", 972),
    ("Expedia", "expedia", "expedia", 487),
    ("IKEA", "ikea", "ikea", 6214),
    ("Maisons du Monde", "maisons-du-monde", "maisons-du-monde", 1699),
    ("Uber Eats", "uber-eats", "uber-eats", 7099),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}

session = requests.Session()
session.headers.update(HEADERS)

def get_page_info(url):
    """Récupère les infos clés d'une page"""
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return {'status': resp.status_code, 'title': None, 'meta': None}
        
        soup = BeautifulSoup(resp.text, 'lxml')
        
        title = soup.find('title')
        title_text = title.get_text().strip() if title else None
        
        meta = soup.find('meta', {'name': 'description'})
        meta_text = meta.get('content', '').strip() if meta else None
        
        return {'status': 200, 'title': title_text, 'meta': meta_text}
    except Exception as e:
        return {'status': 'error', 'title': None, 'meta': str(e)}

print("=" * 100)
print("CASHBACKITO SCRAPER DEBUG - Contenu exact des pages")
print("=" * 100)

for name, slug_p, slug_w, id_eb in MERCHANTS:
    print(f"\n{'='*100}")
    print(f"🏪 {name.upper()}")
    print(f"{'='*100}")
    
    # POULPEO
    url_p = f"https://www.poulpeo.com/reductions-{slug_p}.htm"
    info_p = get_page_info(url_p)
    print(f"\n📗 POULPEO ({info_p['status']})")
    print(f"   URL: {url_p}")
    if info_p['title']:
        print(f"   TITLE: {info_p['title'][:150]}")
    if info_p['meta']:
        print(f"   META: {info_p['meta'][:200]}")
    time.sleep(0.3)
    
    # WIDILO
    url_w = f"https://www.widilo.fr/code-promo/{slug_w}"
    info_w = get_page_info(url_w)
    print(f"\n📙 WIDILO ({info_w['status']})")
    print(f"   URL: {url_w}")
    if info_w['title']:
        print(f"   TITLE: {info_w['title'][:150]}")
    if info_w['meta']:
        print(f"   META: {info_w['meta'][:200]}")
    time.sleep(0.3)
    
    # EBUYCLUB
    url_e = f"https://www.ebuyclub.com/reduction-{slug_p}-{id_eb}"
    info_e = get_page_info(url_e)
    print(f"\n📕 EBUYCLUB ({info_e['status']})")
    print(f"   URL: {url_e}")
    if info_e['title']:
        print(f"   TITLE: {info_e['title'][:150]}")
    if info_e['meta']:
        print(f"   META: {info_e['meta'][:200]}")
    time.sleep(0.3)
    
    # IGRAAL
    url_i = f"https://fr.igraal.com/codes-promo/{slug_p}"
    info_i = get_page_info(url_i)
    print(f"\n📘 IGRAAL ({info_i['status']})")
    print(f"   URL: {url_i}")
    if info_i['title']:
        print(f"   TITLE: {info_i['title'][:150]}")
    if info_i['meta']:
        print(f"   META: {info_i['meta'][:200]}")
    time.sleep(0.3)

print("\n" + "=" * 100)
print("FIN DEBUG")
print("=" * 100)
