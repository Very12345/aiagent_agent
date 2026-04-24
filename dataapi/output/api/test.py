from api import DB
import os

# 确保文件名和你本地的一致
FILE_NAME = '积分题目示例数据.parquet'

def test_duckdb_interface():
    if not os.path.exists(FILE_NAME):
        print(f"❌ 找不到文件: {FILE_NAME}")
        return

    # 使用上下文管理器启动数据库
    with DB(db_path="phy_test.duckdb") as db:
        print("--- 开始测试 ---")
        
        # 1. 测试直接从 Parquet 导入
        try:
            db.create_integral_problems_table(FILE_NAME)
            print("✅ 成功创建表并导入 Parquet 数据")
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return

        # 2. 测试基本查询
        tables = db.list_tables()
        print(f"当前数据库中的表: {tables}")

        # 3. 执行业务统计查询
        # 注意：这里根据你的 API 实现，确认是用 tag.is_multi 还是 tag_is_multi
        try:
            stats = db.get_problem_statistics()
            print(f"\n--- 数据统计结果 ---")
            print(f"总题目数: {stats.get('total')}")
            print(f"定积分(Definite): {stats.get('definite_count')}")
            print(f"发散题(Divergent): {stats.get('divergent_count')}")
        except Exception as e:
            print(f"⚠️ 统计查询失败（可能是字段名不匹配）: {e}")

        # 4. 测试单条数据获取
        sample = db.fetchone("SELECT question, answer FROM integral_problems LIMIT 1")
        if sample:
            print(f"\n--- 样本数据 ---")
            print(f"题目: {sample['question']}")
            print(f"答案: {sample['answer']}")

if __name__ == "__main__":
    test_duckdb_interface()