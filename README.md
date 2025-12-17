# Absolute Quantification Pipeline for Microbial Metagenomics

一个用于微生物宏基因组绝对定量的生物信息学流程，读入原始FASTQ文件，使用Kneaddata去除人类宿主污染，Kraken2进行物种分类，基于ZymoBIOMICS Spike-in Control进行微生物绝对丰度计算。


## 🚀 快速开始

### 1. 安装

#### 通过Conda安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/abs_quant.git
cd abs_quant

# 创建conda环境
conda env create -f environment.yml
conda activate abs_quant

# 安装包
pip install -e .
```

#### 通过Pip安装

```bash
pip install abs_quant
```

### 2. 数据库配置

#### 选项A：下载新数据库

```bash
# 下载并构建所有必要数据库
abs_quant build --threads 8 \
                --library bacteria archaea fungi viral \
                --db /path/to/database
```

#### 选项B：使用现有数据库

```bash
# 如果您已有Kraken2和Kneaddata数据库
abs_quant build --threads 8 \
                --kraken_db /path/to/kraken2_db \
                --kneaddata_db /path/to/kneaddata_db
```

### 3. 运行分析

```bash
abs_quant aq --threads 8 \
             --read_length 150 \
             --kraken_db /path/to/kraken2_db \
             --kneaddata_db /path/to/kneaddata_db \
             -f sample_R1.fastq.gz sample_R2.fastq.gz \
             --output results/
```

## 📁 输出文件

处理完成后，您将获得以下文件：

```
results/
├── kneaddata_out/           # Kneaddata处理结果
│   ├── sample_paired_1.fastq     # 去除宿主后的R1
│   ├── sample_paired_2.fastq     # 去除宿主后的R2
│   ├── sample_unmatched_1.fastq
│   └── sample_unmatched_2.fastq
├── kraken_out/              # Kraken2和Bracken处理结果
│   ├── sample.kraken
│   ├── sample.kreport
│   └── sample.bracken
└── sample_abundance.csv     # 绝对丰度结果（主要输出）
```

## 📊 绝对定量原理

本流程使用以下两种spike-in细菌进行绝对定量：

| 细菌 | Taxonomy ID | 基因组大小 | 革兰氏染色 |
|------|-------------|------------|------------|
| Allobacillus halotolerans | 570278 | 2,700,297 bp | 阳性 |
| Imtechella halotolerans | 1,165,090 | 3,113,111 bp | 阴性 |

**计算公式**：
- 对于革兰氏阳性菌：`丰度 = 20,000,000 × (reads_x / genome_size_x) / (reads_AH / AH_size)`
- 对于革兰氏阴性菌：`丰度 = 20,000,000 × (reads_x / genome_size_x) / (reads_IH / IH_size)`
- 对于未知染色菌：`丰度 = 40,000,000 × (reads_x / genome_size_x) / (reads_AH/AH_size + reads_IH/IH_size)`

## 🔧 依赖软件

本流程依赖于以下软件，推荐通过conda安装：

- **Kraken2** (v2.1.2+) - 快速分类器
- **Bracken** (v2.7+) - 丰度估计
- **Kneaddata** (v0.10.0+) - 质量控制
- **Bowtie2** (v2.4.5+) - 序列比对
- **Trimmomatic** (v0.39+) - 序列修剪
- **Python包**: pandas, numpy, colorama, biopython, importlib-resources

## ⚙️ 命令行选项

### `build` 命令

```bash
abs_quant build --help

选项：
  -t, --threads THREADS   线程数 (默认: 1)
  -l, --read_length LEN   读取长度，用于Bracken (默认: 150)
  --library LIB [LIB ...] 要下载的Kraken2库
  --db DB_DIR             目标数据库路径，将创建并下载到kraken2_AQ和kneaddata_db文件夹
  --kraken_db KRAKEN_DB   现有Kraken2数据库路径
  --kneaddata_db KNEAD_DB 现有Kneaddata数据库路径
```

### `aq` 命令（绝对定量）

```bash
abs_quant aq --help

