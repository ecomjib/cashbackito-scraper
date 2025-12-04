#!/usr/bin/env python3
"""
Cashbackito Scraper V4
Scrape les taux de cashback ET bons d'achat depuis Poulpeo, Widilo, eBuyClub
- Détecte 2 types d'offres : cashback (remboursement) et bon_achat (carte cadeau)
- Patterns robustes pour maximiser la couverture
- Structure JSON enrichie pour le comparateur
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

# Configuration des marchands
# (Nom, slug_poulpeo, slug_widilo, slug_ebuyclub, id_ebuyclub, categorie, emoji)
MERCHANTS = [
    # Marketplace
    ("AliExpress", "aliexpress", "aliexpress", "aliexpress", 6325, "Marketplace", "🛒"),
    ("Cdiscount", "cdiscount", "cdiscount", "cdiscount", 104, "Marketplace", "🏷️"),
    ("Rakuten", "rakuten", "rakuten", "rakuten", 305, "Marketplace", "🛍️"),
    
    # High-Tech
    ("Fnac", "fnac", "fnac", "fnac", 58, "High-Tech", "🎮"),
    ("Darty", "darty", "darty", "darty", 846, "High-Tech", "📺"),
    ("Boulanger", "boulanger", "boulanger", "boulanger", 993, "High-Tech", "🔌"),
    ("Samsung", "samsung", "samsung", "samsung", 4498, "High-Tech", "📱"),
    
    # Mode
    ("ASOS", "asos", "asos", "asos", 3419, "Mode", "👕"),
    ("SHEIN", "shein", "shein", "shein", 7494, "Mode", "👗"),
    ("Zalando", "zalando", "zalando", "zalando", 3601, "Mode", "👠"),
    ("La Redoute", "la-redoute", "la-redoute", "la-redoute", 56, "Mode", "🏠"),
    ("Showroomprive", "showroomprive", "showroomprive", "showroomprive", 1498, "Mode", "🛍️"),
    
    # Sport
    ("Nike", "nike", "nike", "nike", 1145, "Sport", "✔️"),
    ("Adidas", "adidas", "adidas", "adidas", 1356, "Sport", "⚽"),
    ("Decathlon", "decathlon", "decathlon", "decathlon", 880, "Sport", "🏃"),
    
    # Beauté
    ("Sephora", "sephora", "sephora", "sephora", 683, "Beaute", "💄"),
    ("Nocibe", "nocibe", "nocibe", "nocibe", 1863, "Beaute", "💅"),
    ("Yves Rocher", "yves-rocher", "yves-rocher", "yves-rocher", 117, "Beaute", "🌿"),
    
    # Voyage
    ("Booking", "booking", "booking-com", "booking-com", 972, "Voyage", "🏨"),
    ("Expedia", "expedia", "expedia", "expedia", 487, "Voyage", "✈️"),
    
    # Maison
    ("IKEA", "ikea", "ikea", "ikea", 6214, "Maison", "🪑"),
    ("Maisons du Monde", "maisons-du-monde", "maisons-du-monde", "maisons-du-monde", 1699, "Maison", "🏡"),
    
    # Food
    ("Uber Eats", "uber-eats", "uber-eats", "ubereats", 7099, "Food", "🍔"),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}


def extract_rates_from_text(text):
    """
    Extrait les taux de cashback ET bons d'achat d'un texte.
    Retourne un dict avec 'cashback' et 'bon_achat' (ou None si pas trouvé)
    """
    if not text:
        return {'cashback': None, 'bon_achat': None}
    
    text_lower = text.lower().replace(',', '.')
    result = {'cashback': None, 'bon_achat': None}
    
    # ========== PATTERNS CASHBACK ==========
    cashback_patterns = [
        # Patterns directs
        r'(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?cashback',           # "3.6% de cashback"
        r'cashback\s*(?:de\s+)?(\d+(?:\.\d+)?)\s*%',           # "cashback de 3.6%"
        r'jusqu.{0,5}(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?cashback', # "jusqu'à 3.6% de cashback"
        r'(\d+(?:\.\d+)?)\s*%\s*rembours',                      # "3.6% remboursés"
        r'rembours[ée]s?\s*(?:jusqu.{0,5})?\s*(\d+(?:\.\d+)?)\s*%',  # "remboursé jusqu'à 3.6%"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:de\s+)?cash\s*back',         # "3.6% de cash back"
        r'gagnez\s*(?:jusqu.{0,5})?\s*(\d+(?:\.\d+)?)\s*%',     # "gagnez jusqu'à 3.6%"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:en\s+)?cashback',            # "3.6% en cashback"
    ]
    
    for pattern in cashback_patterns:
        match = re.search(pattern, text_lower)
        if match:
            rate = float(match.group(1))
            if 0 < rate <= 20:  # Filtre taux aberrants
                result['cashback'] = rate
                break
    
    # ========== PATTERNS BONS D'ACHAT ==========
    bon_achat_patterns = [
        r'(\d+(?:\.\d+)?)\s*%\s*(?:sur\s+)?(?:les?\s+)?bons?\s*d.?achats?',  # "14% sur les bons d'achat"
        r'bons?\s*d.?achats?\s*(?:de\s+)?(\d+(?:\.\d+)?)\s*%',               # "bon d'achat de 14%"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:sur\s+)?(?:les?\s+)?cartes?\s*cadeaux?',  # "14% sur les cartes cadeaux"
        r'cartes?\s*cadeaux?\s*(?:de\s+)?(\d+(?:\.\d+)?)\s*%',               # "carte cadeau de 14%"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:sur\s+)?(?:les?\s+)?e-?cartes?',          # "14% sur les e-cartes"
        r'bon\s*achat\s*(\d+(?:\.\d+)?)\s*%',                                 # "bon achat 14%"
    ]
    
    for pattern in bon_achat_patterns:
        match = re.search(pattern, text_lower)
        if match:
            rate = float(match.group(1))
            if 0 < rate <= 25:  # Bons d'achat peuvent aller plus haut
                result['bon_achat'] = rate
                break
    
    return result


class CashbackScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.stats = {
            'pages_ok': 0,
            'pages_404': 0,
            'pages_error': 0,
            'cashback_found': 0,
            'bon_achat_found': 0,
        }
        
    def get_page_content(self, url, timeout=15):
        """Récupère le contenu d'une page et retourne (status, soup, meta_desc, title)"""
        try:
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            
            if resp.status_code == 404:
                return (404, None, None, None)
            if resp.status_code != 200:
                return (resp.status_code, None, None, None)
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # Extraire meta description
            meta_desc = ""
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                meta_desc = meta.get('content', '')
            
            # Extraire titre
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text()
            
            return (200, soup, meta_desc, title)
            
        except requests.exceptions.Timeout:
            return ('timeout', None, None, None)
        except Exception as e:
            return ('error', None, None, None)
    
    def scrape_poulpeo(self, slug):
        """Scrape Poulpeo - retourne dict avec cashback et bon_achat"""
        url = f"https://www.poulpeo.com/reductions-{slug}.htm"
        status, soup, meta_desc, title = self.get_page_content(url)
        
        if status != 200:
            return None
        
        self.stats['pages_ok'] += 1
        
        # Combiner meta + titre pour chercher les taux
        combined_text = f"{meta_desc} {title}"
        rates = extract_rates_from_text(combined_text)
        
        # Si pas trouvé dans meta/titre, chercher dans le body
        if not rates['cashback'] and not rates['bon_achat'] and soup:
            # Chercher dans les éléments spécifiques de Poulpeo
            rate_elements = soup.find_all(['span', 'div'], class_=re.compile(r'rate|cashback|percent', re.I))
            for elem in rate_elements[:5]:
                text = elem.get_text()
                found = extract_rates_from_text(text)
                if found['cashback']:
                    rates['cashback'] = found['cashback']
                    break
        
        if rates['cashback'] or rates['bon_achat']:
            return {
                'url': url,
                'cashback': rates['cashback'],
                'bon_achat': rates['bon_achat']
            }
        return None
    
    def scrape_widilo(self, slug):
        """Scrape Widilo - retourne dict avec cashback et bon_achat"""
        url = f"https://www.widilo.fr/code-promo/{slug}"
        status, soup, meta_desc, title = self.get_page_content(url)
        
        if status != 200:
            return None
        
        self.stats['pages_ok'] += 1
        
        # Combiner meta + titre
        combined_text = f"{meta_desc} {title}"
        rates = extract_rates_from_text(combined_text)
        
        # Widilo affiche souvent les taux dans les onglets (Cashback X% | Bon d'achat Y%)
        # On cherche ces patterns spécifiques
        if soup:
            # Chercher les onglets/boutons avec les taux
            tab_text = ""
            tabs = soup.find_all(['button', 'a', 'span', 'div'], 
                                 class_=re.compile(r'tab|filter|category', re.I))
            for tab in tabs[:10]:
                tab_text += " " + tab.get_text()
            
            if tab_text:
                found = extract_rates_from_text(tab_text)
                if found['cashback'] and not rates['cashback']:
                    rates['cashback'] = found['cashback']
                if found['bon_achat'] and not rates['bon_achat']:
                    rates['bon_achat'] = found['bon_achat']
        
        if rates['cashback'] or rates['bon_achat']:
            return {
                'url': url,
                'cashback': rates['cashback'],
                'bon_achat': rates['bon_achat']
            }
        return None
    
    def scrape_ebuyclub(self, slug, merchant_id):
        """Scrape eBuyClub - retourne dict avec cashback et bon_achat"""
        if not merchant_id:
            return None
        
        url = f"https://www.ebuyclub.com/reduction-{slug}-{merchant_id}"
        status, soup, meta_desc, title = self.get_page_content(url)
        
        if status != 200:
            return None
        
        self.stats['pages_ok'] += 1
        
        # eBuyClub format titre: "... + X% Cashback" ou "X% CashBack"
        combined_text = f"{meta_desc} {title}"
        rates = extract_rates_from_text(combined_text)
        
        # Pattern spécifique eBuyClub dans le titre
        if title:
            match = re.search(r'(\d+(?:[,.]\d+)?)\s*%\s*[Cc]ash[Bb]ack', title)
            if match and not rates['cashback']:
                rate = float(match.group(1).replace(',', '.'))
                if 0 < rate <= 20:
                    rates['cashback'] = rate
        
        if rates['cashback'] or rates['bon_achat']:
            return {
                'url': url,
                'cashback': rates['cashback'],
                'bon_achat': rates['bon_achat']
            }
        return None
    
    def scrape_merchant(self, merchant_data):
        """Scrape toutes les plateformes pour un marchand"""
        name, slug_p, slug_w, slug_eb, id_eb, category, emoji = merchant_data
        
        print(f"{emoji} {name}...", end=" ", flush=True)
        
        offers = []
        
        # Poulpeo
        result = self.scrape_poulpeo(slug_p)
        if result:
            if result['cashback']:
                offers.append({
                    "platform": "Poulpeo",
                    "type": "cashback",
                    "rate": result['cashback'],
                    "url": result['url']
                })
                self.stats['cashback_found'] += 1
            if result['bon_achat']:
                offers.append({
                    "platform": "Poulpeo",
                    "type": "bon_achat",
                    "rate": result['bon_achat'],
                    "url": result['url']
                })
                self.stats['bon_achat_found'] += 1
        time.sleep(0.3)
        
        # Widilo
        result = self.scrape_widilo(slug_w)
        if result:
            if result['cashback']:
                offers.append({
                    "platform": "Widilo",
                    "type": "cashback",
                    "rate": result['cashback'],
                    "url": result['url']
                })
                self.stats['cashback_found'] += 1
            if result['bon_achat']:
                offers.append({
                    "platform": "Widilo",
                    "type": "bon_achat",
                    "rate": result['bon_achat'],
                    "url": result['url']
                })
                self.stats['bon_achat_found'] += 1
        time.sleep(0.3)
        
        # eBuyClub
        result = self.scrape_ebuyclub(slug_eb, id_eb)
        if result:
            if result['cashback']:
                offers.append({
                    "platform": "eBuyClub",
                    "type": "cashback",
                    "rate": result['cashback'],
                    "url": result['url']
                })
                self.stats['cashback_found'] += 1
            if result['bon_achat']:
                offers.append({
                    "platform": "eBuyClub",
                    "type": "bon_achat",
                    "rate": result['bon_achat'],
                    "url": result['url']
                })
                self.stats['bon_achat_found'] += 1
        time.sleep(0.3)
        
        # Calculer les meilleurs taux
        cashback_offers = [o for o in offers if o['type'] == 'cashback']
        bon_achat_offers = [o for o in offers if o['type'] == 'bon_achat']
        
        best_cashback = max(cashback_offers, key=lambda x: x['rate']) if cashback_offers else None
        best_bon_achat = max(bon_achat_offers, key=lambda x: x['rate']) if bon_achat_offers else None
        
        # Résumé pour le log
        summary_parts = []
        if best_cashback:
            summary_parts.append(f"CB:{best_cashback['rate']}%/{best_cashback['platform']}")
        if best_bon_achat:
            summary_parts.append(f"BA:{best_bon_achat['rate']}%/{best_bon_achat['platform']}")
        
        if summary_parts:
            print(f"✅ {' | '.join(summary_parts)}")
        else:
            print("❌ Aucune offre")
        
        if offers:
            return {
                "name": name,
                "slug": slug_p,
                "category": category,
                "logo": emoji,
                "offers": offers,
                "best_cashback": {
                    "rate": best_cashback['rate'],
                    "platform": best_cashback['platform'],
                    "url": best_cashback['url']
                } if best_cashback else None,
                "best_bon_achat": {
                    "rate": best_bon_achat['rate'],
                    "platform": best_bon_achat['platform'],
                    "url": best_bon_achat['url']
                } if best_bon_achat else None,
                # Compatibilité avec l'ancien format
                "best_rate": best_cashback['rate'] if best_cashback else (best_bon_achat['rate'] if best_bon_achat else 0),
                "best_platform": best_cashback['platform'] if best_cashback else (best_bon_achat['platform'] if best_bon_achat else "")
            }
        else:
            return None
    
    def run(self):
        """Lance le scraping complet"""
        print("=" * 70)
        print("CASHBACKITO SCRAPER V4 - Cashback + Bons d'achat")
        print("=" * 70)
        print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Marchands: {len(MERCHANTS)}")
        print(f"Plateformes: Poulpeo, Widilo, eBuyClub")
        print("-" * 70)
        
        merchants_data = []
        no_offers = []
        
        for merchant in MERCHANTS:
            result = self.scrape_merchant(merchant)
            if result:
                merchants_data.append(result)
            else:
                no_offers.append(merchant[0])
        
        # Stats
        total_offers = sum(len(m.get('offers', [])) for m in merchants_data)
        merchants_with_cashback = sum(1 for m in merchants_data if m.get('best_cashback'))
        merchants_with_bon_achat = sum(1 for m in merchants_data if m.get('best_bon_achat'))
        
        output = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "last_updated_fr": datetime.now().strftime('%d/%m/%Y à %Hh%M'),
            "version": "4.0",
            "stats": {
                "merchants_total": len(MERCHANTS),
                "merchants_with_offers": len(merchants_data),
                "merchants_with_cashback": merchants_with_cashback,
                "merchants_with_bon_achat": merchants_with_bon_achat,
                "total_offers": total_offers,
                "platforms": ["Poulpeo", "Widilo", "eBuyClub"]
            },
            "merchants": merchants_data
        }
        
        # Sauvegarder
        output_dir = Path(__file__).parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "cashback_rates.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print("-" * 70)
        print("RÉSULTATS")
        print("-" * 70)
        print(f"📊 Marchands avec offres: {len(merchants_data)}/{len(MERCHANTS)}")
        print(f"💰 Avec cashback: {merchants_with_cashback}")
        print(f"🎁 Avec bons d'achat: {merchants_with_bon_achat}")
        print(f"📈 Total offres: {total_offers}")
        
        if no_offers:
            print(f"\n⚠️  Sans offre détectée: {', '.join(no_offers)}")
        
        # Stats par plateforme
        platform_stats = {}
        for m in merchants_data:
            for o in m.get('offers', []):
                key = f"{o['platform']}_{o['type']}"
                platform_stats[key] = platform_stats.get(key, 0) + 1
        
        print(f"\n📋 Par plateforme:")
        for key, count in sorted(platform_stats.items(), key=lambda x: -x[1]):
            platform, offer_type = key.rsplit('_', 1)
            type_label = "💰" if offer_type == "cashback" else "🎁"
            print(f"   {type_label} {platform}: {count}")
        
        print(f"\n✅ Fichier: {output_path}")
        
        return output


if __name__ == "__main__":
    scraper = CashbackScraper()
    scraper.run()
