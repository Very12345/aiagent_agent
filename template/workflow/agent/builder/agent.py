import json
from codex_app_server import AsyncCodex
from pathlib import Path

class Main:
    """读取 plan.json 并构建解决方案"""
    
    def __init__(self, codex: AsyncCodex, workspace: Path, err_logger, info_logger):
        self.codex = codex
        self.workspace = workspace
        self.err_logger = err_logger
        self.info_logger = info_logger
    
    def _load_prompt_file(self, filename: str) -> str | None:
        """如果存在则从 markdown 文件加载提示内容"""
        prompt_path = self.workspace / "workflow" / "agent" / "builder" / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return None
    
    async def run(self, plan: dict = None) -> dict:
        """读取 plan.json（或使用传入的计划），执行步骤，返回解决方案"""
        plan_path = self.workspace / "plan" / "plan.json"
        if not plan_path.exists() and not plan:
            self.err_logger(f"计划文件未找到: {plan_path}")
            exit(1)
        
        if not plan and plan_path.exists():
            with open(plan_path, "r") as f:
                plan = json.load(f)
        
        # 如果存在 builder.md 则自动加载作为自定义提示
        builder_prompt = self._load_prompt_file("prompt.md")
        builder_base_prompt = self._load_prompt_file("prompt_base.md")
        
        if builder_prompt:
            developer_instructions = builder_prompt
        else:
            self.err_logger(f"解决方案提示文件未找到: {self.workspace / 'workflow' / 'agent' / 'builder' / 'builder.md'}")
            exit(1)
        
        if builder_base_prompt:
            base_instructions = builder_base_prompt
        else:
            self.err_logger(f"解决方案基础提示文件未找到: {self.workspace / 'workflow' / 'agent' / 'builder' / 'builder_base.md'}")
            exit(1)
        
        thread = await self.codex.thread_start(
            model="qwen3.5-plus",
            developer_instructions=developer_instructions,
            base_instructions=base_instructions
        )
        
        prompt = f"{json.dumps(plan, indent=2)}"
        result = await thread.run(prompt)
        
        try:
            solution = json.loads(result.final_response)
        except json.JSONDecodeError:
            solution = {"raw_response": result.final_response}
        
        # 保存解决方案供 evaluator 使用
        solu_path = self.workspace / "solution" / "solution.json"
        with open(solu_path, "w") as f:
            json.dump(solution, f, indent=2)
        
        self.info_logger(f"解决方案完成 - 解决方案已保存到: {solu_path}", data=result)
        return solution