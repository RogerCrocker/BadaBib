# Bada Bib!
Bada Bib! is a simple BibTeX Viewer and Editor written in Python and GTK. It is build around the [python-bibtexparser](https://github.com/sciunto-org/python-bibtexparser) library, which it uses for parsing and writing BibTeX entries.

## Features
* View, edit, sort, filter, and search BibTeX databases
* View and edit BibTeX strings or import strings from external files
* Customizable editor layouts
* Shortcuts for common operations, such as protecting upper case letters or converting between unicode and LaTeX

## Caveats
* Bada Bib! is still under development and you might run into bugs at any time. **Please make sure you have backups of your files!**
* Bada Bib! can be slow when working with large databases or databases with a large number of strings. This is partly due to Bada Bib! not being optimized for speed yet, partly due to limitations of python-bibtexparser and Python in general.
* Bada Bib! is not supposed to be a replacement for fully fledged reference managers such as [JabRef](https://github.com/JabRef/jabref), [KBibTeX](https://invent.kde.org/office/kbibtex), [Mendeley](http://mendeley.com/), [Zotero](https://www.zotero.org/), and [others](https://en.wikipedia.org/wiki/Comparison_of_reference_management_software).
* Bada Bib! automatically recognizes if an expression is the name of a string and treats it as such. That is, if `@string { foo = "bar" }` is defined, `foo` will be treated as a string, unless it is enclosed in braces `{foo}`. 

## Screenshots
Main Window
![Main window](/data/screenshots/editor.png)

String Manager
![String Manager](/data/screenshots/string_manager.png)

Icon by svgrepo.com


