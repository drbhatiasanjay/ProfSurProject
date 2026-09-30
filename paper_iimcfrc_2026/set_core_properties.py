"""
Clean up python-docx's default core-properties fingerprints before a paper
is submitted anywhere. Copy this file into your project's docs/ folder
alongside paper_helpers.py.

python-docx's Document() leaves forensic tool-generation fingerprints by
default:
  - core_properties.author / last_modified_by are blank, or literally
    "python-docx" depending on version.
  - core_properties.created / modified are stuck at python-docx's
    hardcoded stock timestamp (2013-12-23 23:15:00 UTC), regardless of
    when the file was actually generated.

Neither is fabrication when the named person really is the author -- it's
correcting metadata that would otherwise misrepresent authorship (blank)
or generation time (a decade-old stock timestamp), the same way you'd fix
a wrong byline or a wrong "last saved" date in any other tool.

Usage:

    from set_core_properties import set_core_properties

    doc = Document()
    ... build the paper ...
    set_core_properties(
        doc,
        author='Jane Researcher',
        title='Exact Paper Title As It Appears On The Title Page',
        corresponding_email='jane@university.edu',   # optional
        last_modified_by=None,                         # defaults to author
    )
    doc.save('paper_v1.docx')
"""

from datetime import datetime, timezone


def set_core_properties(doc, author, title, corresponding_email=None,
                         last_modified_by=None, subject='', keywords='',
                         comments=''):
    """
    Set docx core properties to real values instead of python-docx defaults.

    Args:
        doc: a docx.Document instance, not yet saved.
        author: the actual human author name (or "First Author; Second
            Author" for multi-author papers -- core_properties.author is a
            single string field, not a list).
        title: the paper's exact title, matching the title page.
        corresponding_email: optional; appended to `comments` if given,
            since core_properties has no dedicated email field.
        last_modified_by: defaults to `author` if not given.
        subject, keywords, comments: cleared by default (empty string)
            rather than left at whatever python-docx or a prior save set
            them to -- set explicitly if your venue wants keywords/JEL
            codes recorded here as well as in the visible title block.
    """
    cp = doc.core_properties
    cp.author = author
    cp.last_modified_by = last_modified_by or author
    cp.title = title
    cp.subject = subject
    cp.keywords = keywords
    cp.comments = (comments + (f' Corresponding author: {corresponding_email}'
                                if corresponding_email else '')).strip()

    now = datetime.now(timezone.utc)
    cp.created = now
    cp.modified = now
