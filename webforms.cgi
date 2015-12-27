#!/bin/sh
# webforms.cgi (2015 Yargo Bonetti)
# CGI script for handling flat file databases with common index/base

# set root for temporary files
# (make sure this is a pattern for non-important files, as there
# will be an 'rm -f $tmpr*' command at the end of the script!)
tmpr=${TMP:-/tmp}/webform-$user-tmp$$

# save new version of database; arg.1 = modified file, arg.2 = remarks
# (user name and REMOTE_HOST will be added to the remarks)
dobackup(){
 dmesg="$2 (user=$usr, host=$REMOTE_HOST)"
# comment/uncomment below as desired! commenting out all is also possible
## git version
 #git add "$1" && git commit -m "$dmesg"
## rcs version
 #ci -l -w$usr -m"$dmesg" "$1"
## poor man's version -- if commenting, do all lines of <<HERE document!
 cat <<EOH >>$1.diff

## `date '+%y-%m-%d,%H:%M'` : $dmesg
EOH
# ed-like diff (shortest, and can be more easily replayed)
 diff -e "$1.old" "$1" >>"$1.diff"
 cat "$1" > "$1.old"
# make sure backup files cannot be read by all
 chmod o-rwx "$1.old" "$1.diff"
}

# default permitted characters in record fields: SPC and printable ASCII
# as 'tr' pattern
defaultfieldchars=' -~'

##### ONLY CHANGE BELOW IF YOU KNOW WHAT YOU ARE DOING! #####

pjthome=http://gitlab.com/yargo/webforms

REQUEST_METHOD=`echo $REQUEST_METHOD | tr a-z A-Z`
if test "$REQUEST_METHOD" != "POST" -a "$REQUEST_METHOD" != "GET"
then cat <<EOT

This is $0
which must be run as a CGI script, expecting input from POST or GET requests.

See accompanying README file, or online repository at
	$pjthome
for further information.

EOT
exit 9
fi

myself=`basename "$0"`
mydir=`dirname "$0"`

# temp files for input
tmpf=$tmpr.tmp
inpt=$tmpr.inp

cat >$tmpf
echo "$QUERY_STRING" >>$tmpf

