"""
JSON → Parquet 转换脚本

将符合规范的积分题目 JSON 数据转换为 Parquet 格式。
"""

import json
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import List, Dict, Any

from integral_problem_schema import INTEGRAL_PROBLEM_SCHEMA


def json_to_parquet(json_path: str, parquet_path: str, compress: str = 'snappy') -> Dict[str, Any]:
    """
    将 JSON 文件转换为 Parquet 文件

    Args:
        json_path: 输入 JSON 文件路径
        parquet_path: 输出 Parquet 文件路径
        compress: 压缩方式（snappy/gzip/zstd）

    Returns:
        转换结果信息
    """
    # 读取 JSON 数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        return {'success': False, 'error': 'JSON 根节点必须是数组'}

    # 构建 PyArrow 表
    questions = []
    answers = []
    solutions = []
    tags = []

    for item in data:
        questions.append(item.get('question', ''))
        answers.append(item.get('answer', ''))
        solutions.append(item.get('solution', ''))

        # 构建 tag struct
        tag = item.get('tag', {})
        tags.append({
            'tools_solvable': tag.get('tools_solvable', []),
            'symbolic': tag.get('symbolic', False),
            'problem_type': tag.get('problem_type', ''),
            'pure_int': tag.get('pure_int', False),
            'have_definite': tag.get('have_definite', False),
            'have_indefinite': tag.get('have_indefinite', False),
            'is_multi': tag.get('is_multi', False),
            'is_divergent': tag.get('is_divergent', False)
        })

    # 创建 PyArrow 表
    table = pa.table({
        'question': questions,
        'answer': answers,
        'solution': solutions,
        'tag': tags
    }, schema=INTEGRAL_PROBLEM_SCHEMA)

    # 写入 Parquet 文件
    pq.write_table(table, parquet_path, compression=compress)

    # 计算统计信息
    file_size = Path(parquet_path).stat().st_size
    original_size = Path(json_path).stat().st_size

    return {
        'success': True,
        'input_file': json_path,
        'output_file': parquet_path,
        'input_size': original_size,
        'output_size': file_size,
        'compression_ratio': f"{file_size / original_size * 100:.1f}%",
        'row_count': len(data),
        'compression': compress
    }


def parquet_to_json(parquet_path: str, json_path: str) -> Dict[str, Any]:
    """
    将 Parquet 文件转换回 JSON（用于验证）

    Args:
        parquet_path: 输入 Parquet 文件路径
        json_path: 输出 JSON 文件路径

    Returns:
        转换结果信息
    """
    # 读取 Parquet 文件
    table = pq.read_table(parquet_path)

    # 转换为 Python 对象
    data = table.to_pylist()

    # 写入 JSON 文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        'success': True,
        'input_file': parquet_path,
        'output_file': json_path,
        'row_count': len(data)
    }


def print_parquet_info(parquet_path: str) -> None:
    """
    打印 Parquet 文件信息

    Args:
        parquet_path: Parquet 文件路径
    """
    parquet_file = pq.ParquetFile(parquet_path)
    metadata = parquet_file.metadata
    schema = parquet_file.schema_arrow

    print("=" * 60)
    print(f"Parquet 文件信息：{parquet_path}")
    print("=" * 60)
    print(f"行数量：{metadata.num_rows}")
    print(f"行组数量：{metadata.num_row_groups}")
    print(f"文件大小：{parquet_file.metadata.serialized_size} 字节")
    print(f"\nSchema:")
    for field in schema:
        print(f"  - {field.name}: {field.type}")
        if field.metadata:
            for key, value in field.metadata.items():
                print(f"      {key}: {value}")
    print("=" * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("用法：python convert_to_parquet.py <input.json> <output.parquet> [compression]")
        print("compression 可选：snappy (默认), gzip, zstd, none")
        sys.exit(1)

    json_path = sys.argv[1]
    parquet_path = sys.argv[2]
    compression = sys.argv[3] if len(sys.argv) > 3 else 'snappy'

    print(f"输入文件：{json_path}")
    print(f"输出文件：{parquet_path}")
    print(f"压缩方式：{compression}")
    print("-" * 60)

    result = json_to_parquet(json_path, parquet_path, compression)

    if result['success']:
        print("[OK] 转换成功!")
        print(f"  输入大小：{result['input_size']} 字节")
        print(f"  输出大小：{result['output_size']} 字节")
        print(f"  压缩比：{result['compression_ratio']}")
        print(f"  记录数：{result['row_count']}")

        # 打印 Parquet 文件详情
        print()
        print_parquet_info(parquet_path)
    else:
        print(f"[FAIL] 转换失败：{result.get('error', '未知错误')}")
        sys.exit(1)
