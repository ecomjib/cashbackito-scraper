# 🚀 Cashbackito - Comparateur de Cashback Automatisé

Un comparateur de cashback qui se met à jour **automatiquement toutes les heures** grâce à GitHub Actions. **100% gratuit.**

## ⚡ Comment ça marche ?

```
TOUTES LES HEURES (automatique) :

GitHub Actions se réveille
        ↓
Lance le scraper Python
        ↓
Va sur iGraal, Widilo, Poulpeo, eBuyClub
        ↓
Récupère les taux de tous les marchands
        ↓
Met à jour le fichier JSON
        ↓
Ton site affiche les nouveaux taux
```

## 📁 Fichiers du projet

```
cashbackito-scraper/
├── scraper.py                    # Script Python qui scrape les taux
├── data/
│   └── cashback_rates.json       # Données des taux (généré automatiquement)
├── .github/
│   └── workflows/
│       └── scrape.yml            # Configuration GitHub Actions
├── comparateur.html              # Frontend du comparateur
└── README.md                     # Ce fichier
```

## 🛠️ Installation

### Étape 1 : Créer le repository GitHub

1. Connecte-toi sur [github.com](https://github.com)
2. Clique sur **"+"** → **"New repository"**
3. Nom : `cashbackito-scraper`
4. Coche **"Public"**
5. Coche **"Add a README file"**
6. Clique **"Create repository"**

### Étape 2 : Ajouter les fichiers

**Option simple (interface web) :**

1. Dans ton repo, clique sur **"Add file"** → **"Upload files"**
2. Glisse-dépose tous les fichiers
3. Clique **"Commit changes"**

**Pour le dossier .github/workflows :**

1. Clique sur **"Add file"** → **"Create new file"**
2. Nom : `.github/workflows/scrape.yml`
3. Copie-colle le contenu du fichier scrape.yml
4. Clique **"Commit changes"**

### Étape 3 : Activer GitHub Actions

1. Va dans l'onglet **"Actions"** de ton repo
2. Clique sur **"I understand my workflows, go ahead and enable them"**
3. Clique sur **"🔄 Cashbackito - Mise à jour des taux"**
4. Clique **"Run workflow"** → **"Run workflow"**
5. Attends 2-3 minutes (tu verras une coche verte ✅)

### Étape 4 : Vérifier que ça marche

1. Retourne dans ton repo
2. Va dans le dossier `data/`
3. Ouvre `cashback_rates.json`
4. Tu devrais voir les taux récupérés !

## 🌐 Intégration WordPress

### Méthode 1 : Page HTML personnalisée

1. Dans WordPress, crée une nouvelle page
2. Ajoute un bloc **"HTML personnalisé"**
3. Copie-colle le contenu de `comparateur.html`
4. **Important** : Modifie la ligne `DATA_URL` avec ton username GitHub :
   ```javascript
   const DATA_URL = 'https://raw.githubusercontent.com/TON_USERNAME/cashbackito-scraper/main/data/cashback_rates.json';
   ```
5. Publie la page

### Méthode 2 : Shortcode (plus propre)

1. Ajoute ce code dans le fichier `functions.php` de ton thème :

```php
function cashbackito_shortcode() {
    ob_start();
    ?>
    <!-- Colle ici le contenu HTML du comparateur -->
    <?php
    return ob_get_clean();
}
add_shortcode('cashbackito', 'cashbackito_shortcode');
```

2. Utilise le shortcode `[cashbackito]` dans tes pages

## 💰 Monétisation

### Liens de parrainage

Remplace les URLs dans le fichier `comparateur.html` par tes liens de parrainage :

- **iGraal** : Crée un compte → Obtiens ton lien de parrainage
- **Widilo** : Crée un compte → Obtiens ton lien de parrainage  
- **Poulpeo** : Crée un compte → Obtiens ton lien de parrainage
- **eBuyClub** : Crée un compte → Obtiens ton lien de parrainage

### Revenus estimés

| Visiteurs/mois | Inscriptions (3%) | Revenus |
|----------------|-------------------|---------|
| 1 000 | 30 | 150€ |
| 5 000 | 150 | 750€ |
| 10 000 | 300 | 1 500€ |

## ➕ Ajouter des marchands

Modifie la liste `MERCHANTS` dans `scraper.py` :

```python
MERCHANTS = [
    ("Nom Affiché", "slug-url", "Catégorie", "🎁"),
    # Exemple :
    ("Aliexpress", "aliexpress", "Marketplace", "🛒"),
]
```

Le `slug-url` correspond à la partie de l'URL sur les sites de cashback.

## ⏰ Changer la fréquence

Modifie le fichier `.github/workflows/scrape.yml` :

```yaml
schedule:
  - cron: '0 * * * *'     # Toutes les heures
  - cron: '0 */2 * * *'   # Toutes les 2 heures
  - cron: '0 */6 * * *'   # Toutes les 6 heures
```

## 📊 Coût

**0€**

- GitHub Actions : 2000 minutes gratuites/mois
- GitHub Pages : Gratuit
- Le scraper prend ~2 min/heure = ~1440 min/mois

## ❓ FAQ

**Le scraping ne marche pas pour certains marchands ?**
Normal. Les sites changent leur structure HTML. Le scraper essaie plusieurs méthodes mais ne peut pas tout récupérer.

**Les taux sont faux ?**
Possible. Le scraping n'est pas parfait. Tu peux ajouter un bouton "Signaler une erreur" pour que tes utilisateurs te préviennent.

**GitHub Actions s'arrête ?**
Si ton repo est inactif pendant 60 jours, GitHub peut désactiver les Actions. Fais un commit de temps en temps.

---

**Fait avec ❤️ pour Cashbackito**
