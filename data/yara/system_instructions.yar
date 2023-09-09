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

        $inst_00 = "<|im_start|>assistant"
        $inst_01 = "<|im_start|>system"

        $guidance0 = "{{#system~}}"
        $guidance1 = "{{/system~}}"

    condition:
        any of them
}
