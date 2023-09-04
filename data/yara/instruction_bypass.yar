rule InstructionBypass_vigil: PromptInjection
{
    meta:
        category = "Instruction Bypass"
        description = "Detects phrases used to ignore, disregard, or bypass instructions."
        author = "Adam M. Swanda"

    strings:
        $bypass_phrase = /(Ignore|Disregard|Skip|Forget|Neglect|Overlook|Omit|Bypass|Pay no attention to|Do not follow|Do not obey)\s*(prior|previous|preceding|above|foregoing|earlier|initial)?\s*(content|text|instructions|instruction|directives|directive|commands|command|context|conversation|input|inputs|data|message|messages|communication|response|responses|request|requests)\s*(and start over|and start anew|and begin afresh|and start from scratch)?/
    condition:
        $bypass_phrase
}
