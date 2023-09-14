rule ContainAPIToken
{
    meta:
        category = "Sensitive Information"
        description = "Detects patterns for common API tokens and other secrets"
        author = "Adam M. Swanda"
        references = "https://github.com/l4yton/RegHex"

    strings:
        $artifactory0 = /AKC[a-zA-Z0-9]{10,}/

        $artifactory1 = /AP[\dABCDEF][a-zA-Z0-9]{8,}/

        $aws = /(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}/

        $azure = /AZURE[A-Za-z0-9]{12}/

        $facebook = /EAACEdEose0cBA[0-9A-Za-z]+/

        $google = /AIza[0-9A-Za-z\\-_]{35}/

        $gcp = /(google|gcp|youtube|drive|yt)(.{0,20})?['\"][AIza[0-9a-z\\-_]{35}]['\"]/

        $heroku = /[h|H][e|E][r|R][o|O][k|K][u|U].{0,30}[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}/

        $linkedin = /linkedin(.{0,20})?['\"][0-9a-z]{16}/

        $mailchimp = /[0-9a-f]{32}-us[0-9]{1,2}/

        $mailgun = /key-[0-9a-zA-Z]{32}/

        $slack = /xox[baprs]-([0-9a-zA-Z]{10,48})?/

        $square0 = /sqOatp-[0-9A-Za-z\\-_]{22}/

        $square1 = /sq0csp-[ 0-9A-Za-z\\-_]{43}/

        $twilio = /SK[0-9a-fA-F]{32}/

    condition:
        any of them
}
