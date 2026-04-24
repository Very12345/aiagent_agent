import json
import shutil
from pathlib import Path
from codex_app_server import AsyncCodex

class Main:
    """读取 ques.json 并生成执行计划"""
    
    def __init__(self, codex: AsyncCodex, workspace: Path,  questionspace: Path, err_logger, info_logger):
        self.codex = codex
        self.workspace = workspace
        self.questionspace = questionspace
        self.err_logger = err_logger
        self.info_logger = info_logger
    
    def _load_prompt_file(self, filename: str) -> str | None:
        """如果存在则从 markdown 文件加载提示内容"""
        prompt_path = self.workspace / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        else:
            self.err_logger(f"提示文件未找到: {prompt_path}")
            exit(1)
        return None
    
    def copy_from_questionspace(self,filename: str):
        """从 questionspace 复制 filename 到 workspace"""
        src_path = self.questionspace / filename
        dst_path = self.workspace / "workdir" / filename
        if src_path.exists():
            shutil.copy(src_path, dst_path)
        else:
            self.err_logger(f"文件未找到: {src_path}")
            exit(1)
    
    async def run(self) -> dict:
        """读取 question.json，规划解决方案，返回计划字典"""

        self.copy_from_questionspace("question.json")
        planner_instruction = self._load_prompt_file("instruction.md")
        planner_base_instruction = self._load_prompt_file("instruction_base.md")
        prompt = self._load_prompt_file("prompt.md")
        
        thread = await self.codex.thread_start(
            model="qwen3.5-plus",
            developer_instructions=planner_instruction,
            base_instructions=planner_base_instruction,
            cwd=str(self.workspace / "workdir")
        )
        
        result = await thread.run(prompt)
        
        try:
            plan = json.loads(result.final_response)
        except json.JSONDecodeError:
            plan = {"raw_response": result.final_response, "steps": []}
        
        # 保存计划供 builder 使用
        plan_path = self.questionspace / "plan.json"
        with open(plan_path, "w") as f:
            json.dump(plan, f, indent=2)
        
        self.info_logger(f"规划完成 - 计划已保存到: {plan_path}", data=result)
        return result