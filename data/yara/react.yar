rule ContainsReAct: Injection
{
    meta:
        category = "Informational"
        description = "Potential ReAct Thought / Observation injection"
        reference = "https://labs.withsecure.com/publications/llm-agent-prompt-injection"

    strings:
        // Thought pattern: 'Thought:' followed by a JSON object containing action and action_input
        $thought00 = /Thought:\s*```(json)?\s*{\s*\"action\"\s*:\s*\"[^\"]+\",\s*\"action_input\"\s*:\s*\"[^\"]*\"\s*}```/

        // Thought pattern: 'Thought:' followed by a string containing the thought
        // "The user is asking for X. I can use tool Y to find the answer"
        $thought01 = /Thought:\s\w+[^\n]+/

        // Observation pattern: 'Observation:' followed by a string containing the output of the action
        $observation = /Observation:\s*[^\n]+/

        // Action pattern: 'Action:' followed by a JSON object containing action and action_input
        $action = /Action:\s*```\s*{\s*\"action\"\s*:\s*\"[^\"]+\",\s*\"action_input\"\s*:\s*\"[^\"]*\"\s*}```/

    condition:
        ($thought00)
        or
        (
            $thought01
            and
            $action
        )
        or
        (
            $thought00
            and
            $observation
        )
}
