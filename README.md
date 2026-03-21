# ExoDiscovery-Benchmark

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Models](https://img.shields.io/badge/Models-Qwen3--8B%20%7C%20Gemini%202.5%20Flash-purple)
![Data](https://img.shields.io/badge/Data-NASA%20PSCompPars%20%7C%20HWC-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**ExoDiscovery-Benchmark** is a benchmark for assessing Large Language Model (LLM) performance on exoplanet habitability classification using real NASA tabular data. It measures both classification accuracy and borderline reasoning ability.

---

## Overview

Can LLMs reason reliably over structured astrophysics data? This benchmark evaluates two frontier models on binary exoplanet habitability classification.

Key contributions:
- A curated habitability classification dataset derived from **NASA's Planetary Systems Composite Parameters (PSCompPars)** catalog and the **Habitable Worlds Catalog (HWC)**
- Two evaluation metrics: **classification accuracy** and **flip consistency rate**
- Comparative analysis of **Qwen3-8B** and **Gemini 2.5 Flash** on zero-shot tabular reasoning

---

## Dataset

| Source | Description |
|---|---|
| [NASA PSCompPars](https://exoplanetarchive.ipac.caltech.edu/) | Composite planetary and stellar information for confirmed exoplanets |
| [Habitable Worlds Catalog (HWC)](https://phl.upr.edu/hwc) | Curated list of potentially habitable exoplanets; this benchmark uses the conservative samples |

Habitability labels are derived from HWC membership. Each sample consists of a set of tabular exoplanet features, provided as structured table-form input to the model.

> **Note:** All samples used to evaluate classification accuracy correspond to real confirmed exoplanet entries in the NASA archive. Synthetic data is used for evaluating flip consistency rate to specifically test for reasoning examples at classification borderlines.

---

## Models

| Model | Provider | Parameters | Access |
|---|---|---|---|
| Qwen3-8B | Alibaba Cloud | 8B | Open-weight |
| Gemini 2.5 Flash | Google DeepMind | — | API |

Both models are evaluated in a **zero-shot** setting with no fine-tuning or task-specific prompting beyond the classification instruction.

---

## Metrics

### Classification Accuracy
Standard binary accuracy over the full evaluation set, comparing model predictions against HWC-derived ground truth labels.

### Flip Consistency
A measure of output stability: given the same input presented across multiple independent inference calls, how often does a model produce the same prediction? Lower flip rates indicate more reliable reasoning over tabular inputs.

```
flip_rate = (# inputs where model output changed across runs) / (total inputs)
consistency = 1 - flip_rate
```

---

## Results

| Model | Accuracy | Flip Consistency |
|---|---|---|
| Qwen3-8B | 0.917 | 0.083 |
| Gemini 2.5 Flash | 0.967 | 1.000 |

---

## Usage

### Requirements

```bash
pip install -r requirements.txt
```


### Running the Benchmark
 
Two notebooks are provided, one per model:
 
| Notebook | Model |
|---|---|
| `exodiscover_benchmark_qwen.ipynb` | Qwen3-8B |
| `exodiscover_benchmark_gemini.ipynb` | Gemini 2.5 Flash |
 
**To run on Google Colab:**
1. Open the notebook in Colab
2. Upload the required data files from `data/` to the Colab runtime when prompted
3. Run all cells in order
 
**Required data files** (both notebooks):
 
```
data/PSCompPars.csv
data/hwc_table_all.csv
data/hwc_table_conservative.csv
data/borderline_12.csv
data/borderline_12_modified.csv
data/part1_grouped_dataset.csv
```
 
> API keys for Gemini are required to run `exodiscover_benchmark_gemini.ipynb`. Set your key as an environment variable or in the Colab secrets manager before running.

---

## Acknowledgments

This project uses data from the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) and the [Habitable Worlds Catalog](https://phl.upr.edu/hwc). 

This work was conducted with the assistance of AI tools (Claude, Gemini) for writing support and code generation. All scientific decisions, methodology, and conclusions are the author's own.

---

## License

MIT License. See [`LICENSE`](./LICENSE) for details.
