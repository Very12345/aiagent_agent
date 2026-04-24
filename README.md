# AI Agent 工作流系统

一个基于 Codex 的 AI Agent 工作流管理系统，支持批量问题处理、并发控制和自动化工作流执行。

## 概述

本系统提供了一个完整的 AI Agent 工作流框架，支持：
- 批量处理问题数据（支持 Parquet 格式）
- 并发控制，同时处理多个问题
- 自动化工作流执行（规划、构建、评估）
- 工作空间管理和结果打包
- 完整的日志记录和错误处理

## 主要特性

- **批量处理**: 从 Parquet 文件加载问题并批量处理
- **并发控制**: 使用信号量控制同时处理的问题数量
- **工作流管理**: 支持 Planner、Builder、Evaluator 三阶段工作流
- **自动打包**: 工作完成后自动打包工作空间为 ZIP 文件
- **编码兼容**: 解决 Windows GBK 编码问题，支持 UTF-8
- **独立工作空间**: 每个问题拥有独立的工作空间，避免冲突

## 目录结构

```
aiagent_agent/
├── main.py                 # 主程序入口，工作流引擎
├── run.py                  # 批量处理脚本
├── template/               # 工作流模板
│   ├── workflow/          # 工作流定义
│   │   ├── agent/
│   │   │   ├── planner/   # 规划代理
│   │   │   ├── builder/   # 构建代理
│   │   │   └── evaluator/ # 评估代理
│   │   └── workflow.json  # 工作流配置
│   └── question.json      # 示例问题
├── env/                    # 虚拟环境和依赖
└── workspace/             # 工作空间目录
```

## 快速开始

### 单个问题处理

```bash
# 使用命令行参数处理单个问题
python main.py -question_content "你的问题内容"

# 指定工作空间
python main.py -question_content "你的问题内容" -workspace "custom_workspace"

# 从文件读取问题
python main.py -question_file "question.json"
```

### 批量处理问题

```bash
# 从 Parquet 文件批量处理问题
python run.py ./question-v1.parquet

# 指定并发数（默认8）
python run.py ./question-v1.parquet 4

# 高并发处理（适合高性能系统）
python run.py ./question-v1.parquet 16
```

### 使用自定义工作流

```bash
# 使用 ZIP 格式的工作流
python main.py -workflow_file "workflow.zip"

# 使用目录格式的工作流
python main.py -workflow_dir "./template/workflow"
```

## 工作流程

### 1. 规划阶段 (Planner)
- 读取问题内容
- 分析问题并生成执行计划
- 保存计划到 `plan.json`

### 2. 构建阶段 (Builder)
- 读取执行计划
- 根据计划构建解决方案
- 保存解决方案到 `solution.json`

### 3. 评估阶段 (Evaluator)
- 读取解决方案
- 评估解决方案质量
- 保存评估结果到 `evaluation.json`

## 批量处理详解

### 并发控制

系统使用异步并发处理多个问题，通过信号量控制并发数：

```python
# 默认并发数：8
python run.py ./question-v1.parquet

# 自定义并发数：4
python run.py ./question-v1.parquet 4
```

### 工作空间管理

每个问题都会获得独立的工作空间，格式为：
```
workspace/YYYY-MM-DD-HH-MM-SS+问题ID/
```

例如：
```
workspace/2026-04-24-19-30-45+20_37/
workspace/2026-04-24-19-30-45+20_38/
```

### 结果输出

处理完成后会生成结果文件：
- `question-v1.parquet.processed.json` - 处理结果统计
- `workspace/*/workspace.zip` - 工作空间打包文件

### 处理统计

系统会输出详细的处理统计信息：
```
摘要:
  总共处理的问题数: 2332
  成功: 2300
  失败: 20
  超时: 10
  错误: 2
  跳过: 0
```

## 配置说明

### 环境要求

- Python 3.8+
- Codex 应用服务器
- 依赖包：`pyarrow`, `asyncio`, `pathlib`

### 编码设置

系统已配置 UTF-8 编码，解决 Windows GBK 编码问题：
- 环境变量：`PYTHONIOENCODING=utf-8`
- 文件编码：`encoding='utf-8'`
- 错误处理：`errors='replace'`

### 超时设置

单个问题处理超时时间：5分钟（可在 `run.py` 中调整）

## 工作流模板

### 自定义代理

在 `template/workflow/agent/` 目录下创建自定义代理：

```python
class Main:
    def __init__(self, codex, workspace, questionspace, err_logger, info_logger):
        self.codex = codex
        self.workspace = workspace
        self.questionspace = questionspace
        self.err_logger = err_logger
        self.info_logger = info_logger
    
    async def run(self) -> dict:
        # 实现你的逻辑
        pass
```

### 工作流配置

在 `workflow.json` 中定义工作流步骤：

```json
{
  "name": "自定义工作流",
  "tasks": [
    {
      "name": "步骤1",
      "agent": "planner"
    },
    {
      "name": "步骤2",
      "agent": "builder"
    }
  ]
}
```

## 故障排除

### 编码错误

如果遇到编码错误，确保：
- 设置环境变量 `PYTHONIOENCODING=utf-8`
- 使用 UTF-8 编码的终端

### 工作空间冲突

系统已自动处理工作空间冲突，每个问题都有唯一的工作空间。

### 并发问题

如果遇到并发问题：
- 降低并发数：`python run.py ./question-v1.parquet 4`
- 检查系统资源使用情况

## 开发

### 添加新的代理类型

1. 在 `template/workflow/agent/` 下创建新目录
2. 实现 `Main` 类
3. 在 `workflow.json` 中配置

### 修改工作流逻辑

1. 编辑 `main.py` 中的 `AsyncWorkflowEngine` 类
2. 修改 `run.py` 中的处理逻辑
3. 测试修改后的功能

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 联系方式

如有问题或建议，请在 GitHub 上提交 Issue 或联系维护者。