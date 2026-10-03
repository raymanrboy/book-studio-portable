"""Listing slides (the Listings mode): the six square Etsy pictures made from a book's mockups — no Canva.

The owner, 29.09.2026: "create an entirely new tool of your own"; then "integrate it into our program — a separate
module, called only when needed". It is the Mockups' next steps: the pictures Photoshop saves are cut out without
background while it works, «Зробити слайди» makes the six from the template, and the editor (web/js/pages/
slides-editor.js, loaded only when opened) lets the owner — or an agent, through the files — touch them up.
Nothing here runs at launch: no timers, no browser, no psd_tools until a picture is cut or a button pressed.

    cutout.py   a mockup → the book and its real shadow, transparent; «Без фону»; the background cutter
    store.py    the template and a book's slides (scenes, their versions), the set's pictures
    work.py     «Зробити слайди»: the set made, the six baked; a re-bake after the editor
    bake.py     headless Edge draws web/slides/render.html at 2000×2000
    routes.py   the routes

How it works: wiki/features/slides.md.
"""
from . import routes  # noqa: F401  (registers the routes)
