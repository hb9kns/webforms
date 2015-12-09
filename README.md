# webforms

CGI script for dynamic web forms using a flat file database,
only server-side

## Introduction

The data structure is very simple: There is one base or index file,
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
are ignored as well.

### example base/index file

	# flag	index	name	given	mail

	+	1001	Deere	John	jode@example.com
	# Jamie is no longer active ("deleted")
	-	1002	Crown	Jamie	jacr@example.com
	+	1003	Baker	Jack	jaba@example.com
	+	1004	Able	Joan	joab@example.com

### example record file

	# flag	index	arrival	departure
	
	*	1001	January 2013	present
	-	1002	March 1987	June 2001
	*	1003	April 1984	present
	*	1004	June 2014	November 2015

In this case, the index entry 1002 would no longer be available in the
record tables, and the entry for index 1002 would not be displayed,
when the record file is rendered. (For the time being, the flag only
has meaning in the base/index file, but may be used in future also in
record files.)