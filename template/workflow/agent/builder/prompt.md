read the plan.json&question_content.json&question_tag.json file and execute the steps
your output MUST be only JSON like:

```json
{
    "problem": string,
    "plan": [
        {
            "step": string,
            "detailed_solution": string
        },
        more steps if needed
    ],
    "final_answer": string,
    "answer_format": {
        "includes_constant_C": boolean,
        "is_numeric": boolean,
        "is_infinite": boolean,
        "is_expression": boolean
    }
}
```

don't output any other content except the JSON.
don't use `json` to wrap the JSON.