# save STDIN (POST input) in decoded form:
# first translate '+' into SPC and ';&' (separators) into new lines
# (note: after the last "'" there is a SPC!)
# then permitted escaped characters (restricted for security reasons)
cat $tmpf | tr '+;&' ' 
' | sed -e "s/%C2%B0/deg/g;s/%B0/deg/g;
 s/%2B/+/g;s/%22/\"/g;s/%26/&/g;s/%2F/\//g;s/%28/(/g;s/%29/)/g;s/%3D/=/g;
 s/%3F/?/g;s/%27/'/g;s/%5E/^/g;s/%7E/~/g;s/%3C/</g;s/%3E/>/g;
 s/%7B/{/g;s/%7D/}/g;s/%5B/[/g;s/%5C/\//g;s/%5D/]/g;s/%21/!/g;s/%24/\$/g;
 s/%2C/,/g;s/%3B/;/g;s/%3A/:/g;s/%23/#/g;s/%7C/|/g;s/%60/'/g;s/%40/@/g;
 s/%25/%/g" >$inpt

### now some functions!

# end script after cleanup with exit code as arg.1
finish(){
/bin/rm -f ${tmpr}*
sleep 1 # to reduce possible load
# exit code arg.1, or 0 if missing
exit ${1:-0}
}

# report fatal failure and quit
fatal(){
 cat <<EOT
Content-type: text/plain

fatal error from $myself:

    $*

---

my relative directory: $mydir
my absolute directory: `pwd -P`

---

parsed input:

EOT
cat $inpt
finish 5
}

# get values from decoded input data; optional arg.2 = permitted characters
inptvar(){
 local permchar
# default safe characters
 permchar="${2:-0-9.A-Za-z_-}"
 grep "^$1=" $inpt | head -n 1 | sed -e 's/[^=]*=//' | tr -c -d "$permchar"
}

# get lines beginning with a value, and remove that column
getlines(){
 grep "^$1" | { IFS="	" # record separator TAB only
 while read _ values
 do echo "$values"
 done
 }
}

# check whether entry is present on some line
checkline(){
local entry found
entry="$2"
found=0
# read lines, surround with TAB (in sed pattern), and check if somewhere
getlines "$1" | sed -e 's/^/	/;s/$/	/' | grep "$entry" 2>&1 >/dev/null
}

# display header, arg.1 = page title, arg.2 = main title, arg.3 = description
header(){
cat <<EOH
Content-type: text/html

<html><head><title>$1</title>
<META HTTP-EQUIV="Pragma" CONTENT="no-cache">
<META HTTP-EQUIV="Expires" CONTENT="-1">
</head>
<body>
<p align="right">
<tt>`date '+%a %Y-%m-%d %H:%M'` // db=$db // $usr($perms)</tt>
</p>
<p>
EOH
if test "$pg" != ""
then cat <<EOH
:: <a href="$myself?db=$db&pg=$pg&vw=page">&laquo;<tt>$pg</tt>&raquo;</a>
EOH
fi
cat <<EOH
:: <a href="$myself?db=$db&vw=listpages">all pages</a>
:: <a href="$myself?db=$db&vw=listindex">index/base</a>
:: </p>
<hr />
<h1>$2</h1>
EOH
shift
shift
cat <<EOH
<p>$*</p>
EOH
}

# display footer with some additional info
footer(){
cat <<EOH
<hr />
<p><small><i>processed by <a href="$pjthome">$myself</a></i></small></p>
<pre>
EOH
# cat $inpt # for debugging
cat <<EOH
</pre>
</body>
<head>
<META HTTP-EQUIV="Pragma" CONTENT="no-cache">
<META HTTP-EQUIV="Expires" CONTENT="-1">
</head>
</html>
EOH
}

# both following functions only process first ocurrence of page
# get file name for arg.1=type, arg.2=page
pagefile(){
# get file name
 getlines $1 <$cfg | getlines $2 | { IFS="	" # TAB
  read pfile _
# sanitize
  pfile=`echo $pfile | tr -c -d '0-9.A-Za-z_-'`
# generate probably nonexistent file name, if empty (to later raise errors)
  pfile=${pfile:-`uuidgen`}
# don't change, if it starts with '/'
# else prepend webform root directory
  case $pfile in
   /*) echo "$pfile" ;;
   *) echo "$wdir/$pfile"
  esac
 }
}

# get page info for arg.1=type, arg.2=page
pageinfo(){
 getlines $1 <$cfg | getlines $2 | { IFS="	" # TAB
  read _ pinfo
  echo "$pinfo"
 }
}

# print HTML table head for arg.1=file, arg.2=start column
# exit code = number of rendered columns
tablehead(){
 local skip nc nd
 skip=${2:-0}
 sc=${sc:-1}
 sd=${sd:-0}
 nc=1
 echo '<table><tr>'
# get first line beginning with '*' ('[*]' for grep pattern)
# (note TAB in sed pattern)
 getlines '[*]' <$1 | head -n 1 | sed -e 's/	/\
/g' | { while read field
  do
# for column selected for sorting, invert next sort order
   if test $nc = $sc
   then nd=`expr 1 - $sd`
   else nd=$sd
   fi
# skip start columns
   if test $skip -gt 0
   then skip=`expr $skip - 1`
# render column title with sort link
   else cat <<EOH
<th><a href="$myself?db=$db&pg=$pg&vw=$vw&sc=$nc&sd=$nd">$field</a></th>
EOH
   fi
   nc=`expr $nc + 1`
  done
# report number of columns outside
  expr $nc - 1 >$tmpf
 }
 echo '</tr>'
 return `cat $tmpf`
}

tablefoot(){ echo '</table>' ; }

# attempt to get a lockfile (arg.1)
lockfile(){
 local lf lc
 lc=9 # timeout counter
 lf="$1.lock"
# while file already present, and not yet timeout
 while test -f "$lf" -a $lc -gt 0
 do lc=`expr $lc - 1`
  sleep 2
 done
 if test -f "$lf"
# if file still exists, fail with empty reply
 then echo
 else
# save some debugging stuff
  echo lockfile from $myself > "$lf"
  date -u '+%Y-%m-%d,%H:%M:%S' >> "$lf"
  printenv | sort >> "$lf"
# reply with file name
  echo "$lf"
 fi
}

# release locked file by deleting lockfile
releasefile(){
 if test "$1" != ""
 then /bin/rm -f "$1"
 fi
}

# render warning about missing permissions (arg.1 = necessary)
permwarn(){
 local p
 p=${1:-0}
 if test $p -gt $perms
 then cat <<EOH
<p><em>Warning!</em>Your permission level $perms is lower than necessary ($p) for modification!<br />
Therefore, any save/modification action may fail!</p>
EOH
 fi
}

# function for displaying index entries
# maxindex must be initialised globally, as well as CGI variables db, pg, in
# arg.1,2 = additional tags for each index entry
renderindices(){
 local pastind i ofs
 ofs="$IFS"
 IFS="	" # TAB
 i=1
 while read in desc
# use index for link to edit view, marked with tags
 do cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$pg&in=$in&vw=editindex">$1$in$2</a></td>
EOH
# split description into table fields
  echo "<td>$desc</td>" | sed -e 's:	:</td><td>:g'
  echo '</tr>'
# convert last index to numeric value and increment,
# or set to counter value, if non-numeric
  pastind=`expr $in + 1` ; pastind=${pastind:-$i}
  if test $maxindex -lt $pastind
  then maxindex=$pastind
  fi
  i=`expr $i + 1`
 done
# report outside
 echo $maxindex >$tmpf
 IFS="$ofs"
}

### now preparations for the main script!

# set root for configuration files / working directory
# (this could be set to some hardcoded directory for improved security)
wdir=${WEBFORMSDIR:-$mydir}
# default/fallback
defcfg=default

# define config file name
db=`inptvar db '.0-9A-Za-z_-'`
cfg="$wdir/${db:-defcfg}.cfg"
if test ! -r "$cfg"
then fatal "configuration file $cfg not readable"
# this should never be reached, but just to be sure:
 exit 9
fi

# define index/base file name, '.' is wildcard for index name
idx="`pagefile base . <$cfg`"
if test ! -r "$idx"
then fatal "index/base file $idx not readable"
 exit 9
fi

permadmin=100
permeditor=10
permvisitor=1
# establish permissions (the higher, the better)
perms=0
usr=${REMOTE_USER:-nobody}
if checkline admin $usr <$cfg
then perms=$permadmin
else
 if checkline editor $usr <$cfg
 then perms=$permeditor
 else
# if "visitor" entries exist, user must be explicitly allowed
  if grep "^visitor" $cfg 2>&1 >/dev/null
  then
   if checkline visitor $usr <$cfg
   then perms=$permvisitor
   else perms=0
   fi
# otherwise all unknown users are visitors
  else perms=$permvisitor
  fi # visitor
 fi # editor
fi # admin

# define link field for page view
nopageindex=0
# set to first record field, if nopageindex present with any value
if checkline nopageindex '.*' <$cfg
then nopageindex=1
fi
# reset to index field, if false or 0
if checkline nopageindex false <$cfg
then nopageindex=0
fi
if checkline nopageindex 0 <$cfg
then nopageindex=0
fi

# define permitted characters for record fields
fieldchars=`getlines fieldchars <$cfg | head -n 1`
fieldchars=${fieldchars:-$defaultfieldchars}

# at least permission 1 is necessary for running script at all
if test $perms -lt 1
then fatal user $usr is not allowed
 exit 9
fi

# get and normalize sort column and order
sc=`inptvar sc '0-9'`
sc=${sc:-1}
if test $sc -lt 1
then sc=1
fi
sd=`inptvar sd '0-9'`
# define option flag for sort command
case $sd in
 0) sortopt='' ;;
 1) sortopt='-r' ;;
 *) sd=0 ; sortopt='' ;;
esac
# also ignore lower/uppercase
sortopt="$sortopt -f"

# get and sanitize values
in=`inptvar in '0-9a-zA-Z-'`
pg=`inptvar pg '.0-9a-zA-Z-'`
vw=`inptvar vw '0-9A-Za-z'`

### now the real work!

# get view/command, and process info / render page
vw=${vw:-default}
case $vw in

 page)
  fa=`inptvar fa '0-9a-z'`
# set pattern for hidden/active line filter
  case $fa in
  shown|1) fa=shown ; i='[+-]' ;;
  *) fa=hidden ; i='[+]' ;;
  esac
  header "$pg" "`pageinfo page $pg`" ""
  pagef="`pagefile page $pg`"
  if test -r "$pagef"
  then
# make header for user columns of page file
   tablehead "$pagef" $nopageindex
   getlines $i <"$pagef" | sort $sortopt -k $sc | { IFS="	" # TAB
    while read in f1 desc
# create link to edit view
    do
     if test $nopageindex = 1
# use first field as link text
     then cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$pg&in=$in&vw=editentry">$f1</a>(<a href="$myself?db=$db&pg=$pg&in=$in&vw=descindex">?</a>)</td>
EOH
# use index field, and also show first field
     else cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$pg&in=$in&vw=editentry">$in</a>(<a href="$myself?db=$db&pg=$pg&in=$in&vw=descindex">?</a>)</td>
<td>$f1</td>
EOH
     fi
# split remaining description into table fields
     echo "<td>$desc</td>" | sed -e 's:	:</td><td>:g'
     echo '</tr>'
    done
    }
   cat <<EOH
</table>
<p>for modification, select index name, or
<a href="$myself?db=$db&pg=$pg&in=&vw=editentry">create new entry</a></p>
<p><a href="$myself?db=$db&pg=$pg&vw=page&fa=hidden">hide</a> or
<a href="$myself?db=$db&pg=$pg&vw=page&fa=shown">show</a> hidden entries
(currently $fa)</p>
EOH
  else cat <<EOH
<p>Sorry, but page "$pg" with <b>file name "$pagef" cannot be read!</b></p>
EOH
  fi
  footer ;; # page.

 listpages)
  header "available pages" "List of Available Pages" "This is the list of all pages available for database <tt>$db</tt>."
  echo '<table><tr><th>name</th><th><i>description</i></th></tr>'
  getlines page <$cfg | { IFS="	" # TAB
   while read name file desc
   do cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$name&vw=page">$name</a></td>
<td><i>$desc</i></td></tr>
EOH
   done
   }
  echo '</table>'
  footer ;; # listpages.

 listindex) 
  header "index" "List of Index/Base Values" "This is the list of all index/base values available for database '<tt>$db</tt>'. Inactive/hidden indices are marked like <strike>this</strike>, active ones like <b>this</b>.<br />Select links in first column to edit."
# make header for all columns of index file
  tablehead "$idx" 0
# will be used by renderindices()
  maxindex=0
# active ones
  getlines '[+]' <"$idx" | sort $sortopt -k $sc | renderindices '<b>' '</b>'
# get counter value reported via tmpf
  maxindex=`head -n 1 $tmpf`
# hidden ones
  echo '<tr><td>---</td></tr>'
  getlines '[-]' <"$idx" | sort $sortopt -k $sc | renderindices '<strike>' '</strike>'
  maxindex=`head -n 1 $tmpf`
  cat <<EOH
</table>
 <p>create
 <a href="$myself?db=$db&pg=$pg&in=$maxindex&vw=editindex">new index entry</a>
</p>
EOH
  footer ;; # listindex.

 descindex)
  header "index/base $in" 'Index/base description' "Values associated with index <tt>$in</tt>"
  echo '<pre>'
  getlines '[+-]' <"$idx" | getlines $in
  echo '</pre>'
  cat <<EOH
<p><a href="$myself?db=$db&pg=$pg&in=$in&vw=editindex">EDIT</a></p>
EOH
  footer ;; # descindex.

 editindex)
  header "edit index" "Edit index/base fields" "Edit fields and SAVE.<br />Notes: first field (index) must be unique, will overwrite old entry if already present! To suppress listing of this index on record page, deselect SHOW."
  permwarn $permadmin
# get selected index (but only the first one)
  cat <<EOH
 <form enctype="application/x-www-form-urlencoded" method="post" action="$myself">
EOH
  tablehead "$idx" 0
# get number of rendered header fields
  totalcols=$?
  cat <<EOH
 <tr>
  <td><input type="text" name="in" value="$in" /></td>
EOH
  getlines '[+-]' <"$idx" | getlines $in | head -n 1 | sed -e 's:	:\
:g;s/"/\\"/g' | { fn=1 # index field already counts as 1
   while read field
   do cat <<EOH
  <td><input type="text" name="f$fn" value="$field"></td>
EOH
    fn=`expr $fn + 1`
   done
   while test $fn -lt $totalcols
   do cat <<EOH
  <td><input type="text" name="f$fn" value=""></td>
EOH
    fn=`expr $fn + 1`
   done
  }
  echo ' </tr>'
  tablefoot
  cat <<EOH
SHOW<input type="checkbox" name="fa" value="show" checked>
(also apply to all PAGES<input type="checkbox" name="pages" value="all">)
 <input type="hidden" name="db" value="$db">
 <input type="hidden" name="pg" value="$pg">
 <input type="hidden" name="vw" value="saveindex">
 <input type="submit" name="submit" value="SAVE">
 </form>
EOH
  footer ;; # editindex.

 saveindex)
  header "saveindex" "Saving index entry" "Attempting to save index $in ..."
  inlock="`lockfile \"$idx\"`"
  if test "$inlock" = "" -o ! -w "$idx"
  then cat <<EOH
<p><em>FAILED</em> due to locked or unwritable file <tt>$idx</tt>!
<br />Depending on your browser, it may be possible to recover your entries by selecting "Back".
</p>
EOH
  elif test "$in" = ""
  then echo '<p><em>FAILED</em> due to empty index field!</p>'
  else
   tablehead "$idx" 0
   totalcols=$?
# copy everything not containing selected index (SPC&TAB in patterns)
   grep -v "^[+-][ 	]$in" <"$idx" >$tmpf
# show/hide?
   if test "`inptvar fa`" = "show"
   then newline="+	$in"
   else newline="-	$in"
   fi
# add new/modified fields to initial flag and index name
   i=1
   while test $i -lt $totalcols
   do
    nf="`inptvar f$i \"$fieldchars\"`"
# separate fields by TAB, replace empty fields by SPC
    newline="$newline	${nf:- }"
    i=`expr $i + 1`
   done
   echo "$newline" >>$tmpf
# report new/modified entry
   echo '<tr><td>'
# replace first TAB by SPC; sed commands are 's:TAB:SPC:;s:TAB:...'
   tail -n 1 $tmpf | sed -e 's:	: :;s:	:</td><td>:g'
   echo '</tr></td>'
   tablefoot
   if test $perms -ge $permadmin
   then
# save updated index file
    cat $tmpf > "$idx"
    dobackup "$idx" "saveindex for $in"
    cat <<EOH
<p><a href="$myself?db=$db&pg=$pg&vw=listindex&sc=1&sd=1">DONE!</a>
(+ indicates shown entry, - hidden entry)</p>
EOH
    if test "`inptvar pages`" = "all"
# apply hide/show to all pages
    then
     if test "`inptvar fa`" = "show"
     then
      echo '<hr /><p>also applying SHOW'
      flg='+'
     else
      echo '<hr /><p>also applying HIDE'
      flg='-'
     fi
     echo 'to all related page entries:</p><ul>'
# get all pages for the current database
     getlines page <$cfg | { while read pname _
     do
      pagef="`pagefile page $pname`"
      plock="`lockfile \"$pagef\"`"
      if test "$plock" != "" -a -r "$pagef" -a -w "$pagef"
      then cat <<EOH
<li><tt>$pname</tt></li>
EOH
# copy everything not containing selected index (SPC&TAB in patterns)
       grep -v "^[+-][ 	]$in" <"$pagef" >$tmpf
# replace flag for selected index
       grep "^[+-][ 	]$in" <"$pagef" | sed -e "s/.	/$flg	/" >>$tmpf
       cat $tmpf >"$pagef"
       dobackup "$pagef" "saveindex for $in on page $pname"
      else cat <<EOH
<li>FAILED for pagefile <tt>$pagef</tt> of page <tt>$pname</tt></li>
EOH
      fi
      releasefile "$plock"
     done
     echo '</ul>'
     }
    fi # apply to all pages.
   else cat <<EOH
<p>FAILED due to bad permissions $perms &lt; $permadmin</p>
EOH
   fi
  fi
  releasefile "$inlock"
  footer ;; # saveindex.

 editentry)
  header 'edit entry' "Edit entry for page <tt>$pg</tt>" "Edit fields and SAVE, uncheck SHOW to hide entry"
  permwarn $permeditor
  maxflength=`getlines maxlength <$cfg | head -n 1`
  maxflength=${maxflength:-199}
  pagef="`pagefile page $pg`"
  if test -r "$pagef"
  then
   cat <<EOH
 <form enctype="application/x-www-form-urlencoded" method="post" action="$myself">
EOH
# make header for user columns of page file, with all columns
   tablehead "$pagef" 0
# get number of rendered header fields
   totalcols=$?
# delete link
   cat <<EOH
 <tr><td><select name="in">
EOH
# get all possible index names, only uniques
  getlines '[+]' <"$idx" | sed -e 's/	.*//' | sort -u | {
   while read nin
   do if test "$nin" = "$in"
    then cat <<EOH
  <option value="$nin" selected>$nin #</option>
EOH
    else cat <<EOH
  <option value="$nin">$nin</option>
EOH
    fi
   done
  }
  cat <<EOH
 </select></td>
EOH
# read record fields of current index, split onto separate lines
   getlines '[+-]' <"$pagef" | getlines $in | head -n 1 | sed -e 's:	:\
:g;s/"/\\"/g' | {
    fn=1
    af=autofocus # for first field
    while read field
# populate fields with current values
    do cat <<EOH
  <td>
   <input type="text" name="f$fn" value="$field" maxlength="$maxflength" $af>
  </td>
EOH
     fn=`expr $fn + 1`
     af=''
    done
# add empty fields, if less present than in header line
    while test $fn -lt $totalcols
    do cat <<EOH
  <td><input type="text" name="f$fn" value=""></td>
EOH
     fn=`expr $fn + 1`
    done
   }
   echo ' </tr>'
   tablefoot
   cat <<EOH
 <input type="hidden" name="db" value="$db">
 <input type="hidden" name="pg" value="$pg">
 <input type="hidden" name="vw" value="saveentry">
 <input type="checkbox" name="fa" value="show" checked>SHOW
 <input type="submit" name="submit" value="SAVE">
 </form>
EOH
  else cat <<EOH
<p>Sorry, but page "$pg" with <b>file name "$pagef" cannot be read!</b></p>
EOH
  fi
  footer ;; # editentry.

 saveentry)
  header "saveentry" "Saving page entry" "Attempting to save entry for $in on page $pg ..."
  pagef="`pagefile page $pg`"
  inlock="`lockfile \"$pagef\"`"
  if test "$inlock" = "" -o ! -r "$pagef" -o ! -f "$pagef"
  then cat <<EOH
<p><em>FAILED</em> due to locked/unreadable/unwritable page file <tt>$page</tt>!
<br />Depending on your browser, it may be possible to recover your entries by selecting "Back".
</p>
EOH
  elif test "$in" = ""
  then echo '<p><em>FAILED</em> due to empty index field!</p>'
  else
  tablehead "$pagef" 0
  totalcols=$?
# copy everything not containing selected index (SPC&TAB in patterns)
   grep -v "^[+-][ 	]$in" <"$pagef" >$tmpf
# show/hide?
   if test "`inptvar fa`" = "show"
   then newline="+	$in"
   else newline="-	$in"
   fi
# add new/modified fields to initial flag and index name
   i=1
   while test $i -lt $totalcols
   do
# separate fields by TAB, replace empty fields by SPC
    nf="`inptvar f$i \"$fieldchars\"`"
    newline="$newline	${nf:- }"
    i=`expr $i + 1`
   done
   echo "$newline" >>$tmpf
# report last line, i.e saved entry
   echo '<tr><td>'
# replace first TAB by SPC; sed commands are 's:TAB:SPC:;s:TAB:...'
   tail -n 1 $tmpf | sed -e 's:	: :;s:	:</td><td>:g'
   echo '</tr></td>'
   tablefoot
   if test $perms -ge $permeditor
# save updated page file
   then
    cat $tmpf > "$pagef"
    dobackup "$pagef" "saveentry for $in"
    cat <<EOH
<p><a href="$myself?db=$db&pg=$pg&vw=page&sc=1&sd=1">DONE!</a>
(+ indicates shown entry, - hidden entry)</p>
EOH
   else cat <<EOH
<p>FAILED due to bad permissions $perms &lt; $permeditor</p>
EOH
   fi
  fi
  releasefile "$inlock"
  footer ;; # saveentry.

 *) # default
  header "$myself" "$myself $db" ""
  footer ;;
esac

# cleanup and quit
finish
