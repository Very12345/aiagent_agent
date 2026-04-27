import pandas as pd
import json

# 读取 parquet 文件
df = pd.read_parquet('question-v1.parquet')

# 将 DataFrame 转换为 JSON 格式
json_data = df.to_json(orient='records', force_ascii=False, indent=2)

# 保存为 JSON 文件
with open('question-v1.json', 'w', encoding='utf-8') as f:
    f.write(json_data)

print('转换完成！已生成 question-v1.json 文件')
