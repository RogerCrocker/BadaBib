# default_layouts.py
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


layout_string_article = """
# Editor layout for entrytype 'article'

ID ENTRYTYPE
---
author
title
journal
year volume
---
number pages
month doi
url
note
keywords
---
abstract
"""


layout_string_book = """
# Editor layout for entrytype 'book'

ID ENTRYTYPE
---
author
editor
title
publisher year
---
volume number
series address
edition month
note
keywords
url
"""


layout_string_booklet = """
# Editor layout for entrytype 'booklet'

ID ENTRYTYPE
---
title
---
author howpublished
address month
year
note
keywords
"""


layout_string_conference = """
# Editor layout for entrytype 'conference'

ID ENTRYTYPE
---
author
title
booktitle
year
---
editor volume
number series
pages address
month organization
publisher
note
keywords
"""


layout_string_inbook = """
# Editor layout for entrytype 'inbook'

ID ENTRYTYPE
---
author
editor
title
chapter pages
publisher year
---
volume number
series type
address edition
month
note
keywords
"""


layout_string_incollection = """
# Editor layout for entrytype 'incollection'

ID ENTRYTYPE
---
title
booktitle
year
---
editor volume
number series
type chapter
pages address
edition month
note
keywords
"""


layout_string_inproceedings = """
# Editor layout for entrytype 'inproceedings'

ID ENTRYTYPE
---
author
title
booktitle
year
---
editor volume
number series
pages address
month organization
publisher doi
note
keywords
"""


layout_string_manual = """
# Editor layout for entrytype 'manual'

ID ENTRYTYPE
---
title
---
author
organization address
edition month
year
note
keywords
"""


layout_string_matherthesis = """
# Editor layout for entrytype 'masterthesis'

ID ENTRYTYPE
---
author
title
school year
---
type address
month
note
keywords
"""


layout_string_misc = """
# Editor layout for entrytype 'misc'

ID ENTRYTYPE
---
author
title
howpublished doi
month year
note
keywords
"""


layout_string_online = """
# Editor layout for entrytype 'online'

ID ENTRYTYPE
---
author
title
publisher
year month
url
note
keywords
"""


layout_string_phdthesis = """
# Editor layout for entrytype 'phdthesis'

ID ENTRYTYPE
---
author
title
school year
---
type address
month
note
keywords
"""


layout_string_proceedings = """
# Editor layout for entrytype 'proceedings'

ID ENTRYTYPE
---
title
year doi
---
editor
volume number
series address
month publisher
organization
note
keywords
"""


layout_string_techreport = """
# Editor layout for entrytype 'techreport'

ID ENTRYTYPE
---
author
title
institution year
---
type number
address month
note
keywords
"""


layout_string_unpublished = """
# Editor layout for entrytype 'unpublished'

ID ENTRYTYPE
---
author
title
note
---
month year
keywords
"""


default_layout_strings = {
    "article": layout_string_article,
    "book": layout_string_book,
    "booklet": layout_string_booklet,
    "conference": layout_string_conference,
    "inbook": layout_string_inbook,
    "incollection": layout_string_incollection,
    "inproceedings": layout_string_inproceedings,
    "manual": layout_string_manual,
    "masterthesis": layout_string_matherthesis,
    "misc": layout_string_misc,
    "online": layout_string_online,
    "phdthesis": layout_string_phdthesis,
    "proceedings": layout_string_proceedings,
    "techreport": layout_string_techreport,
    "unpublished": layout_string_unpublished,
}
