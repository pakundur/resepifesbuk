"""Floating action stack: share (collapsed fan) + back-to-top.

Bottom-right, fixed. Two buttons stacked:
    [ share ]        <- opens a vertical fan of 7 share destinations
    [  up   ]        <- scrolls to top of document

Design rules
------------
- Share fan is COLLAPSED by default. Only the trigger is visible until tapped.
- No third-party script, no embed: every fan item is a plain anchor with a
  query-string share URL, same destinations as share.py.
- Copy link has no text label; the clipboard handler is the only JS in the fan.
- Back-to-top is an <a href="#top"> so it works with JS disabled; JS only
  intercepts for smooth scrolling.
- Fan state uses aria-expanded on the trigger so screen readers get it.
- Hidden when the document is short? No: back-to-top on a short page is
  harmless, and per-page conditional rendering would bloat the build. Kept
  always-on for consistent behaviour and cacheable HTML.

Usage:  fab_html(title, url)  ->  <div class="fab">...</div>
"""
from urllib.parse import quote


def _destinations(title: str, url: str):
    """Same destination set as the in-flow share bar. Order = fan order (top
    of the fan first, so the most-used Malaysian target sits closest to the
    trigger and needs the least thumb travel)."""
    t = quote(title)
    u = quote(url, safe="")
    tu = quote(f"{title} {url}")
    return [
        ("whatsapp", "WhatsApp", f"https://wa.me/?text={tu}",
         '<path d="M17.5 14.4c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.5-2.3-1.4-.9-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.2.2-.3.3-.5.1-.2 0-.3 0-.5 0-.1-.7-1.6-.9-2.2-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.2 5.1 4.4.7.3 1.3.5 1.7.6.7.2 1.4.2 1.9.1.6-.1 1.7-.7 2-1.4.2-.7.2-1.3.2-1.4-.1-.1-.3-.2-.5-.3z"/><path d="M12 2C6.5 2 2 6.5 2 12c0 1.8.5 3.4 1.3 4.9L2 22l5.3-1.4c1.4.8 3 1.2 4.7 1.2 5.5 0 10-4.5 10-10S17.5 2 12 2zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3.1.8.8-3-.2-.3c-.8-1.3-1.3-2.9-1.3-4.4C3.6 7.4 7.4 3.6 12 3.6S20.4 7.4 20.4 12 16.6 20.2 12 20.2z"/>'),
        ("telegram", "Telegram", f"https://t.me/share/url?url={u}&text={t}",
         '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm4.6 6.9l-1.6 7.5c-.1.5-.4.7-.9.4l-2.4-1.8-1.2 1.1c-.1.1-.3.3-.5.3l.2-2.5 4.5-4.1c.2-.2 0-.3-.3-.1l-5.6 3.5-2.4-.7c-.5-.2-.5-.5.1-.8l9.4-3.6c.4-.2.8 0 .7.8z"/>'),
        ("facebook", "Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}",
         '<path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/>'),
        ("x", "X", f"https://twitter.com/intent/tweet?url={u}&text={t}",
         '<path d="M18.9 2H22l-7.3 8.3L23.2 22h-6.7l-5.2-6.8L5.3 22H2.2l7.8-8.9L1.2 2h6.9l4.7 6.2L18.9 2zm-1.2 18h1.9L7.4 3.9H5.4L17.7 20z"/>'),
        ("pinterest", "Pinterest", f"https://pinterest.com/pin/create/button/?url={u}&description={t}",
         '<path d="M12 2C6.5 2 2 6.5 2 12c0 4.2 2.6 7.8 6.3 9.3-.1-.8-.2-2 0-2.9l1.2-4.9s-.3-.6-.3-1.5c0-1.4.8-2.4 1.8-2.4.9 0 1.3.6 1.3 1.4 0 .9-.6 2.2-.8 3.4-.2 1 .5 1.8 1.5 1.8 1.8 0 3.2-1.9 3.2-4.7 0-2.4-1.7-4.1-4.2-4.1-2.9 0-4.6 2.1-4.6 4.4 0 .9.3 1.8.8 2.3.1.1.1.2.1.3l-.3 1.1c0 .2-.2.2-.3.1-1.2-.6-2-2.4-2-3.9 0-3.2 2.3-6.1 6.7-6.1 3.5 0 6.2 2.5 6.2 5.8 0 3.5-2.2 6.3-5.2 6.3-1 0-2-.5-2.3-1.2l-.6 2.4c-.2.9-.8 2-1.2 2.6.9.3 1.9.4 2.9.4 5.5 0 10-4.5 10-10S17.5 2 12 2z"/>'),
        ("threads", "Threads", f"https://www.threads.net/intent/post?text={tu}",
         '<path d="M12.2 2h-.4C6.5 2 2.7 5.6 2.7 12s3.8 10 9.1 10c4.6 0 8.4-2.4 8.8-6.9.2-2.3-.6-4.1-2.2-5.3-.8-.6-1.8-1-2.8-1.2-.2-1.6-.9-3-2-3.9C12.5 3.8 11.1 3.4 9.7 3.4c-1.9 0-3.5.7-4.5 2l1.7 1.2c.7-.9 1.7-1.4 2.8-1.4 1 0 1.9.3 2.6.9.5.5.9 1.1 1.1 1.9-.5-.1-1.1-.1-1.7-.1-2.2 0-4 .6-5.2 1.8-1 1-1.6 2.3-1.6 3.7 0 2.6 2.1 4.4 5.1 4.4 2.5 0 4.4-1.1 5.4-3 .6-.9 1-2 1.2-3.2.9.6 1.5 1.5 1.6 2.7.2 1.6-.4 3.2-1.6 4.2-1.3 1.1-3.1 1.7-5.2 1.7-4.4 0-7.3-3-7.3-8.2S9.9 3.8 12.2 3.8h.4c2.3 0 4.2.8 5.3 2.3l1.6-1.2C18.1 3.2 15.6 2 12.2 2zm-2.6 13.9c-1.5 0-2.5-.7-2.5-1.9 0-1.3 1.2-2.1 3.2-2.1.5 0 1 .1 1.5.2-.2 2.5-1.1 3.8-2.2 3.8z"/>'),
        ("email", "Email", f"mailto:?subject={t}&body={tu}",
         '<path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4.2-8 5-8-5V6l8 5 8-5v2.2z"/>'),
    ]


