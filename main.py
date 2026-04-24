import asyncio
import json
import shutil
import time
from pathlib import Path
import subprocess
import sys
import importlib
import importlib.util
import argparse
import zipfile
def get_worktime():
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())



def check_and_install_codex_app_server():
    """检查 codex_app_server 是否存在，如果不存在则自动安装"""
    try:
        from codex_app_server import Codex, AsyncCodex, AppServerConfig
        return Codex, AppServerConfig, AsyncCodex
    except ImportError as e:
        print(f"❌ 导入 codex_app_server 失败: {e}")
        print("❌ codex_app_server 未安装，正在自动安装...")
        
        # 切换到 env 目录
        env_dir = Path.cwd() / "env"
        if not env_dir.exists():
            print(f"❌ env 目录不存在: {env_dir}")
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
        
        

Codex, AppServerConfig, AsyncCodex = check_and_install_codex_app_server()


class AsyncWorkflowEngine:
    """异步工作流引擎：解析并执行 JSON 配置的工作流"""
    def __init__(self, args: argparse.Namespace, codex, workdir: Path):
        self.task_registry = {}
        self.codex = codex
        self.workdir = workdir
        self.thisworktime = get_worktime()
        if(args.workspace):
            self.workspace = Path(args.workspace)
            self.init_workspace(self.workspace)
        else:
            self.workspace = self.create_workspace(workdir)
        if(args.question_file):
            question = args.question_file
            with open(question, "r") as f:
                question = json.load(f)
        elif(args.question_content):
            question = args.question_content
            self.info_logger(f"使用问题内容: {question}")
        else:
            question_path=self.workdir /"template" / "question.json"
            with open(question_path, "r") as f:
                question = json.load(f)
            self.info_logger(f"使用模板问题文件: {question_path}")
        with open(self.workspace / "question" / "question.json", "w") as f:
            json.dump(question, f, ensure_ascii=False, indent=4)
        

        if(args.workflow_file):
            zip_file = args.workflow_file
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(self.workspace / "workflow")
            self.info_logger(f"使用工作流目录: {self.workspace / 'workflow'}")
        elif(args.workflow_dir):
            self.copy_dir(Path(args.workflow_dir), self.workspace / "workflow")
            self.info_logger(f"使用工作流目录: {self.workspace / 'workflow'}")
        else:
            self.copy_dir(Path(self.workdir /"template" / "templateworkflow"), self.workspace / "workflow")
            self.info_logger(f"使用模板工作流目录: {self.workspace / 'workflow'}")
        # 读取工作流配置
        if not (self.workspace / "workflow" / "workflow.json").exists():
            self.err_logger("工作流目录中没有 workflow.json 文件")
            sys.exit(1)
        self.workflow = json.loads((self.workspace / "workflow" / "workflow.json").read_text(encoding="utf-8"))
        self.total_tokens = 0
    def static_usage(self, usage):
        self.info_logger(f"使用 token: {usage.total.total_tokens}")
        self.total_tokens += usage.total.total_tokens

    def copy_dir(self, src: Path, dst: Path):
        """递归复制目录"""
        if not dst.exists():
            dst.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            return
        for item in src.iterdir():
            if item.is_dir():
                self.copy_dir(item, dst / item.name)
            else:
                shutil.copy(item, dst / item.name)
    def err_logger(self, msg: str):
        print(f"\033[91m{msg}\033[0m")
    def info_logger(self, msg: str, data: any = None):
        log_file: Path = self.workspace / "log" / f"{self.thisworktime}_info.log"
        
        msg_str = str(msg) if not isinstance(msg, str) else msg
        output_lines = [f"[{get_worktime()}] {msg_str}"]
        
        if data is not None:
            output_lines.append("")
            formatted_data = self._format_any(data)
            output_lines.append(formatted_data)
        
        full_log = "\n".join(output_lines)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{full_log}\n")
            f.write("=" * 80 + "\n")
        
        console_msg = msg_str if len(msg_str) <= 100 else msg_str[:100] + "..."
        print(f"\033[92m{console_msg}\033[0m")


    def _format_any(self, data, indent=2) -> str:
        """智能格式化任意数据为格式化的字符串，自动展开嵌套的 JSON 字符串"""
        
        def _expand_json_strings(obj):
            """递归展开对象中的 JSON 字符串"""
            if obj is None:
                return None
            elif isinstance(obj, str):
                try:
                    parsed = json.loads(obj)
                    return _expand_json_strings(parsed)
                except (json.JSONDecodeError, TypeError):
                    return obj
            elif isinstance(obj, dict):
                return {k: _expand_json_strings(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [_expand_json_strings(item) for item in obj]
            elif isinstance(obj, set):
                return [_expand_json_strings(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return _expand_json_strings({k: _expand_json_strings(v) for k, v in vars(obj).items()})
            elif hasattr(obj, '__slots__'):
                return {k: _expand_json_strings(getattr(obj, k)) for k in obj.__slots__}
            else:
                return obj
        
        def _convert_to_serializable(obj):
            """递归转换对象为可序列化的格式"""
            if obj is None:
                return None
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            elif isinstance(obj, (dict, list, tuple)):
                return obj
            elif isinstance(obj, set):
                return list(obj)
            elif hasattr(obj, '__dict__'):
                return {k: _convert_to_serializable(v) for k, v in vars(obj).items()}
            elif hasattr(obj, '__slots__'):
                return {k: _convert_to_serializable(getattr(obj, k)) for k in obj.__slots__}
            elif isinstance(obj, (list, tuple)):
                return [_convert_to_serializable(item) for item in obj]
            else:
                return str(obj)
        
        try:
            expanded_data = _expand_json_strings(data)
            serializable_data = _convert_to_serializable(expanded_data)
            return json.dumps(serializable_data, indent=indent, ensure_ascii=False, default=str)
            
        except Exception as e:
            return f"<格式化失败: {type(data).__name__}> {str(data)}"
    def init_workspace(self, thisworkspace: Path):
        """初始化工作空间"""
        print(f"✅ 初始化工作空间: {thisworkspace}")
        # str' object has no attribute 'exists'
        if not thisworkspace.exists():
            thisworkspace.mkdir(parents=True, exist_ok=True)
        if not (thisworkspace / "question").exists():
            (thisworkspace / "question").mkdir(parents=True, exist_ok=True)
        if not (thisworkspace / "log").exists():
            (thisworkspace / "log").mkdir(parents=True, exist_ok=True)
        
    def  create_workspace(self, workdir: Path):
        """创建工作空间"""
        thisworkspace=workdir / "workspace" / f"{self.thisworktime}_workspace"
        print(f"✅ 创建工作空间: {thisworkspace}")
        self.init_workspace(Path(thisworkspace))
        return thisworkspace
    

    def _replace_params(self, params, loop_index):
        """替换参数中的循环索引占位符"""
        if loop_index is None:
            return params
        s = json.dumps(params).replace("{{loop_index}}", str(loop_index))
        return json.loads(s)

    async def load_agent(self, agents, err_logger, info_logger):
        """加载智能体"""
        for agent in agents:
            agent_path = self.workspace / "workflow" / "agent" / agent / "agent.py"
            if not agent_path.exists():
                err_logger(f"智能体文件未找到: {agent_path}")
                sys.exit(1)
            
            spec = importlib.util.spec_from_file_location(f"{agent}_agent", agent_path)
            if spec is None or spec.loader is None:
                err_logger(f"无法加载智能体模块: {agent_path}")
                sys.exit(1)
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"{agent}_agent"] = module
            spec.loader.exec_module(module)
            
            self.task_registry[agent] = module.Main(self.codex, self.workspace / "workflow" / "agent" / agent, self.workspace / "question", err_logger, info_logger)
            info_logger(f"  [加载智能体] {agent}")

    async def execute(self, step, loop_index=None):
        """执行单个工作流步骤"""
        stype = step.get("type")
        name = step.get("name", "Unnamed")

        # 原子任务：异步执行单个函数
        if stype == "load":
            return await self.load_agent(step["agents"], self.err_logger, self.info_logger)
        
        elif stype == "task":
            agent_instance = self.task_registry[step["func"]]
            params = self._replace_params(step.get("params", {}), loop_index)
            self.info_logger(f"  [执行任务] {name}")
            if params:
                result = await agent_instance.run(**params)
            else:
                result = await agent_instance.run()
            self.static_usage(result.usage)
            return json.loads(result.final_response)

        # 顺序管线：按顺序执行多个子任务
        elif stype == "pipeline":
            self.info_logger(f"\n>> 进入管线: {name}")
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
            self.info_logger(f"\n>> 启动并行: {name}")
            tasks = [self.execute(s, loop_index) for s in step["tasks"]]
            combined_results = await asyncio.gather(*tasks)
            return {"status": "success", "type": "parallel", "data": combined_results}

        # 异步循环：重复执行任务体指定次数
        elif stype == "loop":
            self.info_logger(f"\n>> 启动循环: {name}")
            times = step["times"]
            loop_history = []
            for i in range(1, times + 1):
                res = await self.execute(step["body"], loop_index=i)
                loop_history.append(res)
                # 检查中断条件，如果满足则提前退出循环
                if step.get("break_condition"):
                    if eval(step["break_condition"], {"result": res}):
                        self.info_logger(f"🛑 循环中断: 满足条件")
                        break
            return {"status": "finished", "type": "loop", "data": loop_history}

    async def run(self):
        """执行整个工作流"""
        start_time = time.perf_counter()
        self.info_logger(f"🚀 异步引擎启动: {self.workflow.get('name')}")
        
        for step in self.workflow["tasks"]:
            await self.execute(step)
        
        self.info_logger(f"\n✅ 流程全部完成，总耗时: {time.perf_counter() - start_time:.2f}s")
    def package_workflow(self):
        """打包工作流"""
        #打包workspace目录下的所有文件到zip文件
        zip_file = self.workspace.with_suffix(".zip")
        with zipfile.ZipFile(zip_file, "w") as zipf:
            arcname = self.workspace.name.split("/")[-1]
            zipf.write(self.workspace, arcname=arcname)
        # shutil.rmtree(self.workspace)
    #在类注销的时候打印总token数
    async def close(self):
        """显式关闭方法"""
        await self.codex.close()
        self.info_logger(f"总token数: {self.total_tokens}")
        self.package_workflow()
        
    
    def __del__(self):
        if not hasattr(self, '_closed') or not self._closed:
            import warnings
            warnings.warn(f"{self.__class__.__name__} 没有正确关闭，请使用 async with 或显式调用 close()", ResourceWarning)
       # 主程序入口
config = AppServerConfig()
where_result = subprocess.run(["where", "codex.cmd"], text=True, capture_output=True, check=True,)
config.codex_bin = where_result.stdout.strip()

async def main(args: argparse.Namespace):
    # 基础环境初始化
    
    codex_instance = AsyncCodex(config=config)
    work_path = Path.cwd()

    engine = AsyncWorkflowEngine(args, codex_instance, work_path)
    await engine.run()
    await engine.close()

if __name__ == "__main__":
    #处理例如python main.py -w test -f question.json -s "{'ques': {'ques': '你好'}}"
    parser = argparse.ArgumentParser()
    parser.add_argument('-workspace', help='工作空间名称')
    parser.add_argument('-question_file','-f', help='问题文件路径')
    parser.add_argument('-question_content', '-c', help='问题文字描述')
    parser.add_argument('-workflow_file', '-wz', help='工作流文件(zip格式)')
    parser.add_argument('-workflow_dir', '-w', help='工作流目录')

    args = parser.parse_args()

    asyncio.run(main(args))