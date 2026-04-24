import json
from codex_app_server import AsyncCodex
from pathlib import Path
import shutil

class Main:
    """读取 plan.json 并构建解决方案"""
    
    def __init__(self, codex: AsyncCodex, workspace: Path, questionspace: Path, err_logger, info_logger):
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
        """读取 plan.json（或使用传入的计划），执行步骤，返回解决方案"""

        self.copy_from_questionspace("plan.json")
        builder_prompt = self._load_prompt_file("instruction.md")
        builder_base_prompt = self._load_prompt_file("instruction_base.md")
        prompt = self._load_prompt_file("prompt.md")
        
        thread = await self.codex.thread_start(
            model="qwen3.5-plus",
            developer_instructions=builder_prompt,
            base_instructions=builder_base_prompt,
            cwd=str(self.workspace / "workdir")
        )
        
        result = await thread.run(prompt)
        
        try:
            solution = json.loads(result.final_response)
        except json.JSONDecodeError:
            solution = {"raw_response": result.final_response}
        
        # 保存解决方案供 evaluator 使用
        solu_path = self.questionspace / "solution.json"

        with open(solu_path, "w") as f:
            json.dump(solution, f, indent=2)
        
        self.info_logger(f"解决方案完成 - 解决方案已保存到: {solu_path}", data=result)
        return result