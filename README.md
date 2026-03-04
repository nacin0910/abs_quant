# Absolute Quantification Pipeline for Microbial Metagenomics

A bioinformatics pipeline for the absolute quantification of microbial metagenomes. It takes raw FASTQ files as input, uses **Kneaddata** to remove human host contamination, applies **Kraken2** for taxonomic classification, and calculates **absolute microbial abundance** based on user‑provided spike‑in information and sample mass.

## 🚀 Quick Start

### 1. Installation

#### Via Conda

```bash
# Clone the repository
git clone https://github.com/nacin0910/abs_quant.git
cd abs_quant

# Create a conda environment
conda env create -f environment.yml
conda activate abs_quant

# Install the package
pip install -e .
```

### 2. Database Configuration

#### Option A: Download a new database

```bash
# Download and build all necessary databases
abs_quant build --threads 8 \
                --library bacteria archaea fungi viral \
                --db /path/to/database
```

#### Option B: Use existing databases

```bash
# If you already have Kraken2 and Kneaddata databases
abs_quant build --threads 8 \
                --kraken_db /path/to/kraken2_db \
                --kneaddata_db /path/to/kneaddata_db
```

### 3. Run Batch Analysis

The pipeline now includes a built‑in batch mode that processes all FASTQ files in a folder. It automatically recognizes paired‑end or single‑end files and resumes from where it left off if interrupted.

```bash
abs_quant batch --threads 8 \
                --kraken_db /path/to/kraken2_db \
                --kneaddata_db /path/to/kneaddata_db \
                --input /path/to/fastq_folder \
                --output results/ \
                --spikein_copies 4e7 \
                --sample_weight 1.0 \
                --read_threshold 10
```

> **Note:**  
> - `--spikein_copies` is the absolute number of spike‑in molecules added to the sample (e.g., `4e7`, `40M`, `40000000`).  
> - `--sample_weight` is the mass of the sample in grams (wet or dry weight).  
> - The pipeline automatically detects the read length from the FASTQ files, so you no longer need to provide `--read_length`.

## 📁 Output Files

After processing, you will obtain the following structure:

```
results/
├── merged_absolute_abundance.csv   # Combined absolute abundances for all samples (main output)
├── merged_relative_abundance.csv    # Combined relative abundances for all samples
├── sample1/
│   ├── kneaddata_out/               # Kneaddata intermediate files
│   ├── kraken_out/                   # Kraken2 and Bracken output
│   ├── sample1_abundance.csv         # Absolute abundance for this sample
│   └── sample1_relative_abundance.csv
├── sample2/
│   └── ...
└── ...
```

- **`merged_absolute_abundance.csv`** – rows represent species (with full taxonomic lineage), columns represent samples; values are **cells per gram**.
- **`merged_relative_abundance.csv`** – same format, but values are relative abundances (percentage).
- Each sample folder contains the same two CSV files for that individual sample, as well as all intermediate files from Kneaddata and Kraken2/Bracken.

## 🔄 Intelligent Resume Feature

If a previous run was interrupted, the pipeline automatically checks for existing output files:

- If **final abundance files** exist for a sample, the entire sample is skipped.
- If **Kraken2 `.kraken` and `.kreport` files** are present, it skips Kneaddata and runs only Bracken (if needed).
- If **Kneaddata output files** exist, it skips Kneaddata and proceeds directly to Kraken2.

This saves considerable time when re‑running incomplete batches or adding new samples to an existing analysis.

## 📊 Principle of Absolute Quantification

The pipeline calculates absolute abundances using the **ZymoBIOMICS Spike‑in Control I**, which contains two bacterial species with known genome sizes. The spike‑in molecules are added to the sample before DNA extraction.

| Bacterium | Taxonomy ID | Genome Size | Gram Stain |
|-----------|-------------|-------------|------------|
| *Allobacillus halotolerans* | 570278 | 2,700,297 bp | Positive |
| *Imtechella halotolerans*  | 1165090 | 3,113,111 bp | Negative |

**Calculation logic**:

1. **Read count to cells**  
   For a given species, the number of cells is estimated as:  
   `cell_num_x = (read_length * reads_x) / genome_size_x`

2. **Spike‑in reference**  
   The total spike‑in cells are the sum of the two spike‑in species:  
   `total_spikein_cells = cell_num_AH + cell_num_IH`

3. **Absolute abundance (cells/g)**  
   `abundance_x = (cell_num_x / total_spikein_cells) * spikein_copies / sample_weight`

- If the spike‑in abundance is too low (<0.1%), the pipeline issues a warning and outputs only relative abundances.
- For species missing in the genome information table (`gram_size_table.csv`), absolute abundance is left blank.

## ⚙️ Command Line Options

### Global Options

```bash
abs_quant --help
```

### `build` Command

```bash
abs_quant build --help

Options:
  -t, --threads THREADS          Number of threads (default: 1)
  -l, --read_length LEN          Read length for Bracken (default: 150; only used when building new database)
  --library LIB [LIB ...]        Kraken2 libraries to download (e.g., bacteria archaea viral)
  --db DB_DIR                    Target database directory (created if it does not exist)
  --kraken_db KRAKEN_DB          Existing Kraken2 database path
  --kneaddata_db KNEADDATA_DB    Existing Kneaddata database path
```

### `process` Command (Single Sample)

