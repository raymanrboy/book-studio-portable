"""The Workshop (the Listings mode): books in development, made with the book pipeline's agents.

The owner (2026-09-24): "a place where I create books before sending them to the library with orders". Since
2026-09-26 it is the book console moved in (the prototype «Пульт книги»): a book is a folder of the pipeline's
`books/`, where the agents in Antigravity write its text and prompts; the Workshop shows its path, puts every prompt
into the clipboard, catches the picture the owner downloads from Gemini into its row — cut, flipped, the cover laid on
the printer's template — and passes the finished book to the library with its Etsy listing.

    books.py      a book = a folder: the list, the path strip, marks, versions, delete, passing to the library
    rows.py       the agents' files read into rows, the cover's template, hero variants, the book check (GO)
    pictures.py   a picture into its row: cut, flipped, two pages; the cover's margins; ⇄; nothing deleted
    generate.py   the generation mode: the clipboard, the Downloads watcher, F8
    check.py      the book check's rules (the old pipeline's validator; the agents run it too)
    routes.py     the routes

Plan and agreements: wiki/plans/book-console.md; how it works: wiki/features/workshop.md.
"""
from . import routes  # noqa: F401  (registers the routes)
