# Vendored `watchtower_client`

This directory is a copy of `~/Documents/Code/watchtower/client/watchtower_client/` at the time it was last synced. It is vendored (not pip-installed) so deployment to any target — Railway, VPS, a teammate's laptop — works without path gymnastics or private package registries.

## How to update

If `watchtower_client` changes in the watchtower repo, refresh this copy:

```bash
cp ~/Documents/Code/watchtower/client/watchtower_client/*.py \
   ~/Documents/Code/land-finder/scraper/watchtower_client/
```

Then commit the refreshed files.

## Usage

```python
from scraper.watchtower_client import capture_exception, monitor
```

Requires these env vars to be set:

```
WATCHTOWER_SUPABASE_URL=https://tifisttkhfvgcahcjina.supabase.co
WATCHTOWER_SUPABASE_SERVICE_KEY=<service role key>
```

The library never raises — if Supabase is unreachable or credentials are missing, errors are silently dropped so the host application keeps running.
