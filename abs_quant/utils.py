import subprocess
import logging
import sys
from pathlib import Path
import time
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        record.levelname = color + record.levelname + Style.RESET_ALL
        record.msg = color + str(record.msg) + Style.RESET_ALL
        return super().format(record)

def setup_logger():
    """设置日志记录器"""
    logger = logging.getLogger('abs_quant')
    logger.setLevel(logging.INFO)
    
    # 清除现有处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = ColorFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger

def run_command(cmd, description, log_file=None, logger=None, timeout=None):
    """运行外部命令"""
    if logger:
        logger.info(f"🚀 {description}: {' '.join(map(str, cmd))}")
    
    try:
        start_time = time.time()
        
        if log_file:
            with open(log_file, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=True,
                    timeout=timeout
                )
        else:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=timeout
            )
        
        elapsed_time = time.time() - start_time
        
        if logger:
            logger.info(f"✅  {description} 完成 (用时: {elapsed_time:.1f}秒)")
            
            # 如果命令有输出，记录一些关键信息
            if result.stdout and len(result.stdout.strip()) > 0:
                # 只记录最后几行输出，避免日志过长
                lines = result.stdout.strip().split('\n')
                if len(lines) > 5:
                    logger.info("   ... (输出已截断)")
                    for line in lines[-5:]:
                        if line.strip():
                            logger.info(f"   {line.strip()}")
                else:
                    for line in lines:
                        if line.strip():
                            logger.info(f"   {line.strip()}")
        
        return True
        
    except subprocess.TimeoutExpired:
        if logger:
            logger.error(f"⏰  {description} 超时 (超时时间: {timeout}秒)")
        return False
    except subprocess.CalledProcessError as e:
        if logger:
            logger.error(f"❌  {description} 失败")
            if e.stderr:
                # 只显示错误的前几行
                error_lines = e.stderr.strip().split('\n')
                for line in error_lines[:5]:
                    if line.strip():
                        logger.error(f"   错误: {line.strip()}")
                if len(error_lines) > 5:
                    logger.error("   ... (更多错误信息已截断)")
        return False
    except FileNotFoundError as e:
        if logger:
            logger.error(f"❌  命令未找到: {cmd[0]}")
            logger.error(f"   请确保已安装: {cmd[0]}")
            logger.error(f"   可以尝试: conda install -c bioconda {cmd[0]}")
        return False
    except Exception as e:
        if logger:
            logger.error(f"❌  {description} 过程中发生未知错误: {str(e)}")
        return False

def get_sample_name(fastq_path):
    """从FASTQ文件路径提取样本名，支持多种命名约定"""
    path = Path(fastq_path)
    name = path.name
    
    logger = logging.getLogger('abs_quant')
    logger.debug(f"提取样本名 - 原始文件名: {name}")
    
    # 去除常见扩展名
    suffixes = ['.fq', '.fastq', '.fq.gz', '.fastq.gz']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            logger.debug(f"去除扩展名后: {name}")
            break
    
    # 定义要移除的read标识符模式（按优先级）
    read_patterns = [
        # 标准Illumina命名
        '_R1', '_R2',
        # 简化命名
        '_1', '_2',
        # 其他常见模式
        '.R1', '.R2',
        '.1', '.2',
        # kneaddata输出格式
        '_paired_1', '_paired_2',
        '_kneaddata_paired_1', '_kneaddata_paired_2',
        # 双端测序的其他标记
        '_forward', '_reverse',
        '_fwd', '_rev'
    ]
    
    # 按优先级移除匹配的模式
    original_name = name
    for pattern in read_patterns:
        if pattern in name:
            # 尝试移除模式
            new_name = name.replace(pattern, '')
            
            # 检查移除后是否还包含另一个read标识符
            # 如果不包含，或者包含的是不同样本的标识符，则接受
            has_other_pattern = False
            for other_pattern in read_patterns:
                if other_pattern != pattern and other_pattern in new_name:
                    has_other_pattern = True
                    break
            
            if not has_other_pattern:
                name = new_name
                logger.debug(f"移除模式 '{pattern}' 后: {name}")
                break
    
    # 如果移除后名字为空，或者与原始名字相同，尝试其他策略
    if not name or name == original_name:
        # 策略1: 使用下划线分割，取第一部分（假设格式为 sample_something.fastq）
        parts = original_name.split('_')
        if len(parts) > 1:
            # 检查第一部分是否看起来像样本名（不包含数字或特殊字符）
            if parts[0] and not any(c.isdigit() for c in parts[0]):
                name = parts[0]
                logger.debug(f"使用下划线分割第一部分: {name}")
    
    # 清理可能的尾随下划线或点
    name = name.rstrip('_.')
    
    logger.info(f"📝 提取样本名: 从 '{path.name}' 提取到 '{name}'")
    return name


def check_dependencies():
    """检查必要的依赖是否安装"""
    dependencies = ['kraken2', 'bracken', 'kneaddata', 'bowtie2']
    missing = []
    
    for dep in dependencies:
        try:
            subprocess.run([dep, '--version'], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            missing.append(dep)
    
    return missing
