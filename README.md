# webforms

CGI script for dynamic web forms using flat file databases,
server-side only

---

## Overview

Web-based database applications often need complicated installation
of libraries or programs, or rely on Javascript and other techniques
which depend on the available clients. The script presented here is a
simple solution for simple problems, and it only needs a working Unix
environment and a simple webserver with CGI capability.

The data structure handled by this script is as follows.  A list
of unique names, each with optional attributes (text fields), is the backbone of the
entire structure, called the *index* or *base.*  Each of these index names
may have exactly one entry in each of a number of pages, while all
entries in a given page have the same structure of additional fields.

(In principle, the same functionality can be provided by one single big
list with exactly one entry per index name, but it would be rather impractical
to handle and process.)

An example of this structure may be an index of user names
(or personnel numbers), with attributes like full name, address, telephone
numbers and e-mail address, and a collection of lists (pages) with
exactly one entry per person (or none at all) in each list. The lists might contain
data like access rights to various equipment, subscription data to
mailing lists, number of hours worked, etc.

Another example would be an index of computers with attributes like
system responsibles and location or use, and lists with patch information,
available periphery/accessories, or running costs.

## Installation

The script must be installed in a directory where CGI scripts can be executed.
It must be called (e.g, by some HTML link) with at least the variable `db`
set, like `http://example.com/somedir/webforms.cgi?db=test` .

Calling it without any `db` value will generate a fatal error unless the default configuration
file `defcfg.cfg` exists in the path of the script.
Of course this can be modified in the script, if the database should be hardcoded.

To work properly, at least the configuration file (`test.cfg` for the above example)
and the pages referred by it must exist and be readable and writable for
the script. A minimal installation therefore consists in the script itself,
a configuration file `*.cfg` , an index/base file, and one page file.

## Files

### Database structure

There is one *base* or *index* file,
containing one unique index number/name per line, with one or more descriptive
fields.  This index is used as reference in additional files, which
again contain a field for the index, and an arbitrary number of record
fields. Each of these additional files are rendered as HTML tables by the script.

All lines start with a flag character, which is one of the set `#+-*` (possibly more in future versions).
All fields are separated by `TAB` characters which therefore is forbidden as content of any field.
Lines beginning with `#` (comments) or any unknown character are ignored. Empty lines are ignored as well.
The first line starting with `*` is the table header; any additional line starting with `*` is completely ignored.

Index fields must be unique, and this is enforced by the script: any duplicate entry may be overwritten and only one retained.

Normally, entry lines start with the `+` flag character. This renders them as available.

Index entries with leading `-` are not available for edition or creation of page entries,
i.e, any entry with such an index name cannot be modified.
When an index entry is to be saved, the show/hide operation can also be applied to all
pages, i.e the corresponding page records are simultaneously shown/hidden.

Page entries with leading `-` normally are not displayed when the page is rendered,
but they can be un-hidden, and also be edited.

Please note that any entry (index or page data) may be overwritten without warning,
if the user has appropriate permissions.

#### example base/index file

	# names and email addresses
	# Jamie is no longer active ("deleted")
	*	index	name	given	mail
	+	1001	Deere	John	jode@example.com
	-	1002	Crown	Jamie	jacr@example.com
	+	1003	Baker	Jack	jaba@example.com
	+	1004	Able	Joan	joab@example.com

#### example record file

	# entrance and leave database
	*	index	arrival date	departure date
	+	1001	January 2013	present
	-	1002	March 1987	June 2001
	+	1003	April 1984	present
	+	1004	June 2014	November 2015

In this case, the index entry 1002 would no longer be available in the
record tables, and the entry for index 1002 would not be displayed,
when the record file is rendered.
The latter can be changed in the page view, however.

### Configuration file

Each collection of webforms is defined by a configuration file with
suffix `.cfg` , which is indicated to the CGI script by a GET
variable and a hardcoded directory, or completely hardcoded for
improved safety.

This file contains the name of the base/index file (indicated by
a leading `base` field), and the names of the (one or more) page
files (indicated by `page`). Each file name must be prepended with
the page name, and may be followed by a description, which will be
included in the rendered page headers.
The page name for the index file must be set to `file` for correct syntax.

By setting the field `nopageindex` to something else than `false` or `0` ,
displaying of the column for the index/base string can be suppressed.
This column normally is shown as the first one in page views,
but it may be of little use in case of numeric or random-like values.

With the field `emptywarn` a string can be defined which will be displayed
in place of empty fields. This can be any valid HTML code (see example).

Permission levels for user names (passed via `REMOTE_USER` from the webserver)
can be set with field names `admin/editor/visitor`.
If a `visitor` line is present, then *only users explicitly listed*
on any of the permission lines are allowed to access the script.
Otherwise, all users not listed as `admin` or `editor` are allowed
only `visitor` access (i.e, read-only access to all pages).

If `admin` or `editor` lines contain the wildcard `*` then any user will get
the corresponding permissions. The highest level available will be applied.
E.g, an entry of `admin	*` will grant admin permissions to all users,
even if they are listed in `editor` or `visitor` lines.

Logging can be switched on by setting the field `log` with page name 'log'
and the file name. If the file is not writable, no logging will occur without
error.

#### example configuration file

	# test suite configuration
	# type	name	filename
	base	file	relative/path/to/basefile.txt	basefile description
	page	pageone another/path/to/pageone.txt	page one description
	page	pagetwo	/absolute/path/to/pagetwo.txt	page two description
	# suppress displaying index/base field in page view
	nopageindex	true
	# reduce the maximum size of text fields in record input form
	maxfieldlength	80
	# logfile (no logging if unwritable!)
	log	file	test.log
	# how to warn about empty fields (can be undefined)
	emptywarn	<font color="red">/EMPTY/</font>
	# pattern of allowed characters in fields,
	# default = all ASCII characters from SPC to ~ (tilde)
	#fieldchars	' -~'
	# type	names
	admin	chief	johnny	sue
	editor	pam	james
	# (due to visitor line, allow only explicitly listed users)
	visitor	jimmy

## CGI

The script renders various pages, based on CGI environment variables:

- `db` config file
- `pg` page name
- `in` index number
- `vw` view (display selection)
- `sc` sort column
- `sd` sort direction
- `fa` flag for hiding/showing entries
- `fN` field number N

### view/command variable `vw`

This variable value selects the view or command.

- undefined or unknown command: default view rendered according to `db` value
- `vw=listpages` list all available pages
- `vw=page` display page
- `vw=listindex` list all indices
- `vw=descindex` details of index entry
- `vw=editindex` edit index entry
- `vw=saveindex` save index entry
- `vw=editentry` edit page entry/record
- `vw=saveentry` save page entry/record

---

## Version control, logging

By default, version control is done in a very simple way: For each database
file, an old version with the suffix `.old` is saved, and the result from
`diff -e $new $old` is appended to a file with the suffix `.diff` .
(For this to work, the script of course must be able to write to these files.)
In principle, from this any old version can be reconstructed, but currently
there is no automatic way provided.

Version control can also be done with RCS or Git.
However, for this to work, the function `dobackup`
must be modified; please read the source!

If defined, the logfile contains information about all runs of the script,
including user and remote host information -- be careful about privacy issues!

---

## Notes

- The script attempts to lock all database files before writing anything, and fails if not successful after some retries.
- Write permissions are only verified for `vw=saveindex` or `vw=saveentry` but not for the corresponding edit commands.
- For `vw=editindex` the script tries to generate a new and unique index number, if numerical index values are encountered.
- Saving an entry for any existing index will overwrite the former content.
- Entries cannot be deleted by the script; this has to be done manually in the database files.
