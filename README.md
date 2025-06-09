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

### DMI cache

Set `DMI_START_CACHE_DATE` to the first date (YYYY-MM-DD) you wish to
cache weather observations from the DMI API. Optionally configure
`DMI_API_KEY` and `DMI_API_URL` if needed. The application will check
the cache every hour and download missing days automatically.

The PV date picker uses the cached range starting from `DMI_START_CACHE_DATE`,
based on the actual files in the cache, so only dates present there can be
selected.