_COPY_SVG = ('<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">'
             '<path d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H8V7h11v14z"/>'
             '</svg>')

_SHARE_SVG = ('<svg class="fab__ico-share" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="currentColor">'
              '<path d="M18 16.1c-.8 0-1.5.3-2 .8l-7.1-4.2c0-.2.1-.4.1-.6s0-.4-.1-.6L16 7.2c.5.5 1.2.8 2 .8a2.8 2.8 0 1 0-2.8-2.8c0 .2 0 .4.1.6L8.2 10a2.8 2.8 0 1 0 0 4l7.1 4.2c0 .2-.1.4-.1.6A2.8 2.8 0 1 0 18 16.1z"/>'
              '</svg>')

_CLOSE_SVG = ('<svg class="fab__ico-close" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="currentColor">'
              '<path d="M19 6.4 17.6 5 12 10.6 6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12z"/>'
              '</svg>')

_UP_SVG = ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="currentColor">'
           '<path d="M12 4 4 12h5v8h6v-8h5z"/>'
           '</svg>')


def fab_html(title: str, url: str) -> str:
    items = []
    for key, label, href, path in _destinations(title, url):
        items.append(
            f'<a class="fab__item fab__item--{key}" href="{href}" target="_blank" '
            f'rel="noopener nofollow" aria-label="Kongsi ke {label}" title="Kongsi ke {label}" tabindex="-1">'
            f'<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">{path}</svg>'
            f'<span class="fab__tip">{label}</span></a>'
        )

    # Copy-link item sits LAST in the fan (closest to the trigger it came from).
    items.append(
        '<button class="fab__item fab__item--copy" type="button" '
        'onclick="(function(b){var t=location.href;'
        "var f=function(){b.classList.add('is-copied');"
        "setTimeout(function(){b.classList.remove('is-copied');},2000);};"
        "if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(f);}"
        "else{var i=document.createElement('input');i.value=t;document.body.appendChild(i);"
        "i.select();document.execCommand('copy');i.remove();f();}})(this)\" "
        'aria-label="Salin pautan" title="Salin pautan" tabindex="-1">'
        + _COPY_SVG +
        '<span class="fab__tip">Salin pautan</span></button>'
    )

    return (
        '<div class="fab" id="fab">'
        '<div class="fab__fan" id="fab-fan" aria-hidden="true" role="group" aria-label="Kongsi halaman ini">'
        + "".join(items) +
        '</div>'
        '<button class="fab__btn fab__btn--share" type="button" id="fab-share" '
        'aria-expanded="false" aria-controls="fab-fan" aria-label="Kongsi halaman ini" title="Kongsi halaman ini">'
        + _SHARE_SVG + _CLOSE_SVG +
        '</button>'
        '<a class="fab__btn fab__btn--top" href="#top" id="fab-top" aria-label="Kembali ke atas" title="Kembali ke atas">'
        + _UP_SVG +
        '</a>'
        '</div>'
    )


# Progressive-enhancement script. Runs after the FAB markup (placed at end of
# body), so the nodes exist. If JS is off: share trigger does nothing useful
# but stays inert, and back-to-top still works because it is a real anchor.
FAB_JS = """<script>(function(){
var fab=document.getElementById('fab');
if(!fab)return;
var btn=document.getElementById('fab-share');
var fan=document.getElementById('fab-fan');
var top=document.getElementById('fab-top');
var items=fan.querySelectorAll('.fab__item');
function setOpen(o){
  fab.classList.toggle('is-open',o);
  btn.setAttribute('aria-expanded',o?'true':'false');
  fan.setAttribute('aria-hidden',o?'false':'true');
  for(var i=0;i<items.length;i++){items[i].tabIndex=o?0:-1;}
}
btn.addEventListener('click',function(e){
  e.preventDefault();
  setOpen(!fab.classList.contains('is-open'));
});
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'&&fab.classList.contains('is-open')){
    setOpen(false);btn.focus();
  }
});
document.addEventListener('click',function(e){
  if(fab.classList.contains('is-open')&&!fab.contains(e.target)){setOpen(false);}
});
// Back to top: smooth if supported, honour reduced-motion.
top.addEventListener('click',function(e){
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce)return;
  e.preventDefault();
  window.scrollTo({top:0,behavior:'smooth'});
  history.replaceState(null,'',location.pathname+location.search);
});
})();</script>"""
