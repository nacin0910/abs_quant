
# Absolute Quantification Pipeline (abs_quant)

A Python-based conda package for absolute quantification in metagenomic data analysis.

## Installation

### Using Conda (Recommended)

```bash
# Create a new environment
conda create -n abs_quant python=3.8
conda activate abs_quant

# Install the package
pip install abs_quant

# Install dependencies
conda install -c bioconda kraken2 bracken kneaddata trimmomatic bowtie2
```

### From Source

```bash
git clone https://github.com/nacin0910/abs_quant.git
cd abs_quant
pip install -e .
```

## Quick Start

### 1. Database Setup

#### Option A: Build New Databases

```bash
abs_quant build -t 8 -l 150 --db /path/to/database_directory
```

This will:
- Download and build Kraken2 bacteria database
- Add spike-in genomes
- Build Bracken database
- Download Kneaddata human genome database

#### Option B: Use Existing Databases

```bash
abs_quant build -t 8 -l 150 \
  --kraken_db /path/to/existing/kraken_db \
  --kneaddata_db /path/to/existing/kneaddata_db
```

### 2. Run Absolute Quantification

```bash
abs_quant aq -t 8 -l 150 \
  --kraken_db /path/to/kraken2_AQ \
  --kneaddata_db /path/to/kneaddata_db \
  -f sample_R1.fastq.gz sample_R2.fastq.gz \
  -w 0.1 \
  -d 10 \
  --output /path/to/output \
  --output_prefix sample1
```

## Command Reference

### Build Command

```bash
abs_quant build [-h] -t THREADS [-l READ_LENGTH] [--db DB] 
                [--kraken_db KRAKEN_DB] [--kneaddata_db KNEADDATA_DB]
```

**Parameters:**
- `-t, --threads`: Number of threads to use
- `-l, --read_length`: Read length for Bracken database building
- `--db`: Target directory for new database (for new database setup)
- `--kraken_db`: Path to existing Kraken2 database
- `--kneaddata_db`: Path to existing Kneaddata database

### Quantification Command

```bash
abs_quant aq [-h] -t THREADS -l READ_LENGTH --kraken_db KRAKEN_DB 
             --kneaddata_db KNEADDATA_DB -f FQ_FILES FQ_FILES -w DRY_WEIGHT 
             -d DEPTH --output OUTPUT --output_prefix OUTPUT_PREFIX
```

**Parameters:**
- `-t, --threads`: Number of threads to use
- `-l, --read_length`: Read length
- `--kraken_db`: Path to Kraken2 database
- `--kneaddata_db`: Path to Kneaddata database
- `-f, --fq_files`: Forward and reverse FASTQ files
- `-w, --dry_weight`: Dry weight in grams
- `-d, --depth`: Minimum read depth for species detection
- `--output`: Output directory
- `--output_prefix`: Output file prefix

## Workflow

The pipeline performs the following steps:

1. **Host Removal**: Uses Kneaddata to remove host sequences
2. **Taxonomic Classification**: Uses Kraken2 for taxonomic assignment
3. **Abundance Estimation**: Uses Bracken for abundance estimation
4. **Absolute Quantification**: Calculates absolute abundances using spike-in normalization

## Output Files

- `{prefix}_abundance.csv`: Main output with absolute and relative abundances
- `{prefix}.kraken`: Kraken2 classification results
- `{prefix}.kreport`: Kraken2 report
- `{prefix}.bracken`: Bracken abundance estimates

## Dependencies

- Python >= 3.7
- pandas >= 1.3.0
- numpy >= 1.21.0
- biopython >= 1.79
- kraken2
- bracken
- kneaddata
- trimmomatic
- bowtie2

## Citation

If you use this software in your research, please cite:

[Citation information]

## License

MIT License

## Support

For issues and questions, please open an issue on [GitHub](https://github.com/yourusername/abs_quant/issues).
```
