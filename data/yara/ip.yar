rule ContainsIPv4
{
    meta:
        category = "Sensitive Information"
        description = "Detect IPv4 addresses within prompts; may be indicative of injection for SSRF, etc."
        author = "Adam M. Swanda"

    strings:
        $ipv4 = /\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}\b/

    condition:
        $ipv4
}
