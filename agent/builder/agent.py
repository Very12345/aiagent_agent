import json
from main import err_logger, info_logger
from codex_app_server import Codex
import asyncio


class Main:
    """读取 plan.json 并构建解决方案"""
    
    def __init__(self, codex: Codex, workdir: Path):
        self.codex = codex
        self.workdir = workdir
    
    def _load_prompt_file(self, filename: str) -> str | None:
        """如果存在则从 markdown 文件加载提示内容"""
        prompt_path = self.workdir / "agent" / "builder" / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return None
    
    async def run(self, plan: dict = None) -> dict:
        """读取 plan.json（或使用传入的计划），执行步骤，返回解决方案"""
        plan_path = self.workdir / "workspace" / "plan" / "plan.json"
        if not plan_path.exists() and not plan:
            err_logger(f"计划文件未找到: {plan_path}")
            exit(1)
        
        if not plan and plan_path.exists():
            with open(plan_path, "r") as f:
                plan = json.load(f)
        
        # 如果存在 builder.md 则自动加载作为自定义提示
        builder_prompt = self._load_prompt_file("prompt.md")
        builder_base_prompt = self._load_prompt_file("prompt_base.md")
        
        if builder_prompt:
            developer_instructions = builder_prompt
            base_instructions = "输出包含结果的有效 JSON。"
        else:
            err_logger(f"解决方案提示文件未找到: {self.workdir / 'agent' / 'builder' / 'builder.md'}")
            exit(1)
        
        if builder_base_prompt:
            base_instructions = builder_base_prompt
        else:
            err_logger(f"解决方案基础提示文件未找到: {self.workdir / 'agent' / 'builder' / 'builder_base.md'}")
            exit(1)
        
        thread = self.codex.thread_start(
            model="qwen3.5-plus",
            developer_instructions=developer_instructions,
            base_instructions=base_instructions
        )
        
        prompt = f"{json.dumps(plan, indent=2)}"
        result = await asyncio.to_thread(thread.run, prompt)
        
        try:
            solution = json.loads(result.final_response)
        except json.JSONDecodeError:
            solution = {"raw_response": result.final_response}
        
        # 保存解决方案供 evaluator 使用
        solu_path = self.workdir / "workspace" / "solution" / "solu.json"
        with open(solu_path, "w") as f:
            json.dump(solution, f, indent=2)
        
        info_logger(f"solu: {solution}\nsolu_path: {solu_path}\n")
        return solution