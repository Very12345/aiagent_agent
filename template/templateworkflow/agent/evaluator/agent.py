import json
from pathlib import Path
from codex_app_server import AsyncCodex
import shutil



class Main:
    """读取 solu.json 并评估解决方案"""
    
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
        """读取 solution.json（或使用传入的解决方案），执行评估，返回评估结果"""
        
        self.copy_from_questionspace("solution.json")
        self.copy_from_questionspace("question.json")
        evaluator_prompt = self._load_prompt_file("instruction.md")
        evaluator_base_prompt = self._load_prompt_file("instruction_base.md") 
        prompt = self._load_prompt_file("prompt.md")

        
        thread = await self.codex.thread_start(
            model="qwen3.5-plus",
            developer_instructions=evaluator_prompt,    
            base_instructions=evaluator_base_prompt,
            cwd=str(self.workspace / "workdir")
        )
        
        result = await thread.run(prompt)
        
        try:
            evaluation = json.loads(result.final_response)
        except json.JSONDecodeError:
            evaluation = {"raw_response": result.final_response}
        
        # 保存评估结果
        eval_path = self.questionspace / "evaluation.json"
        with open(eval_path, "w") as f:
            json.dump(evaluation, f, indent=2)
        
        self.info_logger(f"评估完成 - 评估结果已保存到: {eval_path}", data=result)
        return result