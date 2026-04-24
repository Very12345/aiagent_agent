read the solution.json file and evaluate the solution
your output MUST be only JSON like:
```json
{
    "problem": string,
    "solution": [
        {
            "step": string,
            "solution": "success"/"failure",
            "advice": string
        },
        more steps if needed
    ],
    "score": number
}
```
if the solution is totally success, then the score is more than 98
otherwise, the score is less than 98
don't output any other content except the JSON.
don't use ```json``` to wrap the JSON.