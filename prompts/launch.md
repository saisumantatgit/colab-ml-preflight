# colab-ml-preflight: Launch (Deploy) Prompt

You are deploying an ML notebook to Google Colab. Colab has NO push command — deployment is manual.

## Pre-Run Validation
1. Mount Drive: `drive.mount('/content/drive')`
2. Verify data files exist at expected paths
3. Verify Colab Secrets (HF_TOKEN) if using gated models
4. Select correct runtime: T4 (free), L4 (pro), A100 (pro+)

## Deployment Methods
- **Drive**: Upload .ipynb to Drive > Open with Colab
- **GitHub**: `https://colab.research.google.com/github/{user}/{repo}/blob/{branch}/{path}.ipynb`
- **gdown**: `!gdown URL` for downloading data from Drive share links

## Post-Launch
1. Verify GPU is allocated (not CPU fallback)
2. Verify Drive mount persists
3. If error: invoke blackbox triage
4. If running: monitor with in-notebook heartbeats
