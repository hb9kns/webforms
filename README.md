# webforms

CGI script for dynamic web forms using flat file databases,
server-side only

---

## Overview

Web-based database applications often need complicated installation
of libraries or programs, or rely on Javascript and other techniques
which depend on the available clients. The script presented here
is a simple solution for simple problems, and it only needs a
working Unix environment and a simple webserver with CGI capability.

The data structure handled by this script is as follows.  A list
of unique names, each with optional attributes (text fields), is
the backbone of the entire structure, called the *index* or *base.*
Each of these index names may have exactly one entry in each of a
number of pages, while all entries in a given page have the same
structure of additional fields.

(In principle, the same functionality can be provided by one single
big list with exactly one entry per index name, but it would be
rather impractical to handle and process.)

An example of this structure may be an index of user names (or
personnel numbers), with attributes like full name, address,
telephone numbers and e-mail address, and a collection of lists
(pages) with exactly one entry per person (or none at all) in each
list. The lists might contain data like access rights to various
equipment, subscription data to mailing lists, number of hours
worked, etc.

Another example would be an index of computers with attributes like
system responsibles and location or use, and lists with patch
information, available periphery/accessories, or running costs.

## Installation

The script must be installed in a directory where CGI scripts can
be executed.  It must be called (e.g, by some HTML link) with at
least the variable `db` set, like
`http://example.com/somedir/webforms.cgi?db=test` .

Calling it without any `db` value will generate a fatal error unless
the default configuration file `defcfg.cfg` exists in the path of
the script.  Of course this can be modified in the script, if the
database should be hardcoded.

To work properly, at least the configuration file (`test.cfg` for
the above example) and the pages referred by it must exist and be
readable and writable for the script. A minimal installation
therefore consists in the script itself, a configuration file
`*.cfg` , an index/base file, and one page file.

## Files

### Database structure

There is one *base* or *index* file, containing one unique index
number/name per line, with one or more descriptive fields.  This
index is used as reference in additional files, which again contain
a field for the index, and an arbitrary number of record fields.
Each of these files are rendered as HTML tables by the script.

All lines start with a flag character, which is one of the set
`#+-*` (possibly more in future versions).  All fields are separated
by `TAB` characters which therefore are forbidden as content of any
field.

- Lines beginning with `#` (comments) or any unrecognized character are completely ignored, as well as empty lines.
- The first line starting with `*` is the table header; any additional line starting with `*` is ignored.
- Lines beginning with `+` or `-` are database entries, and their fields after `+` or `-` contain the index.
- The order of lines may be changed by the CGI script, except for comment and header lines at the beginning of files, which will stay there. Any later interspersed comment or header lines may be moved to the beginning as well.

*Index fields must be unique,* and this is enforced by the script:
any duplicate entry may be overwritten and only one retained.

Normally, entry lines start with the `+` flag character. This
renders them as available or "shown."

Index entries with leading `-` are not available for edition or
creation of page entries, i.e, any entry with such an index name
cannot be modified and is "hidden."  When an index entry is to be saved, the
show/hide operation can also be applied to all pages, i.e the
corresponding page records are simultaneously shown/hidden.

Header fields with the structure `list=listname` will result in the
corresponding field being a selection field, with options coming from
all lines of the file `listname` beginning with '+' (only the part after
TAB is used). This allows to predefine a limited number of possible
entries for certain fields.

Header fields with `xlist=...` instead of `list=...` allow for
evaluation of selection fields, which may be a security risk.
(This feature is deactivated by default, and must be activated by
setting the appropriate flag at the beginning of the source code.)
See the example further below for the syntax of list file entries!

Header fields with the structure `now=description` or `day=description`
will result in the corresponding field being a selection field, with
options empty, old value, or current time (in minute resolution, for
`now=` header) or day (for `day=` header). In case of `now=` fields,
the time will be followed by `=NNNN` where `NNNN` is the epoch time
(in general since Jan.1st 1970 UTC) in minutes; this can be used for
logbook applications to calculate time differences.

Page entries with leading `-` normally are not displayed when the
page is rendered, but they can be "un-hidden," and also be edited.

Please note that any existing entry (index or page data) may be overwritten
without warning, if the user has appropriate permissions.

#### example base/index file

_Please note the TAB characters always separating fields!_

	# names and email addresses
	*	PersNr	Family name	Name	E-Mail	list=color
	+	1001	Family01	One	one@example.com	red
	+	1003	Family03	Three	three@example.com	green
	+	1005	Family05	Four	four@example.org	blue
	+	1008	Family08	Eight	eight@example.com	black
	+	1006	Family06	Six	six@example.org	yellow
	+	1004	Family04	Four	four@example.com	lilac
	+	1007	Family07	Seven	seven@example.org	amber
	-	2001	Family9000	HAL	hal9000@example.com	gold
	+	1002	Family02	TwoTwo	totwo@example.net	cyan

#### example record file

	# entrance and leave database
	*	PersNr	day=Arrival date	day=Departure date	list=divis
	+	1008	sooner	later	HR
	+	1006	2015-01-22	2015-12-1	IT
	+	1007	May 1984	present	IT
	-	1002	2015-01-22	2015-12-19	mgmt
	+	1003	June 2014	November 2015	finances
	+	1004	June 2008	August 2015	production
	+	1005	beginning	end	production
	+	1001	April 1948	2001	HR

