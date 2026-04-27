read the plan.json&question_content.json&question_tag.json file and execute the steps
the plan_content.json file is the plan to execute the steps
there are multiple plans to execute the steps, and you need to execute all of them
your output MUST be only JSON like:

```json
{
    "problem": string,

    "plans": [
        {
            "num":i,
            "plan":{
                "steps":[
                {
                    "step": string,
                    "detailed_solution": string
                },
                more steps if needed
                ]
            }
        },
        more if theres more plans to execute
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
don't use ```json``` to wrap the JSON.
