# webforms

CGI script for dynamic web forms using a flat file database, server-side only

---

## Files

### Database structure

There is one base or index file,
containing one unique index number per line, with one or more descriptive
fields.  This index is used as reference in additional files, which
again contain a field for the index, and an arbitrary number of record
fields. Each of these additional files can be rendered as HTML tables,
with any or several of the index description fields and the corresponding
record fields per line.

All lines start with a flag character, which is one of the set `#+-*`
or something else in future versions. All fields are separated by TAB
which therefore is forbidden as content of any field.  Lines beginning
with `#` (comments) or any unknown character are ignored.  Empty lines
are ignored as well. The first line starting with `*` is the table header;
any additional line starting with `*` is completely ignored.

Index fields must be unique, and this is enforced by the script:
any duplicate entry may be deleted and only one retained.

#### example base/index file

	# names and email addresses
	
	*	index	name	given	mail
	+	1001	Deere	John	jode@example.com
	# Jamie is no longer active ("deleted")
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

Each collection of webforms is defined by a configuration file,
which is indicated to the CGI script by a GET variable and a
hardcoded directory, or completely hardcoded for improved safety.
Its name has the suffix `.cfg` (mandatory).

This file contains the name of the base/index file (indicated by
a leading `index` field), and the names of the (one or more) page
files (indicated by `page`). Each file name must be prepended with
the page name, and may be followed by a description, which will be
included in the rendered page headers. (The page name is irrelevant
for the index file, but any must be given.)

By setting the field `nopageindex` to something else than `false` or `0` ,
displaying of the column for the index/base string can be suppressed.
This column normally is shown as the first one in page views,
but it may be of little use in case of numeric or random-like values.

Permission levels for user names (passed via `REMOTE_USER` from the webserver)
can be set with field names `admin/editor/visitor`.
If a `visitor` line is present, then *only users explicitly listed*
on any of the permission lines are allowed to access the script.
Otherwise, all users not listed as `admin` or `editor` are allowed
only `visitor` access (i.e, read-only access to all pages).

#### example configuration file

	# test suite configuration
	# type	name	filename
	index	dummy	relative/path/to/basefile.txt	basefile description
	page	pageone another/path/to/pageone.txt	page one description
	page	pagetwo	/absolute/path/to/pagetwo.txt	page two description
	# suppress displaying index/base field in page view
	nopageindex	true
	# reduce the maximum size of text fields in record input form
	maxfieldlength	80
	# pattern of allowed characters in fields
	# default: all ASCII characters from SPC to ~ (tilde)
	# fieldchars	' -~'
	# type	names
	admin	chief	johnny	sue
	editor	pam	james
	visitor	guest

## CGI

The script renders various pages, based on CGI environment variables:

- `db` config file _(ignored if hardcoded)_
- `pg` page name
- `in` index number
- `vw` view (display selection)
- `sc` sort column
- `sd` sort direction
- `fa` flag for active/hidden entry
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