# Smile Talk Web V1 — déploiement pilote

Cette application web mobile réutilise **sans dupliquer** l'évaluation pédagogique de `bot.py` et le corpus `SITUATIONS.csv`. La branche de production Telegram `main` n'est pas modifiée. Le site web n'est **pas encore hébergé** : ce dépôt contient le code à déployer.

## Déployer sur un service Render **distinct** du bot Telegram

1. Sur Render, créer **New > Web Service** relié au dépôt GitHub `Brindulos/smiletalk_bot`.
2. Sélectionner la branche **`feature/smiletalk-web-v1`**. **Ne pas changer la branche ni la commande de démarrage du service Telegram existant.**
3. Runtime : Python. Build Command : `pip install -r requirements-web.txt`.
4. Start Command : `gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT web_app:app`.
5. Ajouter les variables d'environnement (Render > Environment) :
   - `OPENAI_API_KEY` : clé API OpenAI valide (ne jamais placer dans le dépôt).
   - `SMILETALK_ACCESS_CODE` : code d'accès équipe, long et difficile à deviner, à transmettre uniquement aux agents autorisés.
   - `SMILETALK_SESSION_SECRET` : valeur aléatoire distincte du code d'accès, au moins 32 caractères. Exemple de génération : `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
   - `SMILETALK_MODEL` : modèle OpenAI autorisé compatible Chat Completions (par défaut `gpt-4o-mini` ; changer et tester avant toute date de retrait annoncée).
6. Lancer le service ; visiter l'URL Render en HTTPS. Ne pas diffuser le lien ou le code d'accès avant validation des tests.

## Tester avant diffusion

- Accès sans code : bloqué. Mauvais code : refus. Bon code : page d'accueil.
- Démarrer un exercice ; vérifier situation et relance issues du CSV.
- Soumettre deux réponses ; vérifier feedback, exemple et note /3.
- Tester une réponse **sans le mot « mais »** ; l'évaluation ne doit pas en inventer.
- Tester le cas d'insultes avec évocation pédagogique de la sécurité.
- Rafraîchir la page entre les deux réponses ; les étapes doivent rester cohérentes sur la même instance.
- Vérifier l'affichage sur iPhone, Android et desktop.
- Contrôler OpenAI Usage et fixer un plafond de dépense pour le projet si disponible.

## Limites intentionnelles de V1

- Aucun compte individuel, aucune statistique ni historique durable. Les données d'exercice sont conservées temporairement **en mémoire du serveur** (expiration après 2 h d'inactivité ; perdues au redémarrage du service).
- **Un seul worker Gunicorn** pour partager correctement les sessions temporaires ; plusieurs instances ne sont pas prises en charge dans cette version.
- Le code collectif est une barrière légère, pas une authentification individuelle. Éviter les données personnelles dans les réponses. Prévoir validation interne PSG / RGPD avant lancement large.
- Les limites locales d'usage protègent un pilote, mais ne remplacent pas le suivi de consommation ni une limite budgétaire côté OpenAI.
- Hébergement séparé = coût Render supplémentaire éventuel. Sur instance gratuite, un démarrage à froid peut ralentir la première visite.
- Les formulaires de la version web ne sont pas conçus comme une authentification forte. Le QR code renvoie vers le site, **sans inclure le code secret dans l'URL**.

## Usage

Accès depuis un smartphone via l'URL Render ; possible de créer un QR code vers cette URL après validation. La dictée est celle du clavier du téléphone (pas d'API audio facturée).
