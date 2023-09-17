rule ContainsGenericSecretPhrase
{
    meta:
        category = "Sensitive Data"
        description = "Detects prompts that contain generic secret phrases (private key, secret token, etc.)"

    strings:
        $re = /(private|secret|access)\s(key|token|password|pass)/
    condition:
        all of them
}

