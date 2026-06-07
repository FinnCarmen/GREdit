# GREdit

GREdit packages **GenRecEdit**, a model-editing workflow for **cold-start generative recommendation** built around the TIGER recommender. The repository is organized as a reproducible research codebase rather than a minimal library: it includes the base recommender, the edit algorithm, request generation utilities, and shell entrypoints for train, prepare, edit, and evaluate.

The workflow is:

1. train a base TIGER recommender on an Amazon Reviews category,
2. construct covariance and cold-start edit requests,
3. solve GenRecEdit updates,
4. re-run recommendation with the edited model and report metrics.

## What This Repository Contains

- `genrecedit/`: the GenRecEdit implementation, hyperparameters, covariance helpers, and CLI glue.
- `genrec/`: the generative recommendation stack used as the editable backbone.
- `prepare_edit_data.py`: reproducible request generation from cached TIGER data.
- `rec_main.py`: training and evaluation entrypoint for the recommender.
- `edit_main.py`: GenRecEdit entrypoint.
- `Scripts/`: ready-to-run shell wrappers for the full pipeline.
- `docs/data_preparation.md`: extra notes on request generation.
- `data/`: expected directory layout for checkpoints and edit requests.

## Repository Layout

```text
GREdit/
├── CITATION.cff
├── README.md
├── pyproject.toml
├── requirements.txt
├── rec_main.py
├── edit_main.py
├── prepare_edit_data.py
├── Scripts/
│   ├── rec_train.sh
│   ├── prepare_data.sh
│   └── edit.sh
├── docs/
│   └── data_preparation.md
├── data/
│   ├── README.md
│   ├── ckpt/
│   └── Edit/
├── genrec/
├── genrecedit/
├── util/
└── notebooks/
```

## Installation

### Option 1: Reproduce the original environment

```bash
conda create -n gredit python=3.10 -y
conda activate gredit
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` is the closest match to the environment used in this packaged codebase and includes the CUDA 12.4 wheel index for PyTorch.

### Option 2: Install as a package

If you prefer editable installs and CLI entrypoints:

```bash
conda create -n gredit python=3.10 -y
conda activate gredit
python -m pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -e .
```

This exposes:

- `gredit-train`
- `gredit-prepare`
- `gredit-edit`

## Supported Categories

The open-source scripts are currently wired for the categories already reflected in the repository data layout:

- `Video_Games`
- `Cell_Phones_and_Accessories`
- `Software`

`prepare_edit_data.py` also contains defaults for a few additional Amazon Reviews categories, but only the three above are reflected in the packaged examples and shell scripts.

## Expected Data Layout

The repository assumes the following paths:

```text
data/
├── ckpt/
│   └── TIGER_<category>/
│       └── genrec_default_ori.pth
├── cache/
│   └── AmazonReviews2023/
│       └── <category>/
│           └── processed/
│               └── sentence-t5-base.sent_emb
└── Edit/
    └── <category>/
        ├── edit_requests_COV.json
        └── edit_requests_cold_test_augmented_<n>.json
```

Important points:

- full pretrained checkpoints are not bundled here;
- processed TIGER caches are not bundled here;
- generated logs and tensorboard outputs are ignored by git;
- lightweight placeholder files may appear under `data/` to preserve the expected structure.

See [data/README.md](data/README.md) for a short summary.

## End-to-End Workflow

### 1. Train the base recommender

Train TIGER for one category:

```bash
bash Scripts/rec_train.sh Video_Games
```

Or with the package entrypoint:

```bash
gredit-train --model TIGER --category Video_Games --max_rows 0.5
```

The training stage is expected to produce:

```text
data/ckpt/TIGER_Video_Games/genrec_default_ori.pth
```

Category-dependent `max_rows` defaults inside `Scripts/rec_train.sh` are:

- `Video_Games`: `0.5`
- `Cell_Phones_and_Accessories`: `0.1`
- `Software`: `0.5`

### 2. Prepare edit requests

Generate the covariance requests and cold-start augmented edit requests:

```bash
bash Scripts/prepare_data.sh Video_Games
```

Or:

```bash
gredit-prepare \
  --category Video_Games \
  --number_per_item 10 \
  --topk 10 \
  --cache_dir data/cache/ \
  --output_dir data/Edit/Video_Games
```

This stage writes:

- `data/Edit/<category>/edit_requests_COV.json`
- `data/Edit/<category>/edit_requests_cold_test_augmented_<number_per_item>.json`

What the script does:

1. loads the processed TIGER dataset split,
2. tokenizes the training split into covariance requests,
3. detects target items from the requested split,
4. uses `sentence-t5-base.sent_emb` to retrieve similar train items,
5. rewrites train sequences to create cold-start edit cases,
6. tokenizes the augmented examples into GenRecEdit request format.

The request JSON entries contain:

- `history`: tokenized recommendation context
- `target_sids`: target semantic IDs
- `case_id`: string case identifier

### 3. Solve edits and evaluate

Run the edit pipeline:

```bash
bash Scripts/edit.sh Video_Games
```

By default the packaged script uses:

