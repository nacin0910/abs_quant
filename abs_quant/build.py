import subprocess
import os
import sys
from pathlib import Path
import shutil
from .utils import run_command

def build_database(threads, read_length, libraries=None, db_dir=None, 
                  kraken_db=None, kneaddata_db=None, logger=None):
    """
    构建或配置数据库
    
    参数:
        threads: 线程数
        read_length: 读取长度
        libraries: 要下载的Kraken2库列表
        db_dir: 新数据库目录
        kraken_db: 现有Kraken2数据库路径
        kneaddata_db: 现有Kneaddata数据库路径
        logger: 日志记录器
    """
    
    if libraries and db_dir:
        # 下载新数据库
        return _download_and_build_databases(threads, read_length, libraries, db_dir, logger)
    elif kraken_db and kneaddata_db:
        # 使用现有数据库
        return _use_existing_databases(threads, read_length, kraken_db, kneaddata_db, logger)
    else:
        logger.error("❌ 必须提供要下载的库和目标目录，或现有数据库路径")
        return False

def _download_and_build_databases(threads, read_length, libraries, db_dir, logger):
    """下载并构建新数据库"""
    try:
        # 创建目录
        kraken_dir = Path(db_dir) / "kraken2_AQ"
        kneaddata_dir = Path(db_dir) / "kneaddata_db"
        log_dir = Path(db_dir) / "log"
        
        kraken_dir.mkdir(parents=True, exist_ok=True)
        kneaddata_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📥 开始下载Kraken2数据库，这可能需要一些时间...")
        logger.info("📚 可下载的数据库包括: archaea bacteria plasmid viral fungi plant")
        
        # 首先下载taxonomy数据库
        logger.info("🌐 第一步：下载Kraken2 taxonomy数据库...")
        cmd_taxonomy = [
            "kraken2-build", "--threads", str(threads),
            "--download-taxonomy",
            "--db", str(kraken_dir)
        ]
        
        success = run_command(cmd_taxonomy, "下载taxonomy数据库",
                             log_file=log_dir / "taxonomy-download.log",
                             logger=logger)
        if not success:
            logger.error("❌ 下载taxonomy数据库失败")
            return False
        
        logger.info("✅ Taxonomy数据库下载完成！")
        
        # 然后下载各个库
        for lib in libraries:
            cmd_library = [
                "kraken2-build", "--threads", str(threads),
                "--download-library", lib,
                "--db", str(kraken_dir)
            ]
            
            success = run_command(cmd_library, f"下载 {lib} 库", 
                                 log_file=log_dir / f"kraken2-{lib}-download.log",
                                 logger=logger)
            if not success:
                logger.error(f"❌ 下载 {lib} 库失败")
                return False
            
            logger.info(f"✅ {lib} 库下载完成！")
        
        logger.info("✅ Kraken2数据库下载完成！")
        
        # 构建Kraken2数据库
        logger.info("🔨 开始构建Kraken2数据库...")
        cmd_build = [
            "kraken2-build", "--threads", str(threads),
            "--build", "--db", str(kraken_dir)
        ]
        
        success = run_command(cmd_build, "构建Kraken2数据库",
                             log_file=log_dir / "kraken2-build.log",
                             logger=logger)
        if not success:
            logger.error("❌ 构建Kraken2数据库失败")
            return False
        
        logger.info("✅ Kraken2数据库构建完成！")
        
        # 构建Bracken数据库
        logger.info("🔨 开始构建Bracken数据库...")
        cmd_bracken = [
            "bracken-build", "-t", str(threads),
            "-d", str(kraken_dir),
            "-l", str(read_length)
        ]
        
        success = run_command(cmd_bracken, "构建Bracken数据库",
                             log_file=log_dir / "bracken-build.log",
                             logger=logger)
        if not success:
            logger.error("❌ 构建Bracken数据库失败")
            return False
        
        logger.info("✅ Bracken数据库构建完成！")
        
        # 下载Kneaddata数据库
        logger.info("📥 开始下载Kneaddata数据库...")
        cmd_kneaddata = [
            "kneaddata_database", "--download", "human_genome", "bowtie2",
            str(kneaddata_dir)
        ]
        
        success = run_command(cmd_kneaddata, "下载Kneaddata数据库",
                             log_file=log_dir / "kneaddata-download.log",
                             logger=logger)
        if not success:
            logger.error("❌ 下载Kneaddata数据库失败")
            return False
        
        logger.info(f"✅ Kneaddata数据库下载完成！路径: {kneaddata_dir}")
        logger.info(f"✅ 所有数据库已成功构建到: {db_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库构建过程中发生错误: {str(e)}")
        return False

def _use_existing_databases(threads, read_length, kraken_db, kneaddata_db, logger):
    """使用现有数据库"""
    try:
        logger.info("🔄 使用现有数据库...")
        
        # 验证数据库存在
        kraken_path = Path(kraken_db)
        kneaddata_path = Path(kneaddata_db)
        
        if not kraken_path.exists():
            logger.error(f"❌ Kraken2数据库路径不存在: {kraken_db}")
            return False
        
        if not kneaddata_path.exists():
            logger.error(f"❌ Kneaddata数据库路径不存在: {kneaddata_db}")
            return False
        
        logger.info("🔨 重建Kraken2数据库索引...")
        cmd = [
            "kraken2-build", "--build", "--db", str(kraken_path),
            "--threads", str(threads)
        ]
        
        success = run_command(cmd, "重建Kraken2数据库索引", logger=logger)
        if not success:
            logger.error("❌ 重建Kraken2数据库索引失败")
            return False
        
        logger.info("🔨 重建Bracken数据库索引...")
        cmd = [
            "bracken-build", "-d", str(kraken_path),
            "-l", str(read_length), "-t", str(threads)
        ]
        
        success = run_command(cmd, "重建Bracken数据库索引", logger=logger)
        if not success:
            logger.error("❌ 重建Bracken数据库索引失败")
            return False
        
        logger.info("✅ 现有数据库配置完成！")
        logger.info("💡 注意: 此pipeline计算的是每在样品中添加20微升ZymoBIOMICS Spike-in Control I时的微生物绝对丰度")
        logger.info("💡 如需自定义添加量，请按照比例换算 (如添加10微升则将所有丰度除以2)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库配置过程中发生错误: {str(e)}")
        return False
