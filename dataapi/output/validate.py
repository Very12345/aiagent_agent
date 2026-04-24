"""
积分题目数据验证脚本

验证 JSON 数据是否符合规范文档定义的所有约束条件。
"""

import json
import re
from typing import Dict, List, Any, Tuple


class IntegralProblemValidator:
    """积分题目数据验证器"""

    # 合法 problem_type 枚举值
    VALID_PROBLEM_TYPES = ['int', 'sum', 'mix']

    # 证明题关键词（出现这些词说明是证明题，不符合规范）
    PROOF_KEYWORDS = ['证明', 'prove', 'show that', 'verify that']

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        验证单条数据

        Args:
            data: JSON 对象

        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # 检查必填字段
        required_fields = ['question', 'answer', 'solution', 'tag']
        for field in required_fields:
            if field not in data:
                self.errors.append(f"缺少必填字段：{field}")

        if self.errors:
            return False, self.errors, self.warnings

        # 验证各字段
        self._validate_question(data['question'])
        self._validate_answer(data['answer'])
        self._validate_solution(data['solution'])
        self._validate_tag(data['tag'])

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_question(self, question: str) -> None:
        """验证 question 字段"""

        # 约束 1: 不能为空
        if not question or not question.strip():
            self.errors.append("question 不能为空")
            return

        # 约束 2: 运算符号用文本表达（检查是否有 Unicode 数学符号）
        unicode_math_chars = ['∫', 'Σ', '∮', '∬', '∭', '∂', '∇', '∞', '≠', '≤', '≥']
        for char in unicode_math_chars:
            if char in question:
                self.errors.append(f"question 包含 Unicode 数学符号 '{char}'，应使用文本格式")

        # 约束 3: 完整自洽（检查是否有"其中 X 为..."的说明）
        # 提取所有变量（单字母或小写字母序列）
        variables = re.findall(r'\b([a-z])\b', question.lower())
        # 检查是否有变量说明
        has_variable_def = '其中' in question or 'where' in question.lower()
        if variables and not has_variable_def:
            self.warnings.append(f"question 包含变量 {variables}，建议添加'其中 X 为...'说明")

        # 约束 4: 唯一积分操作（检查是否有多个积分）
        int_count = question.lower().count('int(')
        if int_count > 1:
            self.errors.append(f"question 包含 {int_count} 个积分操作，只能包含 1 个")

        # 约束 5: 非证明题格式
        for keyword in self.PROOF_KEYWORDS:
            if keyword.lower() in question.lower():
                self.errors.append(f"question 是证明题格式（包含关键词 '{keyword}'），应为计算题")

    def _validate_answer(self, answer: str) -> None:
        """验证 answer 字段"""

        if not answer or not answer.strip():
            self.errors.append("answer 不能为空")
            return

        # 检查是否包含解题过程关键词
        process_keywords = ['解：', '解答：', '因为', '所以', '步骤', 'step']
        for keyword in process_keywords:
            if keyword in answer:
                self.errors.append(f"answer 包含解题过程关键词 '{keyword}'，应仅保留最终结果")

    def _validate_solution(self, solution: str) -> None:
        """验证 solution 字段"""

        if not solution or not solution.strip():
            self.errors.append("solution 不能为空")
            return

        # 检查是否为纯文本（不支持 LaTeX）
        latex_patterns = [r'\$', r'\\[a-z]+', r'\[', r'\]']
        for pattern in latex_patterns:
            if re.search(pattern, solution):
                self.warnings.append(f"solution 可能包含 LaTeX 格式：{pattern}")

    def _validate_tag(self, tag: Dict[str, Any]) -> None:
        """验证 tag 字段"""

        required_tag_fields = [
            'tools_solvable', 'symbolic', 'problem_type', 'pure_int',
            'have_definite', 'have_indefinite', 'is_multi', 'is_divergent'
        ]

        # 检查必填子字段
        for field in required_tag_fields:
            if field not in tag:
                self.errors.append(f"tag 缺少必填子字段：{field}")

        if self.errors:
            return

        # 验证 tools_solvable 是列表
        if not isinstance(tag['tools_solvable'], list):
            self.errors.append("tag.tools_solvable 必须是列表类型")

        # 验证 symbolic 是布尔值
        if not isinstance(tag['symbolic'], bool):
            self.errors.append("tag.symbolic 必须是布尔值")

        # 验证 problem_type 是合法枚举值
        if tag['problem_type'] not in self.VALID_PROBLEM_TYPES:
            self.errors.append(f"tag.problem_type 必须是 {self.VALID_PROBLEM_TYPES} 之一")

        # 验证其他布尔字段
        for field in ['pure_int', 'have_definite', 'have_indefinite', 'is_multi', 'is_divergent']:
            if not isinstance(tag[field], bool):
                self.errors.append(f"tag.{field} 必须是布尔值")

        # 逻辑一致性检查
        self._validate_tag_logic(tag)

    def _validate_tag_logic(self, tag: Dict[str, Any]) -> None:
        """验证 tag 字段的逻辑一致性"""

        # 定积分和不定积分不能同时为 True（逻辑上不严谨，但允许存在）
        # have_definite 和 have_indefinite 至少有一个为 False 是合理的

        # 如果是发散，通常应该有定积分或求和
        if tag.get('is_divergent') and not tag.get('have_definite'):
            self.warnings.append("is_divergent=True 但 have_definite=False，请确认是否正确")

        # problem_type 与积分/求和标记的一致性
        if tag['problem_type'] == 'int' and not (tag['have_definite'] or tag['have_indefinite']):
            self.warnings.append("problem_type='int' 但没有定积分或不定积分标记")


def validate_json_file(file_path: str) -> Dict[str, Any]:
    """
    验证 JSON 文件中的所有数据

    Args:
        file_path: JSON 文件路径

    Returns:
        验证结果报告
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        return {
            'valid': False,
            'error': 'JSON 根节点必须是数组',
            'total': 0,
            'passed': 0,
            'failed': 0,
            'details': []
        }

    validator = IntegralProblemValidator()
    details = []
    passed = 0
    failed = 0

    for i, item in enumerate(data):
        is_valid, errors, warnings = validator.validate(item)

        if is_valid:
            passed += 1
        else:
            failed += 1

        details.append({
            'index': i,
            'question_preview': item.get('question', '')[:50] + '...',
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings
        })

    return {
        'valid': failed == 0,
        'total': len(data),
        'passed': passed,
        'failed': failed,
        'details': details
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = '积分题目示例数据.json'

    print(f"验证文件：{file_path}")
    print("=" * 60)

    result = validate_json_file(file_path)

    if 'error' in result:
        print(f"错误：{result['error']}")
    else:
        print(f"总记录数：{result['total']}")
        print(f"通过：{result['passed']}")
        print(f"失败：{result['failed']}")
        print(f"验证结果：{'[通过]' if result['valid'] else '[失败]'}")

        if result['details']:
            print("\n详细报告:")
            for detail in result['details']:
                status = '[OK]' if detail['valid'] else '[FAIL]'
                print(f"  [{status}] #{detail['index']}: {detail['question_preview']}")
                if detail['errors']:
                    for err in detail['errors']:
                        print(f"      错误：{err}")
                if detail['warnings']:
                    for warn in detail['warnings']:
                        print(f"      警告：{warn}")