- `EDIT_POSTFIXES=(cold_test_augmented)`
- `COV_LAMBDAS=(1000)`
- `NUMBER_KNOWLEDGES=(10)`
- `POS2LAYER=(0 1 2 3)`

These can be overridden from the environment:

```bash
CUDA_VISIBLE_DEVICES=0 \
COV_LAMBDAS="1000 3000" \
NUMBER_KNOWLEDGES="5 10" \
POS2LAYER="0 1 2 3" \
bash Scripts/edit.sh Video_Games
```

The edit stage loads:

- `data/ckpt/TIGER_<category>/genrec_default_ori.pth`
- `data/Edit/<category>/edit_requests_COV.json`
- `data/Edit/<category>/edit_requests_cold_test_augmented_<n>.json`

It writes learned updates under:

```text
results/<category>/deltaW_edit_requests_cold_test_augmented_<cov_lambda>_<n>.pt
```

Then it reloads the base checkpoint, applies the learned `deltaW`, and evaluates the edited recommender.

## CLI Reference

### `rec_main.py`

Base training / evaluation entrypoint:

```bash
python rec_main.py --model TIGER --category Video_Games --max_rows 0.5
```

The script forwards unknown command-line flags to the GenRec configuration parser, so model-specific parameters can be injected from the command line.

### `prepare_edit_data.py`

Useful arguments:

- `--category`
- `--cache_dir`
- `--output_dir`
- `--pretrained_model_path`
- `--max_rows`
- `--topk`
- `--number_per_item`
- `--augmented_split`
- `--seed`
- `--no_write_cov`
- `--no_write_augmented`
- `--save_tokenized_augmented`

Example:

```bash
python prepare_edit_data.py \
  --category Cell_Phones_and_Accessories \
  --topk 10 \
  --number_per_item 10 \
  --augmented_split cold_test \
  --cache_dir data/cache/ \
  --output_dir data/Edit/Cell_Phones_and_Accessories
```

### `edit_main.py`

Useful arguments:

- `--model_name`
- `--pretrained_model_path`
- `--covariance_data_file`
- `--edit_requests_file`
- `--edit_name`
- `--category`
- `--cov_lambda`
- `--number_knowledge`
- `--pos2layer`
- `--cache_dir`
- `--output_dir`

Example:

```bash
python edit_main.py \
  --category Video_Games \
  --pretrained_model_path data/ckpt/TIGER_Video_Games/genrec_default_ori.pth \
  --covariance_data_file data/Edit/Video_Games/edit_requests_COV.json \
  --edit_requests_file data/Edit/Video_Games/edit_requests_cold_test_augmented_10.json \
  --edit_name edit_requests_cold_test_augmented \
  --cov_lambda 1000 \
  --number_knowledge 10 \
  --pos2layer 0 1 2 3
```

## Packaging Notes

This repository is now installable through `pyproject.toml`. The Python package includes:

- `genrecedit`
- `genrec`
- `util`
- packaged YAML configs under `genrec/`

That means downstream users can either run the shell scripts directly or install the project and invoke the CLI entrypoints from any working directory.

## Outputs

Typical generated artifacts:

```text
data/ckpt/TIGER_<category>/genrec_default_ori.pth
data/Edit/<category>/edit_requests_COV.json
data/Edit/<category>/edit_requests_cold_test_augmented_<n>.json
results/<category>/deltaW_*.pt
outputs/logs/
outputs/tensorboard/
```

`results/` and `outputs/` are intentionally git-ignored.

## Troubleshooting

### `FileNotFoundError: genrec_default_ori.pth`

The base TIGER checkpoint is missing. Train the recommender first or copy a checkpoint into:

```text
data/ckpt/TIGER_<category>/genrec_default_ori.pth
```

### Missing `sentence-t5-base.sent_emb`

The processed dataset cache is incomplete. Populate:

```text
data/cache/AmazonReviews2023/<category>/processed/sentence-t5-base.sent_emb
```

### Script runs only one category

Pass categories explicitly:

```bash
bash Scripts/prepare_data.sh Video_Games Software
bash Scripts/edit.sh Video_Games
```

or export:

```bash
export CATEGORIES="Video_Games Software"
```

### CUDA out of memory

Reduce batch-related settings in the model config, reduce the category sampling ratio, or use a larger GPU.

### Torch installation mismatch

If `pip install -e .` cannot find the correct CUDA wheels, install PyTorch first using the official wheel index, then reinstall the package.

## Research Notes and Limitations

- The codebase is research-oriented and still carries some project-specific assumptions.
- The primary reproducible path in this package is the TIGER-based cold-start workflow.
- Some auxiliary notebooks are preserved as research records rather than polished production utilities.
- Large pretrained weights and caches are not versioned in this repository.

## Citation

If this repository helps your research, please cite:

```bibtex
@article{shen2026bringing,
  title={Bringing Model Editing to Generative Recommendation in Cold-Start Scenarios},
  author={Shen, Chenglei and Shi, Teng and Yu, Weijie and Zhang, Xiao and Xu, Jun},
  journal={arXiv preprint arXiv:2603.14259},
  year={2026}
}
```
