import json
from pathlib import Path
from codex_app_server import AsyncCodex



class Main:
    """读取 solu.json 并评估解决方案"""
    
    def __init__(self, codex: AsyncCodex, workspace: Path, err_logger, info_logger):
        self.codex = codex
        self.workspace = workspace
        self.err_logger = err_logger
        self.info_logger = info_logger
    
    def _load_prompt_file(self, filename: str) -> str | None:
        """如果存在则从 markdown 文件加载提示内容"""
        prompt_path = self.workspace / "workflow" / "agent" / "evaluator" / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return None
    
    async def run(self, solution: dict = None) -> dict:
        """读取 solution.json（或使用传入的解决方案），执行评估，返回评估结果"""
        solu_path = self.workspace / "solution" / "solution.json"
        if not solu_path.exists() and not solution:
            self.err_logger(f"解决方案文件未找到: {solu_path}")
            exit(1)
        
        if not solution and solu_path.exists():
            with open(solu_path, "r") as f:
                solution = json.load(f)
        
        ques_path = self.workspace / "question" / "question.json"
        with open(ques_path, "r") as f:
            question_data = json.load(f)
        
        # 如果存在 evaluator.md 则自动加载作为自定义提示
        evaluator_prompt = self._load_prompt_file("prompt.md")
        evaluator_base_prompt = self._load_prompt_file("prompt_base.md") 
        
        if evaluator_prompt:
            developer_instructions = evaluator_prompt
        else:
            self.err_logger(f"评估提示文件未找到: {self.workspace / 'workflow' / 'agent' / 'evaluator' / 'evaluator.md'}")
            exit(1)
        if evaluator_base_prompt:
            base_instructions = evaluator_base_prompt
        else:
            self.err_logger(f"评估基础提示文件未找到: {self.workspace / 'workflow' / 'agent' / 'evaluator' / 'evaluator_base.md'}")
            exit(1)
        
        thread = await self.codex.thread_start(
            model="qwen3.5-plus",
            developer_instructions=developer_instructions,
            base_instructions=base_instructions
        )
        
        prompt = f"问题: {json.dumps(question_data, indent=2)}\n\n解决方案: {json.dumps(solution, indent=2)}"
        result = await thread.run(prompt)
        
        try:
            evaluation = json.loads(result.final_response)
        except json.JSONDecodeError:
            evaluation = {"raw_response": result.final_response}
        
        # 保存评估结果
        eval_path = self.workspace / "evaluation" / "evaluation.json"
        with open(eval_path, "w") as f:
            json.dump(evaluation, f, indent=2)
        
        self.info_logger(f"评估完成 - 评估结果已保存到: {eval_path}", data=result)
        return evaluation