import json

f = open('question-v1.json', 'r', encoding='utf-8')
data = json.load(f)
f.close()

def find_example(data, condition, max_examples=5):
    examples = []
    for item in data:
        if condition(item):
            examples.append(item)
            if len(examples) >= max_examples:
                break
    return examples

print("="*80)
print("1. 不定积分 (have_indefinite=True) 的答案格式 - 包含 +C")
print("="*80)
ex1 = find_example(data, lambda x: x['tag']['problem_type'] == 'int' and x['tag']['have_indefinite'] == True)
for e in ex1[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()

print("="*80)
print("2. 定积分 (have_definite=True) 的答案格式 - 具体数值结果")
print("="*80)
ex2 = find_example(data, lambda x: x['tag']['problem_type'] == 'int' and x['tag']['have_definite'] == True)
for e in ex2[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()

print("="*80)
print("3. symbolic=True 的答案格式 - 可能需要符号化简")
print("="*80)
ex3 = find_example(data, lambda x: x['tag']['symbolic'] == True and x['tag']['problem_type'] in ['int', 'diff'])
for e in ex3[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()

print("="*80)
print("4. is_multi=True 的答案格式 - 多项选择题")
print("="*80)
ex4 = find_example(data, lambda x: x['tag']['is_multi'] == True)
for e in ex4[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()

print("="*80)
print("5. sum (求和题) 的答案格式")
print("="*80)
ex5 = find_example(data, lambda x: x['tag']['problem_type'] == 'sum')
for e in ex5[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()

print("="*80)
print("6. diff (求导题) 的答案格式")
print("="*80)
ex6 = find_example(data, lambda x: x['tag']['problem_type'] == 'diff')
for e in ex6[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()

print("="*80)
print("7. is_divergent=True 的答案格式 - 发散积分")
print("="*80)
ex7 = find_example(data, lambda x: x['tag']['is_divergent'] == True)
for e in ex7[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()

print("="*80)
print("8. mix (混合题) 的答案格式")
print("="*80)
ex8 = find_example(data, lambda x: x['tag']['problem_type'] == 'mix')
for e in ex8[:2]:
    print(f"ID: {e['id']}")
    print(f"问题: {e['question']}")
    print(f"答案: {e['answer']}")
    print()
