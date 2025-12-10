# Cultural Asymmetry in LLMs

Analysis of cultural bias in Large Language Models using Logit Lens technique.

## 📁 Project Structure

```
cultural-asymmetry-llm/
├── scripts/          # Processing and evaluation scripts
│   └── gen_dataset/  # Dataset generation utilities
├── data/            # Datasets and ground truth CSVs
├── results/         # Model evaluation results
└── requirements.txt # Python dependencies
```

## 🎯 Main Dataset

The final dataset for Logit Lens analysis is **`data/subset_h2_completion.json`**:
- **259 items** in completion format
- **5 categories**: indigenous_peoples, dances, painters, movies, landmarks
- **100% accuracy** after manual validation

### Category Distribution:
- Indigenous Peoples: 58 items (22%)
- Dances: 46 items (18%)
- Painters: 28 items (11%)
- Movies: 97 items (37%)
- Landmarks: 30 items (12%)

## 🚀 Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Main scripts workflow:
   - `scripts/extraer_subset_desde_csv.py` - Extract entities from CSVs
   - `scripts/limpiar_subset.py` - Clean and validate dataset
   - `scripts/convertir_a_completion.py` - Convert to Logit Lens format

## 📊 Data Files

### Ground Truth CSVs (data/)
- `pueblos_indigenas_latam_4079Entities.csv`
- `danzas_por_pais_latam_1401Entities.csv`
- `pintores_latam_4671Entities.csv`
- `cine_latam_151363Entities.csv`
- `landmarks_LATAM_103493Entities.csv`

### Processed Datasets (data/)
- `subset_h2_completion.json` - **Main dataset** (Logit Lens format)
- `subset_h2_limpio.json` - Cleaned QA format (68 entities)
- `subset_h2_final.json` - Raw extraction (110 entities)

### QA Datasets (data/)
- `justo_qa.json` (310K questions)
- `tomy_qa.json` (86K questions)
- `usa_qa.json` (16K questions)

## 📈 Evaluation Results

Model evaluations are stored in `results/`:
- Llama-3.1-8B-Instruct
- Qwen3-4B-Instruct-2507
- TinyLlama-1.1B-Chat-v1.0

## 📝 Documentation

See `RESUMEN_SUBSET_H2.md` for detailed process documentation.

## 📄 License

See LICENSE file for details.
