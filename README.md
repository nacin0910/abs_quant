# Absolute Quantification Pipeline for Microbial Metagenomics

A bioinformatics pipeline for the absolute quantification of microbial metagenomes. It takes raw FASTQ files as input, uses Kneaddata to remove human host contamination, applies Kraken2 for taxonomic classification, and calculates absolute microbial abundance based on the ZymoBIOMICS Spike-in Control.

## 🚀 Quick Start

### 1. Installation

#### Via Conda

```bash
# Clone the repository (alternatively, download and extract the installation package)
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

### 3. Run Analysis

```bash
abs_quant aq --threads 8 \
             --read_length 150 \
             --kraken_db /path/to/kraken2_db \
             --kneaddata_db /path/to/kneaddata_db \
             -f sample_R1.fastq.gz sample_R2.fastq.gz \
             --output results/

```

## 📁 Output Files

After processing, you will obtain the following files:

```
results/
├── kneaddata_out/           # Kneaddata output
│   ├── sample_paired_1.fastq      # Host-depleted R1
│   ├── sample_paired_2.fastq      # Host-depleted R2
│   ├── sample_unmatched_1.fastq
│   └── sample_unmatched_2.fastq
├── kraken_out/              # Kraken2 and Bracken output
│   ├── sample.kraken
│   ├── sample.kreport
│   └── sample.bracken
└── sample_abundance.csv     # Absolute abundance results (main output)

```

## 📊 Principle of Absolute Quantification

This pipeline uses the following two spike-in bacteria for absolute quantification, both with a cell count of 2 x 10^7 per prep (20 μl):

| Bacteria | Taxonomy ID | Genome Size | Gram Stain |
| --- | --- | --- | --- |
| Allobacillus halotolerans | 570278 | 2,700,297 bp | Positive |
| Imtechella halotolerans | 1,165,090 | 3,113,111 bp | Negative |

**Calculation Formulas**:

* For Gram-positive bacteria: `Abundance = 20,000,000 × (reads_x / genome_size_x) / (reads_AH / AH_size)`
* For Gram-negative bacteria: `Abundance = 20,000,000 × (reads_x / genome_size_x) / (reads_IH / IH_size)`
* For bacteria with unknown Gram stain: `Abundance = 40,000,000 × (reads_x / genome_size_x) / (reads_AH/AH_size + reads_IH/IH_size)`
* If the spike-in input volume is not 20 μl, simply scale it proportionally (e.g., if 40 μl is added, multiply the calculated absolute abundance by 2)

## 🔧 Dependencies

This pipeline depends on the following software, which will be installed when creating the conda environment:

* **Kraken2** (v2.1.2+) - Fast taxonomic classifier
* **Bracken** (v2.7+) - Abundance estimation
* **Kneaddata** (v0.10.0+) - Quality control
* **Bowtie2** (v2.4.5+) - Sequence alignment
* **Trimmomatic** (v0.39+) - Sequence trimming
* **Python packages**: pandas, numpy, colorama, biopython...

## ⚙️ Command Line Options

### `build` Command

```bash
abs_quant build --help

Options:
  -t, --threads THREADS    Number of threads (default: 1)
  -l, --read_length LEN    Read length, used for Bracken (default: 150)
  --library LIB [LIB ...]  Kraken2 libraries to download
  --db DB_DIR              Target database path; will create and download to kraken2_AQ and kneaddata_db folders
  --kraken_db KRAKEN_DB    Existing Kraken2 database path
  --kneaddata_db KNEAD_DB  Existing Kneaddata database path

```

### `aq` Command (Absolute Quantification)

```bash
abs_quant aq --help

Options:
  -t, --threads THREADS    Number of threads (required)
  -l, --read_length LEN    Read length (required)
  --kraken_db KRAKEN_DB    Kraken2 database path (required)
  --kneaddata_db KNEAD_DB  Kneaddata database path (required)
  -f, --fq_files FQ1 FQ2   FASTQ files (R1 and R2) (required)
  --output OUTPUT_DIR      Output directory (required)

```

## 💡 Usage Examples

### Example 1: Complete Analysis Pipeline

```bash
# 1. Download databases (first-time use)
abs_quant build --threads 16 \
                --library bacteria archaea \
                --db /home/user/databases

# 2. Process multiple samples
for sample in sample1 sample2 sample3; do
    abs_quant aq --threads 8 \
                 --read_length 150 \
                 --kraken_db /home/user/databases/kraken2_AQ \
                 --kneaddata_db /home/user/databases/kneaddata_db \
                 -f ${sample}_R1.fastq.gz ${sample}_R2.fastq.gz \
                 --output results/${sample}
done

```

### Example 2: Batch Processing Script

Create a `run_analysis.sh` script:

```bash
#!/bin/bash

# Set parameters
THREADS=8
READ_LEN=150
KRAKEN_DB="/path/to/kraken2_db"
KNEAD_DB="/path/to/kneaddata_db"
OUTPUT_DIR="results"

# Process all samples
for r1_file in data/*_R1.fastq.gz; do
    r2_file="${r1_file/_R1/_R2}"
    sample=$(basename "${r1_file/_R1*/}")
    
    echo "Processing sample: ${sample}"
    
    abs_quant aq --threads ${THREADS} \
                 --read_length ${READ_LEN} \
                 --kraken_db ${KRAKEN_DB} \
                 --kneaddata_db ${KNEAD_DB} \
                 -f ${r1_file} ${r2_file} \
                 --output ${OUTPUT_DIR}/${sample}
done

```

## 🔍 Results Interpretation

The output file `sample_abundance.csv` contains the following columns:

| Column Name | Description |
| --- | --- |
| name | Species name |
| taxonomy_id | NCBI taxonomy ID |
| new_est_reads | Number of reads estimated by Bracken |
| abs_abundance | Absolute abundance (cell count) |
| relative_abundance | Relative abundance (%, only when spike-in reads are insufficient) |

## 🐛 Troubleshooting

### Common Issues

1. **Kraken2 database download fails**
* Check network connection
* Ensure sufficient disk space (~100GB)
* Try downloading libraries individually: `--library bacteria`


2. **Out of Memory**
* Reduce the number of threads: `--threads 4`
* Increase system swap space


3. **Spike-in not detected**
* Check if the ZymoBIOMICS Spike-in Control was added to the sample
* Check if the spike-in concentration is appropriate


4. **Data type error**
* Ensure the numerical columns in the genome information table are of numeric type, not strings



### Log Files

All steps generate log files, located at:

* Database building: `database_dir/log/`
* Sample processing: `output_dir/` (Standard output)

## 📝 Data File Description

### gram_size_table.csv

This file contains microbial genome information used for absolute quantification calculations. It requires at least the following columns:

* `taxonomy_id`: NCBI taxonomy ID (integer)
* `genome_size`: Genome size (integer, in bp)
* `Gram.stain`: Gram stain type ("positive", "negative", or "varied")

You can use the example file provided in the package (located in the `abs_quant/data` directory within the installation path), or prepare and replace it according to your custom Kraken database.

## 📚 References

1. Wood DE, Lu J, Langmead B. Improved metagenomic analysis with Kraken 2. Genome Biology. 2019;20:257.
2. Lu J, Breitwieser FP, Thielen P, Salzberg SL. Bracken: estimating species abundance in metagenomics data. PeerJ Computer Science. 2017;3:e104.
3. ZymoBIOMICS Spike-in Control I Technical Manual

## 📧 Contact Information

NI Can - nican0910@connect.hku.hk
