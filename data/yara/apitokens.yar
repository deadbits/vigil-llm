rule ContainsAPIToken
{
    meta:
        category = "Sensitive Information"
        description = "Detects patterns for common API tokens and other secrets"
        author = "Adam M. Swanda"
        references = "https://github.com/l4yton/RegHex"

    strings:
        $artifactory0 = /AKC[a-zA-Z0-9]{10,}/

        $artifactory1 = /AP[\dABCDEF][a-zA-Z0-9]{8,}/

        $aws0 = /(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}/
        $aws1 = /amzn\\.mws\\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/
        $aws2 = /da2-[a-z0-9]{26}/

        $azure = /AZURE[A-Za-z0-9]{12}/

        $facebook = /EAACEdEose0cBA[0-9A-Za-z]+/

        $google = /AIza[0-9A-Za-z\\-_]{35}/
        $google_oauth = /ya29\\.[0-9A-Za-z\\-_]+/
        $gcp_oauth = /[0-9]+-[0-9A-Za-z_]{32}\\.apps\\.googleusercontent\\.com/

        $linkedin = /linkedin(.{0,20})?['\"][0-9a-z]{16}/

        $mailchimp = /[0-9a-f]{32}-us[0-9]{1,2}/

        $mailgun = /key-[0-9a-zA-Z]{32}/

        $slack = /(xox[pborsa]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32})/
        $slack_webhook = /https:\/\/hooks\\.slack\\.com\/services\/T[a-zA-Z0-9_]{8}\/B[a-zA-Z0-9_]{8}\/[a-zA-Z0-9_]{24}/

        $stripe0 = /sk_live_[0-9a-zA-Z]{24}/
        $stripe1 = /rk_live_[0-9a-zA-Z]{24}/        

        $square0 = /sqOatp-[0-9A-Za-z\\-_]{22}/

        $square1 = /sq0csp-[ 0-9A-Za-z\\-_]{43}/

        $telegram = /[0-9]+:AA[0-9A-Za-z\\-_]{33}/
        $twilio = /SK[0-9a-fA-F]{32}/

    condition:
        any of them
}

