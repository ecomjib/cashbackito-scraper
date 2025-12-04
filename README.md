# Cashbackito Scraper V2

Scraper automatique des taux de cashback depuis :
- Poulpeo
- Widilo  
- iGraal
- eBuyClub

## Marchands (23)

| Catégorie | Marchands |
|-----------|-----------|
| Marketplace | AliExpress, Cdiscount, Rakuten |
| High-Tech | Fnac, Darty, Boulanger, Samsung |
| Mode | ASOS, SHEIN, Zalando, La Redoute, Showroomprivé |
| Sport | Nike, Adidas, Decathlon |
| Beauté | Sephora, Nocibé, Yves Rocher |
| Voyage | Booking, Expedia |
| Maison | IKEA, Maisons du Monde |
| Food | Uber Eats |

## GitHub Actions

Le scraper tourne automatiquement toutes les 2 heures via GitHub Actions.

### URL des données

```
https://raw.githubusercontent.com/ecomjib/cashbackito-scraper/main/data/cashback_rates.json
```

## Lancer manuellement

1. Aller sur l'onglet Actions du repo
2. Cliquer sur "Scrape Cashback Rates"
3. Cliquer sur "Run workflow"
