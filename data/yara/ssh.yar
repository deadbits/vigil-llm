rule ContainsSSHKey
{
    meta:
        category = "Sensitive Data"
        description = "Detects prompts that contain SSH private key headers"

    strings:
        $re = /-----BEGIN ((EC|PGP|DSA|RSA|OPENSSH) )?PRIVATE KEY( BLOCK)?-----/
    condition:
        all of them
}

