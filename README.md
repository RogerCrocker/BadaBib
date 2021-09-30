# Bada Bib!
Bada Bib! is a simple BibTeX Viewer and Editor written in Python and GTK. It is build around the [python-bibtexparser](https://github.com/sciunto-org/python-bibtexparser) library, which it uses for parsing and writing BibTeX entries.

<a href='https://www.flathub.org/apps/details/com.github.rogercrocker.badabib'><img width='240' alt='Download on Flathub' src='https://flathub.org/assets/badges/flathub-badge-en.png'/></a>

## Features
* View, edit, sort, filter, and search BibTeX databases.
* View and edit BibTeX strings or import strings from external files.
* Customizable editor layouts.
* Shortcuts for common operations, such as protecting upper case letters or converting between unicode and LaTeX.

## Caveats
* Bada Bib! is still under development, and you will run into bugs using it. Please open issues for any bug or any flaws in the code, I am not an experienced GTK programmer. Finally, **please make sure you have backups of your files!**
* Bada Bib! is not supposed to be a replacement for fully fledged reference managers such as [JabRef](https://github.com/JabRef/jabref), [KBibTeX](https://invent.kde.org/office/kbibtex), [Mendeley](http://mendeley.com/), [Zotero](https://www.zotero.org/), and [others](https://en.wikipedia.org/wiki/Comparison_of_reference_management_software).
* Bada Bib! can be annoyingly slow when working with large databases or databases with a large number of strings.
* Bada Bib! automatically recognizes if an expression is the name of a string and treats it as such. That is, if `@string { foo = "bar" }` is defined, `foo` will be treated as a string, unless it is enclosed in braces `{foo}`.
* Bada Bib! does not have a lot of settings and exposes even fewer of them to the user. This will hopefully change in the future. 

## Screenshots
Main Window
![Main window](/data/screenshots/editor.png)

String Manager
![String Manager](/data/screenshots/string_manager.png)

Icon by [svgrepo.com](https://www.svgrepo.com/)


