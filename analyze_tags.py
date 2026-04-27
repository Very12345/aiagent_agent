import json

f = open('question-v1.json', 'r', encoding='utf-8')
data = json.load(f)
f.close()

tags_count = {
    'problem_type': {},
    'symbolic': {},
    'pure_int': {},
    'have_definite': {},
    'have_indefinite': {},
    'is_multi': {},
    'is_divergent': {},
    'tools_solvable': []
}

for item in data:
    tag = item['tag']
    pt = tag['problem_type']
    tags_count['problem_type'][pt] = tags_count['problem_type'].get(pt, 0) + 1
    tags_count['symbolic'][tag['symbolic']] = tags_count['symbolic'].get(tag['symbolic'], 0) + 1
    tags_count['pure_int'][tag['pure_int']] = tags_count['pure_int'].get(tag['pure_int'], 0) + 1
    tags_count['have_definite'][tag['have_definite']] = tags_count['have_definite'].get(tag['have_definite'], 0) + 1
    tags_count['have_indefinite'][tag['have_indefinite']] = tags_count['have_indefinite'].get(tag['have_indefinite'], 0) + 1
    tags_count['is_multi'][tag['is_multi']] = tags_count['is_multi'].get(tag['is_multi'], 0) + 1
    tags_count['is_divergent'][tag['is_divergent']] = tags_count['is_divergent'].get(tag['is_divergent'], 0) + 1
    if tag['tools_solvable']:
        tags_count['tools_solvable'].append(tag['tools_solvable'])

print('=== problem_type 分布 ===')
for k, v in sorted(tags_count['problem_type'].items()):
    print(f'  {k}: {v}')

print('\n=== symbolic 分布 ===')
for k, v in tags_count['symbolic'].items():
    print(f'  {k}: {v}')

print('\n=== pure_int 分布 ===')
for k, v in tags_count['pure_int'].items():
    print(f'  {k}: {v}')

print('\n=== have_definite 分布 ===')
for k, v in tags_count['have_definite'].items():
    print(f'  {k}: {v}')

print('\n=== have_indefinite 分布 ===')
for k, v in tags_count['have_indefinite'].items():
    print(f'  {k}: {v}')

print('\n=== is_multi 分布 ===')
for k, v in tags_count['is_multi'].items():
    print(f'  {k}: {v}')

print('\n=== is_divergent 分布 ===')
for k, v in tags_count['is_divergent'].items():
    print(f'  {k}: {v}')

print('\n=== tools_solvable 非空数量 ===')
print(f'  {len(tags_count["tools_solvable"])} 个')
if tags_count['tools_solvable']:
    print('  前3个示例:', tags_count['tools_solvable'][:3])
