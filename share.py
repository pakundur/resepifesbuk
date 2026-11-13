"""Share bar for recipe pages.

Scope: link-sharing destinations ONLY, per the brief. No Like/Follow embeds,
no third-party tracking scripts, no iframes. Every button is a plain anchor
with a query-string share URL, so there is zero JS and zero external request
until the reader actually clicks.

Included:
  - WhatsApp (dominant in Malaysia)
  - Telegram
  - Facebook
  - X / Twitter
  - Pinterest  (recipe discovery - high intent for food)
  - Email      (dark social)
  - Copy link  (the only JS, uses navigator.clipboard, degrades silently)

Deliberately excluded: Instagram/TikTok (no web share endpoint for links),
and all JS-SDK buttons that would inject trackers.

Usage:  share_html(title, url)  ->  <div class="share-bar">...</div>
"""
from urllib.parse import quote


def share_html(title: str, url: str, compact: bool = False) -> str:
    t = quote(title)
    u = quote(url, safe="")
    tu = quote(f"{title} {url}")
    img = ""

    targets = [
        ("whatsapp", "WhatsApp",
         f"https://wa.me/?text={tu}",
         '<path d="M17.5 14.4c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.5-2.3-1.4-.9-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.2.2-.3.3-.5.1-.2 0-.3 0-.5 0-.1-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.2 5.1 4.4.7.3 1.3.5 1.7.6.7.2 1.4.2 1.9.1.6-.1 1.7-.7 2-1.4.2-.7.2-1.3.2-1.4-.1-.1-.3-.2-.5-.3z"/><path d="M12 2C6.5 2 2 6.5 2 12c0 1.8.5 3.4 1.3 4.9L2 22l5.3-1.4c1.4.8 3 1.2 4.7 1.2 5.5 0 10-4.5 10-10S17.5 2 12 2zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3.1.8.8-3-.2-.3c-.8-1.3-1.3-2.9-1.3-4.4C3.6 7.4 7.4 3.6 12 3.6S20.4 7.4 20.4 12 16.6 20.2 12 20.2z"/>'),
        ("telegram", "Telegram",
         f"https://t.me/share/url?url={u}&text={t}",
         '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm4.6 6.9l-1.6 7.5c-.1.5-.4.7-.9.4l-2.4-1.8-1.2 1.1c-.1.1-.3.3-.5.3l.2-2.5 4.5-4.1c.2-.2 0-.3-.3-.1l-5.6 3.5-2.4-.7c-.5-.2-.5-.5.1-.8l9.4-3.6c.4-.2.8 0 .7.8z"/>'),
        ("facebook", "Facebook",
         f"https://www.facebook.com/sharer/sharer.php?u={u}",
         '<path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/>'),
        ("x", "X",
         f"https://twitter.com/intent/tweet?url={u}&text={t}",
         '<path d="M18.9 2H22l-7.3 8.3L23.2 22h-6.7l-5.2-6.8L5.3 22H2.2l7.8-8.9L1.2 2h6.9l4.7 6.2L18.9 2zm-1.2 18h1.9L7.4 3.9H5.4L17.7 20z"/>'),
        ("pinterest", "Pinterest",
         f"https://pinterest.com/pin/create/button/?url={u}&description={t}",
         '<path d="M12 2C6.5 2 2 6.5 2 12c0 4.2 2.6 7.8 6.3 9.3-.1-.8-.2-2 0-2.9l1.2-4.9s-.3-.6-.3-1.5c0-1.4.8-2.4 1.8-2.4.9 0 1.3.6 1.3 1.4 0 .9-.6 2.2-.8 3.4-.2 1 .5 1.8 1.5 1.8 1.8 0 3.2-1.9 3.2-4.7 0-2.4-1.7-4.1-4.2-4.1-2.9 0-4.6 2.1-4.6 4.4 0 .9.3 1.8.8 2.3.1.1.1.2.1.3l-.3 1.1c0 .2-.2.2-.3.1-1.2-.6-2-2.4-2-3.9 0-3.2 2.3-6.1 6.7-6.1 3.5 0 6.2 2.5 6.2 5.8 0 3.5-2.2 6.3-5.2 6.3-1 0-2-.5-2.3-1.2l-.6 2.4c-.2.9-.8 2-1.2 2.6.9.3 1.9.4 2.9.4 5.5 0 10-4.5 10-10S17.5 2 12 2z"/>'),
        ("email", "Email",
         f"mailto:?subject={t}&body={tu}",
         '<path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4.2-8 5-8-5V6l8 5 8-5v2.2z"/>'),
    ]

    btns = []
    for key, label, href, path in targets:
        btns.append(
            f'<a class="share-btn share-{key}" href="{href}" target="_blank" '
            f'rel="noopener nofollow" aria-label="Kongsi ke {label}" title="Kongsi ke {label}">'
            f'<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">{path}</svg>'
            f'<span>{label}</span></a>'
        )

    btns.append(
        '<button class="share-btn share-copy" type="button" '
        'onclick="(function(b){var t=location.href;'
        "var f=function(){b.querySelector('span').textContent='Disalin';"
        "setTimeout(function(){b.querySelector('span').textContent='Salin pautan';},2000);};"
        "if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(f);}"
        "else{var i=document.createElement('input');i.value=t;document.body.appendChild(i);"
        "i.select();document.execCommand('copy');i.remove();f();}})(this)\" "
        'aria-label="Salin pautan">'
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
        '<path d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H8V7h11v14z"/>'
        '</svg><span>Salin pautan</span></button>'
    )

    cls = "share-bar compact" if compact else "share-bar"
    return (
        f'<div class="{cls}" role="group" aria-label="Kongsi resepi ini">'
        f'<span class="share-label">Kongsi</span>'
        + "".join(btns)
        + "</div>"
    )
