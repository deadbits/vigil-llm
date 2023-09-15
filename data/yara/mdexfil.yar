rule MarkdownExfiltration
{
    meta:
        category = "Data Exfiltration"
        description = "Detects Markdown image with query parameters used during data exfiltration"
        author = "Adam M. Swanda"
        references = "https://embracethered.com/blog/posts/2023/bing-chat-data-exfiltration-poc-and-fix/"

    strings:
        $md = /\!\[\w+]\((https?:\/\/[\w\.-]+)\/(\w+)\?q=\)/
    condition:
        all of them
}
