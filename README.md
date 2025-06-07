# eloverblik-solceller
Estimering af solcelle business case ud fra eloverblik data

Nu kan applikationen også estimere solcelleproduktion for en valgfri adresse i Danmark ved hjælp af data fra EU's PVGIS tjeneste.
Perioden for solcellevejret vælges nu med en separat datovælger i brugerfladen.

## Docker

Byg og kør applikationen i en Docker container:

```bash
# Byg billede
docker build -t eloverblik .

# Kør containeren på port 8050
docker run -p 8050:8050 eloverblik
```
