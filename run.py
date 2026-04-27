import asyncio
import pyarrow.parquet as pq
import json
from pathlib import Path
import sys
import subprocess
import shlex
from datetime import datetime


def load_parquet_questions(parquet_path):
    """从 parquet 文件加载问题数据"""
    try:
        parquet_file = pq.ParquetFile(parquet_path)
        table = parquet_file.read()
        return table.to_pylist()
    except Exception as e:
        print(f'加载 parquet 文件 {parquet_path} 时出错: {e}')
        return []


def parse_question_ranges(range_str, total_questions):
    """解析题目范围字符串，返回要处理的问题索引列表
    
    Args:
        range_str: 范围字符串，如 "1-20,21-30" 或 "5,10,15-20"
        total_questions: 总问题数
    
    Returns:
        要处理的问题索引列表（从0开始）
    """
    if not range_str:
        return list(range(total_questions))
    
    indices = set()
    ranges = range_str.split(',')
    
    for r in ranges:
        r = r.strip()
        if '-' in r:
            # 处理范围，如 "1-20"
            start, end = r.split('-')
            start = int(start.strip())
            end = int(end.strip())
            # 转换为0-based索引
            start_idx = max(0, start - 1)
            end_idx = min(total_questions, end)
            indices.update(range(start_idx, end_idx))
        else:
            # 处理单个数字，如 "5"
            idx = int(r.strip()) - 1  # 转换为0-based索引
            if 0 <= idx < total_questions:
                indices.add(idx)
    
    return sorted(indices)


async def process_question(question_data, index, semaphore):
    """处理单个问题 - 调用 main.py 来处理问题
    
    Args:
        question_data: 问题数据字典
        index: 问题索引
        semaphore: 并发控制信号量
    """
    async with semaphore:  # 使用信号量限制并发数
        # 提取问题内容
        question_id = question_data.get('id', f'unknown_{index}')
        
        
        # 生成唯一的workspace名称：workspace/time+id
        current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        workspace_name = f'workspace/{current_time}+{question_id}'
        
        print(f'开始处理问题 {index} (ID: {question_id}, workspace: {workspace_name})...')
        
        try:
            # 调用 main.py 来处理问题，添加 workspace 参数
            cmd = ['python', 'main.py', '-question_json', json.dumps(question_data), '-workspace', workspace_name,'-unpack']
            
            # 设置环境变量，使用 UTF-8 编码避免 Windows GBK 编码问题
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # 在异步环境中运行同步的 subprocess
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # 替换无法解码的字符
                env=env,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f'问题 {index} (ID: {question_id}) 处理成功')
                return {
                    'index': index,
                    'id': question_id,
                    'status': 'success',
                    'workspace': workspace_name,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                print(f'问题 {index} (ID: {question_id}) 处理失败: {result.stderr}')
                return {
                    'index': index,
                    'id': question_id,
                    'status': 'failed',
                    'workspace': workspace_name,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print(f'问题 {index} (ID: {question_id}) 处理超时')
            return {
                'index': index,
                'id': question_id,
                'status': 'timeout',
                'workspace': workspace_name,
                'reason': 'processing_timeout'
            }
        except Exception as e:
            print(f'问题 {index} (ID: {question_id}) 处理出错: {e}')
            return {
                'index': index,
                'id': question_id,
                'status': 'error',
                'workspace': workspace_name,
                'error': str(e)
            }





async def main(parquet_path, max_concurrent=8, question_ranges=None):
    """主函数 - 并行处理 parquet 文件
    
    Args:
        parquet_path: parquet 文件路径
        max_concurrent: 最大并发处理的问题数量
        question_ranges: 题目范围字符串，如 "1-20,21-30"
    """
    print(f'正在从 {parquet_path} 加载问题...')
    all_questions = load_parquet_questions(parquet_path)

    if not all_questions:
        print('未加载到问题。退出。')
        return

    print(f'已加载 {len(all_questions)} 个问题。')
    
    # 解析题目范围
    question_indices = parse_question_ranges(question_ranges, len(all_questions))
    questions = [all_questions[i] for i in question_indices]
    
    if question_ranges:
        print(f'题目范围: {question_ranges}')
    print(f'将处理 {len(questions)} 个问题（从 {len(all_questions)} 个问题中筛选）。')
    print(f'并发设置: 同时最多处理 {max_concurrent} 个问题')
    print(f'处理方式: 对每个问题调用 python main.py -question_json "问题"')

    # 创建信号量来控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)

    print(f'正在处理所有 {len(questions)} 个问题...')

    # 为所有问题创建异步任务
    tasks = []
    for idx, question in enumerate(questions):
        # 使用原始索引作为问题编号
        original_index = question_indices[idx]
        task = asyncio.create_task(process_question(question, original_index, semaphore))
        tasks.append(task)

    # 等待所有任务完成
    all_results = await asyncio.gather(*tasks)

    print(f'已完成所有 {len(questions)} 个问题的处理。')

    # 保存结果
    output_file = Path(parquet_path).with_suffix('.processed.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f'结果已保存到 {output_file}')

    # 打印摘要
    print('\n摘要:')
    print(f'  总共处理的问题数: {len(all_results)}')
    if all_results:
        success_count = sum(1 for r in all_results if r.get('status') == 'success')
        failed_count = sum(1 for r in all_results if r.get('status') == 'failed')
        timeout_count = sum(1 for r in all_results if r.get('status') == 'timeout')
        error_count = sum(1 for r in all_results if r.get('status') == 'error')
        skipped_count = sum(1 for r in all_results if r.get('status') == 'skipped')
        
        print(f'  成功: {success_count}')
        print(f'  失败: {failed_count}')
        print(f'  超时: {timeout_count}')
        print(f'  错误: {error_count}')
        print(f'  跳过: {skipped_count}')


if __name__ == '__main__':
    # 解析命令行参数
    if len(sys.argv) < 2:
        print('用法: python run.py <parquet文件路径> [最大并发数] [题目范围]')
        print('示例: python run.py ./question-v1.parquet 8')
        print('示例: python run.py ./question-v1.parquet 8 "1-20,21-30"')
        print('示例: python run.py ./question-v1.parquet 4 "5,10,15-20"')
        print('参数说明:')
        print('  parquet文件路径: 必需，包含问题数据的 parquet 文件路径')
        print('  最大并发数: 可选，同时处理的最大问题数量，默认 8')
        print('  题目范围: 可选，指定要处理的题目范围，格式如 "1-20,21-30" 或 "5,10,15-20"')
        print('           题目编号从1开始，多个范围用逗号分隔')
        print('           不指定则处理所有题目')
        sys.exit(1)

    parquet_path = sys.argv[1]
    max_concurrent = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8
    
    # 解析题目范围参数
    question_ranges = None
    if len(sys.argv) > 2:
        if not sys.argv[2].isdigit():
            # 第二个参数是题目范围
            question_ranges = sys.argv[2]
        elif len(sys.argv) > 3:
            # 第三个参数是题目范围
            question_ranges = sys.argv[3]

    print(f'配置: 最大并发数={max_concurrent}, 题目范围={question_ranges if question_ranges else "全部"}')
    
    # 运行主函数
    asyncio.run(main(parquet_path, max_concurrent, question_ranges))