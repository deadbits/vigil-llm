rule ContainsReAct_txt
{
    meta:
        category = "Injection"
        description = "Detects potential injection of plaintext ReAct patterns"
        reference = "https://labs.withsecure.com/publications/llm-agent-prompt-injection"

    strings:
        // Thought pattern: 'Thought:' followed by the thought process
        $thought = /Thought:\s\w+[^\n]+/

        // Action pattern: 'Action:' followed by the action to take
        $action = /Action:\s*\w+[^\n]*\n/

        // Action Input pattern: 'Action Input:' followed by the input to the action
        $action_input = /Action Input:\s\w+[^\n]+/

        // Observation pattern: 'Observation:' followed by the result of the action
        $observation = /Observation:\s\w+[^\n]+/

    condition:
        $thought
        and
        (
            (
                $action
                and
                $action_input
            )
            or
            (
                $action
            )
            or
            (
                $observation
            )
        )
}
