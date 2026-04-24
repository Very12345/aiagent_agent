"""
积分题目数据格式规范 v1.0 - PyArrow Schema 定义

本文档面向 AI Infrastructure 组，定义积分/求和题目的标准数据格式，
用于数据集构建、存储和加载。

作者：数据组
版本：1.0
最后更新：2026-04-15
"""

import pyarrow as pa
import json

INTEGRAL_PROBLEM_SCHEMA = pa.schema([
    pa.field('question', pa.string(), nullable=False, metadata={
        'description': '题目内容，运算符号用文本表达',
        'constraints': '["运算符号用文本表达","格式灵活","完整自洽","符号说明完整","唯一积分操作","非证明题格式","支持积分/求和"]'
    }),

    pa.field('answer', pa.string(), nullable=False, metadata={
        'description': '最终答案表达式',
        'constraints': '["仅提供最终结果","不包含解题过程","保持最简形式"]'
    }),

    pa.field('solution', pa.string(), nullable=False, metadata={
        'description': '纯文本解题过程',
        'constraints': '["纯文本格式","直接摘录文本"]'
    }),

    pa.field('tag', pa.struct([
        pa.field('tools_solvable', pa.list_(pa.string()), nullable=False),
        pa.field('symbolic', pa.bool_(), nullable=False),
        pa.field('problem_type', pa.dictionary('int8', pa.string()), nullable=False),
        pa.field('pure_int', pa.bool_(), nullable=False),
        pa.field('have_definite', pa.bool_(), nullable=False),
        pa.field('have_indefinite', pa.bool_(), nullable=False),
        pa.field('is_multi', pa.bool_(), nullable=False),
        pa.field('is_divergent', pa.bool_(), nullable=False)
    ]), nullable=False)

], metadata={
    'name': 'integral_problem',
    'version': '1.0',
    'description': 'Integral/Sum problem data format for Phy-LLM',
    'maintainer': 'Data-Group',
    'total_fields': '4',
    'tag_subfields': '8'
})


def validate_problem_data(table):
    """验证积分题目数据是否符合规范"""
    required_fields = ['question', 'answer', 'solution', 'tag']

    for field in required_fields:
        if field not in table.column_names:
            raise ValueError(f"缺少必填字段：{field}")

    tag_type = table.schema.field('tag').type
    if not pa.types.is_struct(tag_type):
        raise ValueError("tag 字段必须是 struct 类型")

    required_tag_fields = ['tools_solvable', 'symbolic', 'problem_type',
                           'pure_int', 'have_definite', 'have_indefinite',
                           'is_multi', 'is_divergent']

    for field in required_tag_fields:
        if field not in [f.name for f in tag_type]:
            raise ValueError(f"tag 缺少必填子字段：{field}")

    return True


def get_schema():
    """返回 Schema 对象"""
    return INTEGRAL_PROBLEM_SCHEMA


def print_schema_info():
    """打印 Schema 信息"""
    print("=" * 60)
    print("积分题目数据格式规范 v1.0")
    print("=" * 60)
    print(f"字段总数：4 个核心字段 + 8 个 tag 子字段")
    print(f"字段列表：{[f.name for f in INTEGRAL_PROBLEM_SCHEMA]}")
    print("=" * 60)
