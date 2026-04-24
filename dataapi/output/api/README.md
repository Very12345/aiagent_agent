# DuckDB API 接口 - 积分题目数据管理

这是一个为积分题目数据设计的DuckDB数据库访问接口，支持直接查询Parquet文件、导入数据到DuckDB表、执行SQL查询等功能。

## 安装依赖

```bash
pip install duckdb pyarrow
```

> **注意**：本API依赖 `integral_problem_schema.py` 文件来定义积分题目的数据结构规范。请确保该文件与 `api.py` 位于同一目录下。

## 快速开始

### 1. 基本用法

```python
from api import DB

# 创建数据库连接（内存数据库）
with DB() as db:
    # 导入Parquet数据到表
    db.from_parquet('积分题目示例数据.parquet', 'integral_problems')
    
    # 执行SQL查询
    results = db.execute("SELECT question, answer FROM integral_problems LIMIT 5")
    print(results)
```

### 2. 直接查询Parquet文件（无需导入）

```python
from api import DB

with DB() as db:
    # 直接查询Parquet文件中的数据
    results = db.query_parquet('积分题目示例数据.parquet', 'tag.problem_type = "int"')
    print(results)
```

### 3. 获取积分题目统计信息

```python
from api import DB

with DB() as db:
    # 获取统计信息
    stats = db.get_problem_statistics()
    print(f"总题数: {stats['total']}")
    print(f"积分题数量: {stats['by_problem_type'].get('int', 0)}")
    print(f"定积分题数量: {stats['definite_count']}")
    print(f"不定积分题数量: {stats['indefinite_count']}")
    print(f"发散题数量: {stats['divergent_count']}")
```

## API 参考

### `class DB(db_path: str = ":memory:", read_only: bool = False)`

DuckDB数据库连接管理器。

**参数：**
- `db_path`: 数据库路径，`:memory:`表示内存数据库
- `read_only`: 是否只读模式

### 主要方法

#### `from_parquet(parquet_path: str, table_name: str, overwrite: bool = True)`
从Parquet文件导入数据到DuckDB表。

#### `execute(query: str, params: Optional[tuple] = None)`
执行SQL查询并返回结果字典列表。

#### `fetchone(query: str, params: Optional[tuple] = None)`
执行查询并返回第一行结果。

#### `fetchall(query: str, params: Optional[tuple] = None)`
执行查询并返回所有结果。

#### `query_parquet(parquet_path: str, query: str)`
直接查询Parquet文件（不导入到表）。

#### `get_problem_statistics()`
获取积分题目统计信息，返回包含以下字段的字典：
- `total`: 总题数
- `by_problem_type`: 按problem_type分类的题数统计（使用`AS problem_type`别名）
- `definite_count`: 定积分题数量
- `indefinite_count`: 不定积分题数量  
- `divergent_count`: 发散题数量

#### `create_integral_problems_table(parquet_path: str = None)`
创建积分题目表（如果提供Parquet文件则导入数据）。

## 文件结构

- `api.py`: 主要API接口文件
- `README.md`: 项目文档
- `积分题目示例数据.parquet`: 示例数据文件
- `integral_problem_schema.py`: 积分题目数据Schema定义（必需依赖）
- `validate.py`: 数据验证工具
- `convert_to_parquet.py`: JSON转Parquet转换工具
- `test.py`: 测试脚本

## 许可证

MIT License