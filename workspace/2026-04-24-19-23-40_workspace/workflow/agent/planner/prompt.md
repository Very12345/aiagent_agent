read question.json and solve the problem
your output MUST be only JSON like:
```json
{
    "problem": string,
    "plan": [
        {
            "step": string,
            "detailed_task": string,
            "tools_can_use": array of strings
        },
        more steps if needed
    ]
}
```
don't output any other content except the JSON.
don't use ```json``` to wrap the JSON.