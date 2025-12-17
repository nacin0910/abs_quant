import argparse
import sys
import os
from .build import build_database
from .process import process_sample
from .utils import setup_logger, ColorFormatter
import logging

def main():
    """主命令行接口"""
    parser = argparse.ArgumentParser(
        description="Absolute Quantification Pipeline for Microbial Metagenomics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 构建数据库
  abs_quant build --threads 8 --library bacteria archaea --db /path/to/database
  
  # 使用现有数据库
  abs_quant build --threads 8 --kraken_db /path/to/kraken2_db --kneaddata_db /path/to/kneaddata_db
  
  # 处理样本
  abs_quant aq --threads 8 --read_length 150 \\
               --kraken_db /path/to/kraken2_db \\
               --kneaddata_db /path/to/kneaddata_db \\
               -f sample_R1.fastq.gz sample_R2.fastq.gz \\
               --output results/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # build 命令
    build_parser = subparsers.add_parser('build', help='构建或配置数据库')
    build_parser.add_argument('-t', '--threads', type=int, default=1, 
                             help='线程数 (默认: 1)')
    build_parser.add_argument('-l', '--read_length', type=int, default=150,
                             help='读取长度，用于Bracken数据库构建 (默认: 150)')
    build_parser.add_argument('--library', nargs='+', 
                             help='要下载的Kraken2库 (e.g., bacteria archaea viral)')
    build_parser.add_argument('--db', type=str, 
                             help='目标数据库目录 (如果下载新数据库)')
    build_parser.add_argument('--kraken_db', type=str,
                             help='现有Kraken2数据库路径')
    build_parser.add_argument('--kneaddata_db', type=str,
                             help='现有Kneaddata数据库路径')
    
    # aq 命令 (绝对定量)
    aq_parser = subparsers.add_parser('aq', help='运行绝对定量分析')
    aq_parser.add_argument('-t', '--threads', type=int, required=True,
                          help='线程数')
    aq_parser.add_argument('-l', '--read_length', type=int, required=True,
                          help='读取长度')
    aq_parser.add_argument('--kraken_db', type=str, required=True,
                          help='Kraken2数据库路径')
    aq_parser.add_argument('--kneaddata_db', type=str, required=True,
                          help='Kneaddata数据库路径')
    aq_parser.add_argument('-f', '--fq_files', nargs=2, required=True,
                          help='FASTQ文件 (R1 和 R2)')
    aq_parser.add_argument('--output', type=str, required=True,
                          help='输出目录')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger()
    
    if args.command == 'build':
        try:
            success = build_database(
                threads=args.threads,
                read_length=args.read_length,
                libraries=args.library,
                db_dir=args.db,
                kraken_db=args.kraken_db,
                kneaddata_db=args.kneaddata_db,
                logger=logger
            )
            if success:
                logger.info("✅ 数据库构建/配置完成！")
            else:
                logger.error("❌ 数据库构建/配置失败！")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ 发生错误: {str(e)}")
            sys.exit(1)
            
    elif args.command == 'aq':
        try:
            success = process_sample(
                threads=args.threads,
                read_length=args.read_length,
                kraken_db=args.kraken_db,
                kneaddata_db=args.kneaddata_db,
                fastq_files=args.fq_files,
                output_dir=args.output,
                logger=logger
            )
            if success:
                logger.info("✅ 样本处理完成！")
            else:
                logger.error("❌ 样本处理失败！")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ 发生错误: {str(e)}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
