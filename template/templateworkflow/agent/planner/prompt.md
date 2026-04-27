read question\_content.json\&question\_tag.json and solve the problem
you need to plan the steps to solve the problem,and prepare multiple plans to solve the problem as much as possible
your output MUST be only JSON like:

```json
{
    "problem": string,
    "plans": [
        "num":i,
        "plan": [
            {
                "step": string,
                "detailed_task": string,
                "tools_can_use": array of strings
            },
            more steps if needed
        ]
    ]
}
```

don't output any other content except the JSON.
don't use ```json``` to wrap the JSON.