In this case, the index entry 2001 would not be available in the
record tables, and the entry for index 1002 would not be displayed,
when the record file is rendered.

#### example list file

	# favourites
	*	color
	+	green
	+	blue
	+	cyan
	+	gold
	+	black	5
	+	lilac
	+	amber

The selection `black` is only allowed for up to 5 times in a page.
The other selections have no limits.

#### example evaluation list file

	# evaluate
	* varia
	+	blue
	+	system	=	$DEFCOLOR

The selection `system` will be displayed as the content of the variable
`$DEFCOLOR` which might be defined in the environment.

Effectively, if the third column (not counting the '+') of a selection
entry is not empty, it will be evaluated by the webforms script, and
in this case, the first column is an irrelevant placeholder.
This allows for dynamic content, e.g a list with entries

	+	--
	+	now	=	$field
	+	now	=	$nowstring=$nowminutes

will have the same functionality as a column with a `now=XXXX` header
(`$field`, `$nowstring` and `$nowminutes` are internals of the script),
and the entry

	+	host	=	`hostname`

will evaluate to a selection of the current hostname (if this command
is available to the shell).

**WARNING: Be careful with this powerful type of list,**
**there might be side effects affecting the script or environment!**
**Any user who can control such entries in the list file**
**can execute arbitrary shell commands through the script!**

### Configuration file

Each collection of webforms is defined by a configuration file with
suffix `.cfg` , which is indicated to the CGI script by a GET
variable and a hardcoded directory, or completely hardcoded for
improved safety.

This file contains the name of the base/index file (indicated by
a leading `base` field), and the names of the (one or more) page
files (indicated by `page/upag/ulog`). Each file name must be prepended with
the page name, and may be followed by a description, which will be
included in the rendered page headers.
The page name for the index file must be set to `file` for correct syntax.

Pages with type `upag` instead of `page` allow for user-dependant entries:
Unless the user has editor permission or higher (see below for permissions),
they can only access page entries with an index field corresponding to
their own user name. This can be used to let users submit entries from a
given number of options, or handle their self-supplied data.

Pages with type `ulog` instead of `page` allow for user-dependant
entries with timestamps: Indices will be generated as username followed
by underscore `_` and a number-only timestamp, and non-admin users can
only generate entries with their username as index prefix.
This can be used for logbook entries of different users.

List files used for populating selection fields are indicated by `list`
(or `xlist` for selections allowing dynamic evaluation)
followed by their reference name, file name, and optionally description.

File names can be absolute or relative; the starting directory is the
working directory of the CGI script.

By setting the entry `nopageindex` to something else than `false` or `0` ,
displaying of the column for the index/base string can be suppressed.
This column normally is shown as the first one in page views,
but it may be of little use in case of numeric or random-like values.

With the field `emptywarn` a string can be defined which will be displayed
in place of empty fields. This can be any valid HTML code (see example).

The entry `showindex` can be used to indicate additional fields from the
index/base file to be displayed in pages. The field positions correspond
to the header fields of the base file, and any `showindex` field other than
`-` will display the corresponding base entry field with its name as header,
c.f example configuration.

The value after `maxfieldlength` will limit form entry fields to the given
character length; however, any length will displayed when database contents
are rendered.

With `fieldchars` the permitted characters in entry fields can be listed.
By default, all printable ASCII characters are allowed. `TAB` is always
excluded from all fields, though.

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

User names are sanitized: only characters from the set '0-9A-Za-z.-' are
allowed, and entries in the configuration file must conform to this.

Logging can be switched on by setting the field `log` with page name 'file'
and the file name. If the file is not writable, no logging will occur, without
any error.

#### example configuration file

	# test config file
	# file definitions
	# base	file	relative/path/to/basefile.txt	basefile description
	base	file	test.base	People
	page	dates	test.dates	Dates
	# in 'phone' page, users below admin level only see their own entries
	upag	phone	test.phone	Phone numbers
	list	color	test.color	favourite color
	xlist	varia	test.eval	various dynamic values
	list	divis	test.div	company division
	# uncomment to suppress displaying index/base field in page view
	#nopageindex	true
	# user permissions:
	admin	chief	nobody
	editor	deputy
	# if visitor line is defined, only allow explicitly listed users
	visitor	dings
	# display definitions:
	# additional index field names to be shown in pageviews:
	# skip fields with a single dash '-', never use '|' in these names!
	# here, the 3rd and 4th index/base entry fields are used, and the
	# 1st and 2nd are skipped
	showindex	-	-	Email	Fav.color
	# how to warn about empty fields (can be undefined)
	emptywarn	<font color="red"><b>#EMPTY#</b></font>
	# reduce the maximum size of text fields in record input form
	maxfieldlength	80
	# logfile (no logging if unwritable!)
	log	file	test.log
	# pattern of allowed characters in fields,
	# default = all ASCII characters from SPC to ~ (tilde)
	#fieldchars	' -~'

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
- If a file 'help.html' exists in the working directory, it will be linked at the upper right corner of every page generated.
- If a file 'style.css' exists in the working directory, it will be used as stylefile for every page generated.
