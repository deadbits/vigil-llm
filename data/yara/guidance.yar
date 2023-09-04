rule ContainsGuidance_vigil: Guidance
{
    meta:
        category = "Informational"
        description = "Detects prompts that include Guidance language terms (e.g., {{#system~}})"
        reference = "https://github.com/guidance-ai/guidance"
        author = "Adam M. Swanda"

    strings:
        $system0 = "{{#system~}}"
        $system1 = "{{/system~}}"

        $user0 = "{{#user~}}"
        $user1 = "{{/user~}}"

        $assistant0 = "{{#assistant~}}"
        $assistant1 = "{{/assistant~}}"
    condition:
        (
            any of ($system*)
            or
            any of ($user*)
            or
            any of ($assistant*)
        )
}