选项：
  -t, --threads THREADS    线程数 (必需)
  -l, --read_length LEN    读取长度 (必需)
  --kraken_db KRAKEN_DB    Kraken2数据库路径 (必需)
  --kneaddata_db KNEAD_DB  Kneaddata数据库路径 (必需)
  -f, --fq_files FQ1 FQ2   FASTQ文件 (R1和R2) (必需)
  --output OUTPUT_DIR      输出目录 (必需)
```

## 💡 使用示例

### 示例1：完整分析流程

```bash
# 1. 下载数据库（首次使用）
abs_quant build --threads 16 \
                --library bacteria archaea \
                --db /home/user/databases

# 2. 处理多个样本
for sample in sample1 sample2 sample3; do
    abs_quant aq --threads 8 \
                 --read_length 150 \
                 --kraken_db /home/user/databases/kraken2_AQ \
                 --kneaddata_db /home/user/databases/kneaddata_db \
                 -f ${sample}_R1.fastq.gz ${sample}_R2.fastq.gz \
                 --output results/${sample}
done
```

### 示例2：批量处理脚本

创建一个`run_analysis.sh`脚本：

```bash
#!/bin/bash

# 设置参数
THREADS=8
READ_LEN=150
KRAKEN_DB="/path/to/kraken2_db"
KNEAD_DB="/path/to/kneaddata_db"
OUTPUT_DIR="results"

# 处理所有样本
for r1_file in data/*_R1.fastq.gz; do
    r2_file="${r1_file/_R1/_R2}"
    sample=$(basename "${r1_file/_R1*/}")
    
    echo "处理样本: ${sample}"
    
    abs_quant aq --threads ${THREADS} \
                 --read_length ${READ_LEN} \
                 --kraken_db ${KRAKEN_DB} \
                 --kneaddata_db ${KNEAD_DB} \
                 -f ${r1_file} ${r2_file} \
                 --output ${OUTPUT_DIR}/${sample}
done
```

## 🔍 结果解释

输出文件 `sample_abundance.csv` 包含以下列：

| 列名 | 描述 |
|------|------|
| name | 物种名称 |
| taxonomy_id | NCBI分类ID |
| new_est_reads | Bracken估计的reads数 |
| abs_abundance | 绝对丰度（细胞数） |
| relative_abundance | 相对丰度（%，仅当spike-in不足时） |

## 🐛 故障排除

### 常见问题

1. **Kraken2数据库下载失败**
   - 检查网络连接
   - 确保有足够的磁盘空间（~100GB）
   - 尝试单个库下载：`--library bacteria`

2. **内存不足**
   - 减少线程数：`--threads 4`
   - 增加系统交换空间

3. **Spike-in检测不到**
   - 检查样本中是否添加了ZymoBIOMICS Spike-in Control
   - 检查spike-in浓度是否合适

4. **数据类型错误**
   - 确保基因组信息表中的数值列是数值类型，不是字符串
   - 运行 `python check_and_fix_data.py` 修复数据文件

### 日志文件

所有步骤都生成日志文件，位于：
- 数据库构建：`database_dir/log/`
- 样本处理：`output_dir/`（标准输出）

## 📝 数据文件说明

### gram_size_table.csv

该文件包含微生物基因组信息，用于绝对定量计算。至少需要以下列：
- `taxonomy_id`: NCBI分类ID（整数）
- `genome_size`: 基因组大小（整数，单位bp）
- `Gram.stain`: 革兰氏染色类型（"positive"或"negative"）

您可以从NCBI下载完整的基因组信息表，或使用包中提供的示例文件。



## 📚 参考文献

1. Wood DE, Lu J, Langmead B. Improved metagenomic analysis with Kraken 2. Genome Biology. 2019;20:257.
2. Lu J, Breitwieser FP, Thielen P, Salzberg SL. Bracken: estimating species abundance in metagenomics data. PeerJ Computer Science. 2017;3:e104.
3. ZymoBIOMICS Spike-in Control I Technical Manual

## 📧 联系方式

NI Can - nican0910@connect.hku.hk

