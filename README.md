# AI Agent Workflow Engine 使用指南

## 系统概述

这是一个基于异步工作流引擎的AI智能体系统，集成了Codex API，支持模块化的智能体协作。系统采用JSON配置化的工作流设计，支持多种执行模式，能够自动处理问题解决、方案构建和评估优化的完整流程。

## 系统架构

```
aiagent_agent/
├── main.py                 # 主程序入口，异步工作流引擎
├── workflow.json           # 工作流配置
├── question/ques.json      # 问题定义
├── agent/                  # 智能体模块
│   ├── planner/           # 规划器智能体
│   ├── builder/           # 构建器智能体
│   └── evaluator/         # 评估器智能体
├── workspace/             # 工作空间输出
│   ├── plan/             # 规划结果
│   ├── solution/         # 解决方案
│   └── evaluation/       # 评估结果
└── env/                  # codex_app_server依赖环境
```

## 快速开始

### 1. 问题配置 (question/ques.json)

在`ques.json`中定义需要解决的问题：

```json
{
  "problem": "你的问题描述"
}
```

### 2. 工作流配置 (workflow.json)

配置任务执行流程，支持多种模式：

```json
{
  "workflow_name": "AI智能体工作流",
  "type": "pipeline",
  "name": "标准构建链",
  "tasks": [
    {
      "name": "load_agent",
      "type": "load",
      "agents": ["planner", "builder", "evaluator"]
    },
    {
      "name": "规划阶段",
      "type": "task",
      "func": "planner"
    },
    {
      "name": "优化循环",
      "type": "loop",
      "times": 3,
      "break_condition": "result.get(\"score\") >= 98",
      "body": {
        "type": "pipeline",
        "name": "构建评估链",
        "tasks": [
          {
            "name": "构建阶段",
            "type": "task",
            "func": "builder"
          },
          {
            "name": "评估阶段",
            "type": "task",
            "func": "evaluator"
          }
        ]
      }
    }
  ]
}
```

**工作流模式说明：**

- **load**: 加载智能体模块
- **task**: 执行单个任务
- **pipeline**: 顺序执行多个任务
- **parallel**: 并行执行多个任务
- **loop**: 循环执行，支持中断条件

## 智能体系统

系统包含三个核心智能体，每个智能体都有独立的职责和提示配置：

### 规划器 (agent/planner/)

**职责**: 分析问题并生成解决方案的详细计划

**文件结构**:
- `agent.py` - 智能体主类，继承自`Main`基类
- `prompt.md` - 开发者指令（自定义提示）
- `prompt_base.md` - 基础指令

**提示配置示例**:
```markdown
# prompt.md
你是一个规划器。
读取输入问题并给出解决计划。
你的输出必须是JSON格式，包含问题和计划。

# prompt_base.md  
输出包含步骤、资源和成功标准的有效JSON。
```

### 构建器 (agent/builder/)

**职责**: 根据规划结果生成具体的解决方案

**提示配置示例**:
```markdown
# prompt.md
你是一个构建器。
读取输入问题和计划并给出解决方案。

# prompt_base.md
输出包含结果的有效JSON。
```

### 评估器 (agent/evaluator/)

**职责**: 评估解决方案的质量并提供反馈

**提示配置示例**:
```markdown
# prompt.md
你是一个评估器。
评估解决方案的质量。

# prompt_base.md
输出包含评分和反馈的有效JSON。
```

## 技术架构

### 异步工作流引擎 (AsyncWorkflowEngine)

核心引擎类，支持：
- **异步任务执行**: 基于asyncio的异步执行模型
- **智能体动态加载**: 运行时加载和实例化智能体模块
- **参数替换**: 支持循环索引等动态参数
- **错误处理**: 完善的异常处理和日志记录

### Codex API 集成

系统自动集成codex_app_server，提供：
- **自动依赖检查**: 启动时自动检查并安装依赖
- **线程管理**: 智能的API线程管理和资源分配
- **模型配置**: 支持多种模型配置（默认使用qwen3.5-plus）

## 运行方式

```bash
python main.py
```

**系统启动流程**:
1. **依赖检查**: 自动检查并安装codex_app_server依赖
2. **环境初始化**: 创建Codex实例和工作目录
3. **智能体加载**: 动态加载配置的智能体模块
4. **工作流执行**: 按照workflow.json配置执行任务链
5. **结果输出**: 生成结果文件到workspace目录

## 输出文件结构

```
workspace/
├── plan/
│   └── plan.json          # 规划器生成的解决方案计划
├── solution/
│   └── solu.json          # 构建器生成的解决方案
└── evaluation/
    └── eval.json          # 评估器生成的评估结果
```

## 高级配置

### 添加自定义智能体

1. **创建智能体目录**: 在`agent/`下创建新目录
2. **实现智能体类**: 创建`agent.py`，继承`Main`基类
3. **配置提示文件**: 创建`prompt.md`和`prompt_base.md`
4. **更新工作流**: 在workflow.json中添加智能体引用

**智能体类示例**:
```python
class Main:
    """自定义智能体"""
    
    def __init__(self, codex: Codex, workdir: Path):
        self.codex = codex
        self.workdir = workdir
    
    async def run(self) -> dict:
        """智能体主逻辑"""
        # 实现你的智能体逻辑
        return {"status": "success", "data": "结果"}
```

### 工作流模式详解

#### 顺序管线 (pipeline)
```json
{
  "type": "pipeline",
  "name": "任务链",
  "tasks": [任务1, 任务2, 任务3]
}
```

#### 并行执行 (parallel)  
```json
{
  "type": "parallel", 
  "name": "并行任务",
  "tasks": [任务A, 任务B, 任务C]
}
```

#### 循环执行 (loop)
```json
{
  "type": "loop",
  "name": "优化循环", 
  "times": 5,
  "break_condition": "result.get('score') >= 95",
  "body": {循环体任务}
}
```

## 故障排除

### 常见问题

1. **依赖安装失败**
   - 检查网络连接
   - 确认Python环境正确配置
   - 查看env目录下的pyproject.toml配置

2. **智能体加载失败**
   - 确认agent目录结构正确
   - 检查agent.py中的Main类定义
   - 验证提示文件存在且格式正确

3. **工作流执行错误**
   - 检查workflow.json语法正确性
   - 确认引用的智能体名称匹配
   - 查看日志文件获取详细信息

### 日志系统

系统自动生成日志文件：
- `log/{时间戳}_info.log` - 详细执行日志
- 控制台彩色输出 - 实时状态监控

## 开发指南

### 代码结构
- `main.py` - 主程序入口，包含异步引擎和任务注册
- `agent/*/agent.py` - 智能体实现类
- 采用模块化设计，易于扩展和维护

### 扩展建议
- 添加新的智能体类型
- 实现自定义工作流模式
- 集成更多AI模型和API
- 添加可视化监控界面

1. **依赖安装失败**：检查网络连接，手动运行`cd env && pip install -e .`
2. **JSON解析错误**：检查workflow.json格式是否正确
3. **任务执行失败**：确认对应的md提示文件存在且格式正确