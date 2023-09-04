rule SystemInstructions_vigil: PromptInjection
{
    meta:
        category = "Instruction Bypass"
        description = "Detects prompts that contain common System Instruction strings"
        author = "Adam M. Swanda"

    strings:
        $inst = "System Instruction: "
        $inst0 = "[system]"
        $inst_l2_1 = "<s>[INST] <<SYS>>"
        $inst_l2_0 = "<</SYS>>"

        $guidance0 = "{{#system~}}"
        $guidance1 = "{{/system~}}"

    condition:
        ($inst) or ($inst0) 
        or 
        ($inst_l2_1 and $inst_l2_0)
        or
        ($guidance0)
        or
        ($guidance1)
}
