# C-MAPSS source and integrity

All twelve raw files use the same source as the existing FD004 fallback:
https://github.com/PunVas/nasa-c-mapss/tree/2b562334f2114d9dadfc0861dededc16cf2550d9

FD001–FD003 were downloaded over verified HTTPS, then matched to the Git blob identities in that exact commit's tree fetched independently through Git. Existing FD004 bytes matched both their prior SHA-256 constants and the same tree. The frozen `cmapss-manifest.json` records byte counts, Git SHA-1 object identities and SHA-256 digests for every file. These checks establish pinned mirror integrity, not an independent NASA signature or certification. No expected checksum was changed to accept a mismatch.

From the repository root:

```bash
.venv/bin/python scripts/portfolio/download.py
```

Existing files are checked before reuse; mismatches fail and are not silently replaced. Missing files download from the pinned raw mirror and must match both recorded digests. Raw data stay ignored under `data/raw/CMAPSSData/`. The original NASA/FD004-specific helper remains for compatibility; the new downloader covers all four subsets. Train/test engine counts are FD001 100/100, FD002 260/259, FD003 100/100, FD004 249/248.