```bash
abs_quant process --help

Options:
  -t, --threads THREADS           Number of threads (required)
  --kraken_db KRAKEN_DB           Kraken2 database path (required)
  --kneaddata_db KNEADDATA_DB     Kneaddata database path (required)
  -f, --fq_files FQ1 [FQ2 ...]    FASTQ file(s). For paired‑end: R1 R2; for single‑end: one file.
  --output OUTPUT_DIR              Output directory (required)
  --spikein_copies SPIKEIN_COPIES  **Total number of spike‑in cells added** (sum of both Gram‑positive and Gram‑negative bacteria).  
                                   For ZymoBIOMICS Spike‑in Control I, 20 μl contains **4×10⁷ cells** (2×10⁷ per species).  
                                   If you use a different volume, adjust proportionally (e.g., 10 μl → 2×10⁷).
  --sample_weight SAMPLE_WEIGHT    Sample mass in grams (required)
```

### `batch` Command (Batch Processing)

```bash
abs_quant batch --help

Options:
  -t, --threads THREADS           Number of threads (required)
  --kraken_db KRAKEN_DB           Kraken2 database path (required)
  --kneaddata_db KNEADDATA_DB     Kneaddata database path (required)
  --input INPUT_DIR                Directory containing FASTQ files (required)
  --output OUTPUT_DIR              Output directory (required)
  --spikein_copies SPIKEIN_COPIES  Absolute number of spike‑in molecules added (e.g., 4e7)
  --sample_weight SAMPLE_WEIGHT    Sample mass in grams (required)
  --read_threshold THRESHOLD       Minimum reads to report in absolute table (default: 10)
```

## 💡 Usage Examples

### Example 1: Full batch analysis with custom spike‑in

```bash
abs_quant batch --threads 16 \
                --kraken_db /home/user/databases/kraken2_AQ \
                --kneaddata_db /home/user/databases/kneaddata_db \
                --input /home/user/raw_data \
                --output /home/user/results \
                --spikein_copies 4e7 \
                --sample_weight 0.5 \
                --read_threshold 10
```

### Example 2: Process a single sample

```bash
abs_quant process --threads 8 \
                  --kraken_db /home/user/databases/kraken2_AQ \
                  --kneaddata_db /home/user/databases/kneaddata_db \
                  -f sample_R1.fastq.gz sample_R2.fastq.gz \
                  --output /home/user/results/sample1 \
                  --spikein_copies 4e7 \
                  --sample_weight 1.2
```

### Example 3: Build a new database

```bash
abs_quant build --threads 8 \
                --library bacteria archaea viral \
                --db /home/user/databases
```

## 🔍 Results Interpretation

### Merged absolute abundance table (`merged_absolute_abundance.csv`)

| Column | Description |
|--------|-------------|
| taxonomy_id | NCBI taxonomy ID |
| phylum, class, order, family, genus, species, strain | Taxonomic lineage (from `gram_size_table.csv`) |
| *sample_name* | Absolute abundance for that sample (cells/g) |

### Merged relative abundance table (`merged_relative_abundance.csv`)

Same format, but values are percentages (relative abundance).

### Individual sample files

Each sample folder contains two CSV files with the same columns as above, plus an extra column `new_est_reads` (Bracken‑estimated reads) for reference.

## 📦 Dependencies

All dependencies are installed automatically via the conda environment:

- **Kraken2** (v2.1.2+)
- **Bracken** (v2.7+)
- **Kneaddata** (v0.10.0+)
- **Bowtie2** (v2.4.5+)
- **Trimmomatic** (v0.39+)
- Python packages: pandas, numpy, colorama, biopython

## 📝 Data File Description

### `gram_size_table.csv`

This file must be located in the `abs_quant/data/` directory of the installed package. It contains microbial genome information used for absolute quantification calculations. The required columns are:

- `taxonomy_id` – NCBI taxonomy ID (integer)
- `phylum, class, order, family, genus, species, strain` – taxonomic classification (optional but recommended)
- `genome_size` – genome size in base pairs (integer)
- `Gram.stain` – Gram stain type (`positive`, `negative`, or `varied`)

If your custom Kraken2 database contains species not present in this table, the pipeline will issue warnings and skip absolute quantification for those species.

## 🐛 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Kraken2 database download fails | Check network connection; ensure enough disk space (~100 GB); download libraries individually. |
| Out of memory | Reduce threads (`--threads 4`) or increase swap space. |
| Spike‑in not detected | Verify that the ZymoBIOMICS Spike‑in was added; check concentration. |
| Column errors in output | Ensure `gram_size_table.csv` contains the required columns. |
| Pipeline hangs | Look at log files in the sample output directory; use `--read_threshold` to filter low‑abundance species. |

### Log Files

- Database building logs are stored in `database_dir/log/`
- Sample processing logs are printed to the console and can be redirected to a file.

## 📚 References

1. Wood DE, Lu J, Langmead B. Improved metagenomic analysis with Kraken 2. *Genome Biology*. 2019;20:257.
2. Lu J, Breitwieser FP, Thielen P, Salzberg SL. Bracken: estimating species abundance in metagenomics data. *PeerJ Computer Science*. 2017;3:e104.
3. ZymoBIOMICS Spike‑in Control I Technical Manual.

## 📧 Contact

NI Can – nican0910@connect.hku.hk
