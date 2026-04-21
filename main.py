import asyncio
import json
import time
from pathlib import Path
import subprocess
import sys
import importlib    

def err_logger(msg: str):
    print(f"\033[91m{msg}\033[0m")
thisworktime=time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
def info_logger(msg: str):
    # 写在log文件夹时间+_info.log文件中
    log_file =  Path("log") / f"{thisworktime}_info.log"
    with open(log_file, "a",encoding="utf-8") as f:
        f.write(f"{msg}\n")
    if len(msg) > 30:
        print(f"\033[92m{msg[:30]+'...'}\033[0m")
    else:
        print(f"\033[92m{msg}\033[0m")
      
def check_and_install_codex_app_server():
    """检查 codex_app_server 是否存在，如果不存在则自动安装"""
    try:
        from codex_app_server import Codex, AppServerConfig
        return Codex, AppServerConfig
    except ImportError:
        print("❌ codex_app_server 未安装，正在自动安装...")
        
        # 切换到 env 目录
        env_dir = Path.cwd() / "env"
        if not env_dir.exists():
            err_logger(f"❌ env 目录不存在: {env_dir}")
            sys.exit(1)
        
        # 运行 pip install -e .
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                cwd=env_dir,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ codex_app_server 安装成功")
            print(result.stdout)
            result = subprocess.run(
                [sys.executable, Path("main.py")],
                cwd=Path.cwd(),
                text=True,
                check=True
            )
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"❌ 安装失败: {e}")
            print(f"错误输出: {e.stderr}")
            sys.exit(1)
        
        

Codex, AppServerConfig = check_and_install_codex_app_server()


  
# 任务注册表，用于存储已注册的任务类
TASK_REGISTRY = {}

def register_task(name: str):
    """装饰器：将任务类注册到 TASK_REGISTRY"""
    def wrapper(cls):
        TASK_REGISTRY[name] = cls
        return cls
    return wrapper



def get_task_registry(codex: Codex, workdir: Path) -> dict:
    """获取已实例化的任务注册表，将类转换为可调用方法"""
    registry = {}
    for name, cls in TASK_REGISTRY.items():
        instance = cls(codex, workdir)
        registry[name] = instance.run
    return registry

class AsyncWorkflowEngine:
    """异步工作流引擎：解析并执行 JSON 配置的工作流"""
    
    def __init__(self, workflow: dict, task_registry: dict, codex=None, workdir=None):
        self.workflow = workflow
        self.task_registry = task_registry
        self.codex = codex
        self.workdir = workdir

    def _replace_params(self, params, loop_index):
        """替换参数中的循环索引占位符"""
        if loop_index is None:
            return params
        s = json.dumps(params).replace("{{loop_index}}", str(loop_index))
        return json.loads(s)

    async def load_agent(self, agents):
        """加载智能体"""
        for agent in agents:
            #从agent对应目录加载agent.py文件
            agent_path = Path("agent") / agent / "agent.py"
            if not agent_path.exists():
                err_logger(f"智能体文件未找到: {agent_path}")
                exit(1)
            # 从agent/agent名目录的agent.py加载Main类
            module = importlib.import_module(f"agent.{agent}.agent")
            # 创建Main类的实例并存储实例本身，而不是run方法
            self.task_registry[agent] = module.Main(self.codex, self.workdir)
            info_logger(f"  [加载智能体] {agent}")

    async def execute(self, step, loop_index=None):
        """执行单个工作流步骤"""
        stype = step.get("type")
        name = step.get("name", "Unnamed")

        # 原子任务：异步执行单个函数
        if stype == "load":
            return await self.load_agent(step["agents"])
        
        elif stype == "task":
            agent_instance = self.task_registry[step["func"]]
            params = self._replace_params(step.get("params", {}), loop_index)
            info_logger(f"  [执行任务] {name}")
            if params:
                return await agent_instance.run(**params)
            else:
                return await agent_instance.run()

        # 顺序管线：按顺序执行多个子任务
        elif stype == "pipeline":
            info_logger(f"\n>> 进入管线: {name}")
            task_results = []
            last_res = {}
            for sub_step in step["tasks"]:
                last_res = await self.execute(sub_step, loop_index)
                task_results.append(last_res)
                await asyncio.sleep(0.2)
            # 合并最后一个任务的结果到返回字典中，便于 break_condition 读取
            return {
                "status": "success", 
                "data": task_results, 
                **last_res
            }

        # 异步并行：同时执行多个子任务
        elif stype == "parallel":
            info_logger(f"\n>> 启动并行: {name}")
            tasks = [self.execute(s, loop_index) for s in step["tasks"]]
            combined_results = await asyncio.gather(*tasks)
            return {"status": "success", "type": "parallel", "data": combined_results}

        # 异步循环：重复执行任务体指定次数
        elif stype == "loop":
            info_logger(f"\n>> 启动循环: {name}")
            times = step["times"]
            loop_history = []
            for i in range(1, times + 1):
                res = await self.execute(step["body"], loop_index=i)
                loop_history.append(res)
                # 检查中断条件，如果满足则提前退出循环
                if step.get("break_condition"):
                    if eval(step["break_condition"], {"result": res}):
                        info_logger(f"🛑 循环中断: 满足条件")
                        break
            return {"status": "finished", "type": "loop", "data": loop_history}

    async def run(self):
        """执行整个工作流"""
        start_time = time.perf_counter()
        info_logger(f"🚀 异步引擎启动: {self.workflow.get('name')}")
        
        for step in self.workflow["tasks"]:
            await self.execute(step)
            
        info_logger(f"\n✅ 流程全部完成，总耗时: {time.perf_counter() - start_time:.2f}s")

# 主程序入口
config = AppServerConfig()
where_result = subprocess.run(["where", "codex.cmd"], text=True, capture_output=True, check=True,)
config.codex_bin = where_result.stdout.strip()

async def main():
    # 1. 基础环境初始化
    codex_instance = Codex(config=config) 
    work_path = Path.cwd()

    # 2. 获取实例化的任务注册表（关键步骤）
    # 将 TASK_REGISTRY 里的类变成实例的 .run 方法
    active_registry = get_task_registry(codex_instance, work_path)

    # 3. 加载 JSON 配置化的工作流（由引擎驱动）
    workflow_config = json.loads((Path.cwd() / "workflow.json").read_text(encoding="utf-8"))

    # 4. 实例化引擎并运行
    # 传入的是 active_registry（已实例化的方法映射）
    engine = AsyncWorkflowEngine(workflow_config, active_registry, codex_instance, work_path)
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())