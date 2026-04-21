import json
from main import err_logger, info_logger
import asyncio
from codex_app_server import Codex

class Main:
    """读取 ques.json 并生成执行计划"""
    
    def __init__(self, codex: Codex, workdir: Path):
        self.codex = codex
        self.workdir = workdir
    
    def _load_prompt_file(self, filename: str) -> str | None:
        """如果存在则从 markdown 文件加载提示内容"""
        prompt_path = self.workdir / "agent" / "planner" / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return None
    
    async def run(self) -> dict:
        """读取 ques.json，规划解决方案，返回计划字典"""
        ques_path = self.workdir / "question" / "ques.json"
        if not ques_path.exists():
            err_logger(f"问题文件未找到: {ques_path}")
            exit(1)
        
        with open(ques_path, "r") as f:
            question_data = json.load(f)
        
        # 如果存在 planner.md 则自动加载作为自定义提示
        planner_prompt = self._load_prompt_file("prompt.md")
        planner_base_prompt = self._load_prompt_file("prompt_base.md")
        if planner_prompt:
            # 使用 planner.md 内容作为开发者指令
            developer_instructions = planner_prompt
            base_instructions = "输出包含步骤、资源和成功标准的有效 JSON。"
        else:
            err_logger(f"规划提示文件未找到: {self.workdir / 'agent' / 'planner' / 'planner.md'}")
            exit(1)
        
        if planner_base_prompt:
            base_instructions = planner_base_prompt
        else:
            err_logger(f"规划基础提示文件未找到: {self.workdir / 'agent' / 'planner' / 'planner_base.md'}")
            exit(1)
        
        thread = self.codex.thread_start(
            model="qwen3.5-plus",
            developer_instructions=developer_instructions,
            base_instructions=base_instructions
        )
        
        prompt = f"{json.dumps(question_data, indent=2)}"
        result = await asyncio.to_thread(thread.run, prompt)
        
        try:
            plan = json.loads(result.final_response)
        except json.JSONDecodeError:
            plan = {"raw_response": result.final_response, "steps": []}
        
        # 保存计划供 builder 使用
        plan_path = self.workdir / "workspace" / "plan" / "plan.json"
        with open(plan_path, "w") as f:
            json.dump(plan, f, indent=2)
        
        info_logger(f"plan: {plan}\nplan_path: {plan_path}\n")
        return plan