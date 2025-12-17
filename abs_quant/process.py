import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from .utils import run_command, get_sample_name

def _remove_host_sequences(threads, fastq_files, kneaddata_db, 
                          output_dir, sample_name, logger):
    """去除宿主序列"""
    try:
        # Kneaddata命令 - 移除--scratch-dir参数
        cmd = [
            "kneaddata",
            "--threads", str(min(8, threads)),  # Trimmomatic最多8线程
            "--input1", str(fastq_files[0]),
            "--input2", str(fastq_files[1]),
            "--reference-db", str(kneaddata_db),
            "--output", str(output_dir),
            "--output-prefix", sample_name,
            "--remove-intermediate-output"
        ]
        
        success = run_command(cmd, "去除宿主序列", logger=logger)
        return success

    except Exception as e:
        logger.error(f"❌ 去除宿主序列失败: {str(e)}")
        return False


def _classify_sequences(threads, read_length, kraken_db, kneaddata_out_dir, 
                       kraken_out_dir, sample_name, logger):
    """使用Kraken2和Bracken进行分类
    
    参数:
        threads: 线程数
        read_length: 读取长度
        kraken_db: Kraken2数据库路径
        kneaddata_out_dir: Kneaddata输出目录
        kraken_out_dir: Kraken输出目录
        sample_name: 样本名
        logger: 日志记录器
    """
    try:
        logger.info(f"🔍 查找Kraken2输入文件...")
        
        # 查找kneaddata输出文件
        # 尝试多种可能的扩展名
        file_patterns = [
            (f"{sample_name}_paired_1.fastq", f"{sample_name}_paired_2.fastq"),
            (f"{sample_name}_paired_1.fastq.gz", f"{sample_name}_paired_2.fastq.gz"),
            (f"{sample_name}_paired_1.fq", f"{sample_name}_paired_2.fq"),
            (f"{sample_name}_paired_1.fq.gz", f"{sample_name}_paired_2.fq.gz"),
            # 如果kneaddata在文件名中添加了额外的后缀
            (f"{sample_name}.kneaddata_paired_1.fastq", f"{sample_name}.kneaddata_paired_2.fastq"),
            (f"{sample_name}.kneaddata_paired_1.fastq.gz", f"{sample_name}.kneaddata_paired_2.fastq.gz"),
        ]
        
        r1_file = None
        r2_file = None
        
        for r1_pattern, r2_pattern in file_patterns:
            r1_candidate = kneaddata_out_dir / r1_pattern
            r2_candidate = kneaddata_out_dir / r2_pattern
            
            if r1_candidate.exists() and r2_candidate.exists():
                r1_file = r1_candidate
                r2_file = r2_candidate
                logger.info(f"📁 找到输入文件: {r1_pattern} 和 {r2_pattern}")
                break
        
        # Kraken2分类
        kraken_output = kraken_out_dir / f"{sample_name}.kraken"
        kreport_output = kraken_out_dir / f"{sample_name}.kreport"
        
        cmd = [
            "kraken2", "--threads", str(threads),
            "--db", str(kraken_db),
            "--confidence", "0.1",
            "--paired",
            "--output", str(kraken_output),
            "--report", str(kreport_output),
            str(r1_file), str(r2_file)
        ]
        
        success = run_command(cmd, "Kraken2分类", logger=logger)
        if not success:
            return False
        
        # Bracken定量 - 现在使用传入的read_length参数
        bracken_output = kraken_out_dir / f"{sample_name}.bracken"
        
        cmd = [
            "bracken", "-t", str(threads),
            "-d", str(kraken_db),
            "-i", str(kreport_output),
            "-o", str(bracken_output),
            "-r", str(read_length),  # 使用传入的read_length参数
            "-l", "S"  # Species level
        ]
        
        success = run_command(cmd, "Bracken定量", logger=logger)
        return success
        
    except Exception as e:
        logger.error(f"❌ 序列分类失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_sample(threads, read_length, kraken_db, kneaddata_db, 
                  fastq_files, output_dir, logger):
    """
    处理样本进行绝对定量分析
    
    参数:
        threads: 线程数
        read_length: 读取长度
        kraken_db: Kraken2数据库路径
        kneaddata_db: Kneaddata数据库路径
        fastq_files: FASTQ文件路径列表 [R1, R2]
        output_dir: 输出目录
        logger: 日志记录器
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        kneaddata_out_dir = output_path / "kneaddata_out"
        kraken_out_dir = output_path / "kraken_out"
        
        kneaddata_out_dir.mkdir(parents=True, exist_ok=True)
        kraken_out_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取样本名
        sample_name = get_sample_name(fastq_files[0])
        logger.info(f"🧬 开始处理样本: {sample_name}")
        logger.info(f"📏 读取长度: {read_length} bp")
        
        # 1. 去除宿主序列
        logger.info("🔍 步骤1: 去除宿主序列...")
        success = _remove_host_sequences(
            threads=threads,
            fastq_files=fastq_files,
            kneaddata_db=kneaddata_db,
            output_dir=kneaddata_out_dir,
            sample_name=sample_name,
            logger=logger
        )
        
        if not success:
            return False
        
        # 2. 读取比对和分类 - 修正：传递read_length参数
        logger.info("🔍 步骤2: 微生物分类...")
        success = _classify_sequences(
            threads=threads,
            read_length=read_length,  # 传递read_length参数
            kraken_db=kraken_db,
            kneaddata_out_dir=kneaddata_out_dir,
            kraken_out_dir=kraken_out_dir,
            sample_name=sample_name,
            logger=logger
        )
        
        if not success:
            return False
        
        # 3. 绝对定量计算
        logger.info("🔍 步骤3: 绝对定量计算...")
        success = _calculate_absolute_abundance(
            read_length=read_length,
            output_dir=output_path,
            kraken_out_dir=kraken_out_dir,
            sample_name=sample_name,
            logger=logger
        )
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 样本处理过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def _calculate_absolute_abundance(read_length, output_dir, 
                                 kraken_out_dir, sample_name, logger):
    """计算绝对丰度"""
    try:
        # 读取Bracken结果
        bracken_file = kraken_out_dir / f"{sample_name}.bracken"
        if not bracken_file.exists():
            logger.error(f"❌ Bracken输出文件未找到: {bracken_file}")
            return False
        
        # 读取Bracken表格
        df = pd.read_csv(bracken_file, sep='\t')
        
        current_dir = Path(__file__).parent
        gram_size_file = current_dir / 'data' / 'gram_size_table.csv'
        genome_info = pd.read_csv(gram_size_file)
        genome_info['genome_size'] = pd.to_numeric(genome_info['genome_size'], errors='coerce')
        
        # Spike-in信息
        AH_taxid = 570278    # Allobacillus halotolerans
        IH_taxid = 1165090   # Imtechella halotolerans
        AH_size = 2700297    # 基因组大小
        IH_size = 3113111
        
        # 提取spike-in reads
        ah_row = df[df['taxonomy_id'] == AH_taxid]
        ih_row = df[df['taxonomy_id'] == IH_taxid]
        
        reads_AH = ah_row['new_est_reads'].values[0] if len(ah_row) > 0 else 0
        reads_IH = ih_row['new_est_reads'].values[0] if len(ih_row) > 0 else 0
        
        logger.info(f"📊 AH reads数: {reads_AH}, IH reads数: {reads_IH}")
        
        # 计算细胞数
        cell_num_AH = read_length * reads_AH / AH_size if reads_AH > 0 else 0
        cell_num_IH = read_length * reads_IH / IH_size if reads_IH > 0 else 0
        
        logger.info(f"📊 AH细胞数: {cell_num_AH:.2f}, IH细胞数: {cell_num_IH:.2f}")
        
        # 检查spike-in丰度
        total_reads = df['new_est_reads'].sum()
        ah_ratio = reads_AH / total_reads if total_reads > 0 else 0
        ih_ratio = reads_IH / total_reads if total_reads > 0 else 0
        
        df['abs_abundance'] = 0.0
        
        if ah_ratio < 0.001 or ih_ratio < 0.001:
            logger.warning("⚠️  样品中spike-in丰度过低，无法作绝对定量，仅输出相对丰度")
            df['relative_abundance'] = df['new_est_reads'] / total_reads * 100 if total_reads > 0 else 0
            
            # 保存结果到output_dir（不是子目录）
            output_file = output_dir / f"{sample_name}_abundance.csv"
            df[['name', 'taxonomy_id', 'new_est_reads', 'relative_abundance']].to_csv(
                output_file, index=False
            )
            logger.info(f"📄 相对丰度结果已保存到: {output_file}")
        else:
            logger.info("✅  Spike-in丰度正常，进行绝对定量计算...")
            
            # 为每个物种计算绝对丰度
            for idx, row in df.iterrows():
                taxid = row['taxonomy_id']
                reads_x = row['new_est_reads']
                
                # 查找基因组信息
                genome_row = genome_info[genome_info['taxonomy_id'] == taxid]
                
                if len(genome_row) == 0:
                    # 如果没有基因组信息，跳过
                    continue
                
                genome_size = genome_row.iloc[0]['genome_size']
                gram_stain = genome_row.iloc[0]['Gram.stain']
                
                # 计算细胞数
                cell_num_x = read_length * reads_x / genome_size
                
                if gram_stain == 'positive':
                    cell_num_total = 20000000 * cell_num_x / cell_num_AH if cell_num_AH > 0 else 0
                elif gram_stain == 'negative':
                    cell_num_total = 20000000 * cell_num_x / cell_num_IH if cell_num_IH > 0 else 0
                else:
                    total_spikein = cell_num_AH + cell_num_IH
                    cell_num_total = 40000000 * cell_num_x / total_spikein if total_spikein > 0 else 0
                
                df.at[idx, 'abs_abundance'] = cell_num_total
            
            # 保存结果到output_dir（不是子目录）
            output_file = output_dir / f"{sample_name}_abundance.csv"
            df[['name', 'taxonomy_id', 'new_est_reads', 'abs_abundance']].to_csv(
                output_file, index=False
            )
            logger.info(f"📄 绝对丰度结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 绝对定量计算失败: {str(e)}")
        return False
