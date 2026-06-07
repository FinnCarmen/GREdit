# Data Layout

This repository keeps the expected `data/` directory layout so the provided scripts can run with minimal path editing.

What is intentionally not included:

- full pretrained TIGER checkpoints
- processed Amazon Reviews caches
- tensorboard logs and training outputs
- large generated edit artifacts

What is included:

- lightweight placeholder paths under `data/ckpt/`
- example request-file locations under `data/Edit/`
- plain-text or JSON placeholder files that preserve expected filenames but are not runnable artifacts

To reproduce the workflow, populate:

- `data/ckpt/TIGER_<category>/genrec_default_ori.pth`
- `data/cache/AmazonReviews2023/<category>/processed/`
- `data/Edit/<category>/edit_requests_*.json`

The scripts in `Scripts/` and the commands in the main `README.md` assume this layout.
