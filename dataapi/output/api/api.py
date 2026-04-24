"""
DuckDB API 接口 - 积分题目数据管理

提供对积分题目数据的DuckDB访问接口，支持：
- 直接查询Parquet文件
- 导入Parquet文件到DuckDB表
- 执行SQL查询
- 表管理操作
"""

import duckdb
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


class DB:
    """DuckDB数据库连接管理器"""
    
    def __init__(self, db_path: str = ":memory:", read_only: bool = False):
        """
        初始化DuckDB连接
        
        Args:
            db_path: 数据库路径，":memory:"表示内存数据库
            read_only: 是否只读模式
        """
        self.db_path = db_path
        self.read_only = read_only
        self._conn = None
    
    def __enter__(self):
        """上下文管理器入口"""
        try:
            if self.db_path == ":memory:":
                # 内存数据库
                self._conn = duckdb.connect()
            else:
                # 文件数据库
                self._conn = duckdb.connect(self.db_path, read_only=self.read_only)
            
            # 加载必要的扩展
            self._conn.execute("INSTALL httpfs")
            self._conn.execute("LOAD httpfs")
            self._conn.execute("INSTALL parquet")
            self._conn.execute("LOAD parquet")
            
            return self
        except Exception as e:
            if self._conn:
                self._conn.close()
            raise e
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self._conn:
            self._conn.close()
        return False
    
    def execute(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行SQL查询并返回结果
        
        Args:
            query: SQL查询语句
            params: 查询参数（用于防止SQL注入）
            
        Returns:
            查询结果列表，每个元素是字典形式的行数据
        """
        if not self._conn:
            raise RuntimeError("Database connection not established")
        
        try:
            if params:
                result = self._conn.execute(query, params)
            else:
                result = self._conn.execute(query)
            
            # 获取列名
            columns = [desc[0] for desc in result.description]
            
            # 获取所有行
            rows = result.fetchall()
            
            # 转换为字典列表
            result_list = []
            for row in rows:
                result_list.append(dict(zip(columns, row)))
            
            return result_list
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")
    
    def fetchone(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """
        执行查询并返回第一行结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            第一行结果字典，或None
        """
        results = self.execute(query, params)
        return results[0] if results else None
    
    def fetchall(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询并返回所有结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            所有结果的字典列表
        """
        return self.execute(query, params)
    
    def from_parquet(self, parquet_path: str, table_name: str, 
                    overwrite: bool = True) -> None:
        """
        从Parquet文件导入数据到DuckDB表
        
        Args:
            parquet_path: Parquet文件路径
            table_name: 目标表名
            overwrite: 是否覆盖已存在的表
        """
        if not self._conn:
            raise RuntimeError("Database connection not established")
        
        try:
            # 检查Parquet文件是否存在
            if not os.path.exists(parquet_path):
                raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
            
            # 如果表已存在且需要覆盖，则删除
            if overwrite:
                try:
                    self._conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                except:
                    pass
            
            # 创建表并导入数据
            # DuckDB支持直接从Parquet文件创建表
            self._conn.execute(f"""
                CREATE TABLE {table_name} AS 
                SELECT * FROM read_parquet('{parquet_path}')
            """)
            
        except Exception as e:
            raise RuntimeError(f"Failed to import from Parquet: {e}")
    
    def list_tables(self) -> List[str]:
        """
        列出所有表
        
        Returns:
            表名列表
        """
        if not self._conn:
            raise RuntimeError("Database connection not established")
        
        try:
            result = self._conn.execute("SELECT table_name FROM duckdb_tables()")
            tables = [row[0] for row in result.fetchall()]
            return tables
        except Exception as e:
            raise RuntimeError(f"Failed to list tables: {e}")
    
    def table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表信息
        
        Args:
            table_name: 表名
            
        Returns:
            表信息字典
        """
        if not self._conn:
            raise RuntimeError("Database connection not established")
        
        try:
            # 获取表结构
            result = self._conn.execute(f"DESCRIBE {table_name}")
            columns = result.fetchall()
            
            # 获取行数
            count_result = self._conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = count_result.fetchone()[0]
            
            return {
                'table_name': table_name,
                'row_count': row_count,
                'columns': [
                    {
                        'name': col[0],
                        'type': col[1],
                        'null': col[2],
                        'key': col[3],
                        'default': col[4],
                        'extra': col[5]
                    }
                    for col in columns
                ]
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get table info: {e}")
    
    def query_parquet(self, parquet_path: str, query: str) -> List[Dict[str, Any]]:
        """
        直接查询Parquet文件（不导入到表）
        
        Args:
            parquet_path: Parquet文件路径
            query: SQL查询语句（可以引用'parquet_file'作为表名）
            
        Returns:
            查询结果
        """
        if not self._conn:
            raise RuntimeError("Database connection not established")
        
        try:
            # DuckDB支持直接查询Parquet文件
            # 使用read_parquet函数
            full_query = f"SELECT * FROM (SELECT * FROM read_parquet('{parquet_path}')) t WHERE 1=1"
            if query.strip().upper().startswith('SELECT'):
                full_query = f"SELECT * FROM (SELECT * FROM read_parquet('{parquet_path}')) t WHERE 1=1"
                # 简单的查询重写，实际应用中可能需要更复杂的解析
            else:
                # 假设query是WHERE条件
                full_query = f"SELECT * FROM read_parquet('{parquet_path}') WHERE {query}"
            
            return self.execute(full_query)
        except Exception as e:
            raise RuntimeError(f"Failed to query Parquet file: {e}")
    
    def create_integral_problems_table(self, parquet_path: str = None) -> None:
        """
        创建积分题目表（如果parquet_path提供则导入数据）
        
        Args:
            parquet_path: Parquet文件路径（可选）
        """
        if not self._conn:
            raise RuntimeError("Database connection not established")
        
        # 如果提供了Parquet文件，则导入数据
        # DuckDB的read_parquet会自动根据Parquet文件的Schema创建结构体列
        if parquet_path:
            self.from_parquet(parquet_path, "integral_problems", overwrite=True)
    
    def get_problem_statistics(self) -> Dict[str, Any]:
        """
        获取积分题目统计信息
        
        Returns:
            统计信息字典
        """
        if not self._conn:
            raise RuntimeError("Database connection not established")
        
        try:
            # 基本统计
            stats = {}
            
            # 总题数
            total = self.fetchone("SELECT COUNT(*) as count FROM integral_problems")
            stats['total'] = total['count'] if total else 0
            
            # 按problem_type统计
            problem_types = self.fetchall("""
                SELECT tag.problem_type AS problem_type, COUNT(*) as count 
                FROM integral_problems 
                GROUP BY tag.problem_type
            """)
            stats['by_problem_type'] = {item['problem_type']: item['count'] for item in problem_types}
            
            # 定积分/不定积分统计
            definite_stats = self.fetchone("""
                SELECT COUNT(*) as count FROM integral_problems 
                WHERE tag.have_definite = true
            """)
            stats['definite_count'] = definite_stats['count'] if definite_stats else 0
            
            indefinite_stats = self.fetchone("""
                SELECT COUNT(*) as count FROM integral_problems 
                WHERE tag.have_indefinite = true
            """)
            stats['indefinite_count'] = indefinite_stats['count'] if indefinite_stats else 0
            
            # 发散题统计
            divergent_stats = self.fetchone("""
                SELECT COUNT(*) as count FROM integral_problems 
                WHERE tag.is_divergent = true
            """)
            stats['divergent_count'] = divergent_stats['count'] if divergent_stats else 0
            
            return stats
        except Exception as e:
            raise RuntimeError(f"Failed to get statistics: {e}")


# 使用示例和测试代码
if __name__ == "__main__":
    # 示例用法
    print("DuckDB API 接口 - 积分题目数据管理")
    print("=" * 50)
    print("示例用法:")
    print("1. 创建数据库连接:")
    print("   with DB() as db:")
    print("       db.from_parquet('积分题目示例数据.parquet', 'integral_problems')")
    print("       results = db.execute('SELECT * FROM integral_problems LIMIT 5')")
    print()
    print("2. 直接查询Parquet文件:")
    print("   with DB() as db:")
    print("       results = db.query_parquet('积分题目示例数据.parquet', 'tag_problem_type = \"int\"')")
    print()
    print("3. 获取统计信息:")
    print("   with DB() as db:")
    print("       stats = db.get_problem_statistics()")
    print("       print(stats)")