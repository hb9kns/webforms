#!/bin/sh
# CGI script for handling flat file databases with common index/base
info='webforms.cgi // 2019-12-16 Y.Bonetti // http://gitlab.com/yargo/webforms'

# set root for temporary files
# (make sure this is a pattern only for temporary files, because
# there is an 'rm -f $tmpr*' command at the end of the script!)
# if `$TMPDIR` contains whitespace or other crap, anything might happen!
tmpr=${TMPDIR:-/tmp}/webform-$user-tmp$$

# set to yes for activating xlist= feature -- Caution: might be dangerous!
xlists=no

# generate string for time stamp, suitable as index
nowstring=`date '+%y-%m-%d,%H:%M'`
# same, but as epoch minutes
nowminutes=$(( `date -u +%s`/60 ))
# for daystamps
today=`date '+%Y-%m-%d'`

# save new version of database; arg.1 = modified file, arg.2 = remarks
# (user name and REMOTE_ADDR will be added to the remarks)
dobackup(){
 dmesg="$2 (user=$usr, remote=$REMOTE_ADDR)"
# comment/uncomment below as desired! commenting out all is also possible
# (git version:)
# git add "$1" && git commit -m "$dmesg"
# (rcs version:)
# ci -l -w"$usr" -m"$dmesg" "$1"
# (poor man's version -- if commenting, do all lines of HERE/<<EOH document!)
 cat <<EOH >>"$1.diff"

## $nowstring : $dmesg
EOH
# ed-like inverse (new to old) diff: short, and can be more easily replayed
 diff -e "$1" "$1.old" >>"$1.diff"
 cat "$1" > "$1.old"
# make sure backup files cannot be read by others/all
 chmod o-rwx "$1.old" "$1.diff"
}

# default permitted characters in record fields: SPC and printable ASCII
# will be used as 'tr' pattern
defaultfieldchars=' -~'

# default help file (may also be nonexistent, then ignored)
defhelp="./help.html"

stylefile="./style.css"
iconfile="./favicon.ico"

# # # ONLY CHANGE BELOW IF YOU KNOW WHAT YOU ARE DOING! # # #

REQUEST_METHOD=`echo $REQUEST_METHOD | tr a-z A-Z`
if test "$REQUEST_METHOD" != "POST" -a "$REQUEST_METHOD" != "GET"
then cat <<EOT

$info

This is a CGI script, expecting input from POST or GET requests.
See accompanying README file, or online repository for further information.

EOT
exit 9
fi

myself=`basename "$0"`
mydir=`dirname "$0"`

# temp files for input
tmpf=$tmpr.tmp
inpt=$tmpr.inp
# and showindex filtered index
tmpi=$tmpr.idx

# slurp stdin and QUERY_STRING
cat >$tmpf
echo "$QUERY_STRING" >>$tmpf

# save slurped input in decoded form:
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

# # first define some functions

# end script after cleanup with exit code as arg.1
finish(){
/bin/rm -f ${tmpr}*
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

# # # NB: a lot of sed and grep patterns contain TAB and SPC characters!

# get lines beginning with a value, and remove that column,
#  after deleting all comment lines (#)
# note TAB in sed and grep pattern: make sure there is a TAB,
#  and that the value is complete
getlines(){
# record separator TAB only
 sed -e '/^#/d;s/$/	/' | grep "^$1[	]" | { IFS="	"
 while read _ values
# remove trailing added TAB
 do echo "${values%	}"
 done
 }
}

# check whether entry arg.2 is present on some line beginning with arg.1
checkline(){
local entry found
entry="$2"
found=0
# read lines, surround with TAB (also in sed pattern), and check if somewhere
getlines "$1" | sed -e 's/^/	/;s/$/	/' |
 grep "	$entry	" 2>&1 >/dev/null
}

# display header, arg.1 = page title, arg.2 = main title, arg.3 = description
header(){
cat <<EOH
Content-type: text/html

<html><head><title>$1</title>
<META HTTP-EQUIV="Pragma" CONTENT="no-cache">
<META HTTP-EQUIV="Expires" CONTENT="-1">
EOH
if test -r "$stylefile"
then cat <<EOH
<link rel="stylesheet" type="text/css" href="$stylefile">
EOH
fi
if test -r "$iconfile"
then cat <<EOH
<link rel="shortcut icon" href="$iconfile">
EOH
fi
cat <<EOH
</head>
<body>
<p align="right">
<tt>`date '+%a %Y-%m-%d %H:%M'` // db=$db // $usr($perms)</tt>
EOH
if test "$helpfile" != ""
then cat <<EOH
:: <a href="$helpfile">Help</a>
EOH
fi
echo '</p><p>'
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
# uncomment during maintenance
# echo '<p><center><font color="red"><h1>MAINTENANCE, DO NOT USE!</h1></font></center></p>'
echo "<p>$3</p>"
}

# display footer with some additional info
footer(){
cat <<EOH
<hr />
<p><small><i>
$info<br />
running on <tt>`hostname`</tt>
 (`w|head -n 1`)
</i></small></p>
<pre>
EOH
# uncomment for debugging
# cat $inpt
cat <<EOH
</pre>
</body>
<!-- some clients seem to prefer getting pragmas at the end -->
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
 local pf
# get file name
 getlines "$1" <"$cfg" | getlines $2 | { IFS="	"
  read pf _
# sanitize
  pf=`echo $pf | tr -c -d '0-9.A-Za-z_/-'`
# don't change, if it starts with '/' or '.' or is empty (i.e nothing found)
# else prepend webform root directory
  case $pf in
   /*) echo "$pf" ;;
   .*) echo "$pf" ;;
   ?*) echo "$wdir/$pf"
  esac
 }
}

# get page info for arg.1=type, arg.2=page
pageinfo(){
 getlines $1 <"$cfg" | getlines $2 | { IFS="	"
  read _ pinfo
  echo "$pinfo"
 }
}

# print HTML table head for arg.1=file, arg.2=start column,
#  if arg.3=showindex then also field names from config var 'showindex'
# exit code = number of rendered columns
# sc and sd are global variables!
tablehead(){
 local skip nc nd idxf ffn
 skip=${2:-0}
 sc=${sc:-1}
 sd=${sd:-0}
 nc=1
# empty file used for reporting to caller
 : >$tmpf
 if test "$3" = "showindex"
# remove skipped fields consisting only of '-',
# append TAB to end of list for later separation
 then idxf=`echo "$showindex	" | sed -e 's/-	//g;s/	/*	/g'`
 else idxf=''
 fi
 echo '<table><tr>'
# get first line beginning with '*' ('[*]' for grep pattern),
# and inject $idxf after index (note TABs in sed patterns),
# and convert into list with each field on a separate line for `while read`
 getlines '[*]' <"$1" | head -n 1 | sed -e "s|	|	$idxf|" -e 's/	/\
/g' | { while read field
  do
# for column selected for sorting, invert next sort order
   if test $nc = $sc
   then nd=$(( 1-$sd ))
   else nd=$sd
   fi
# now render column titles with sort links:
# skip start columns
   if test $skip -gt 0
   then skip=$(( $skip-1 ))
# report field numbers and names to caller
   else echo $nc:$field >>$tmpf
# if list field, get file name for list file,
    case $field in
     list=*|xlist=*) ffn="`pagefile list ${field#*=}`"
# and use entry in first line beginning with '*'
      field="`cat "$ffn" | getlines '[*]' | sed -e 's/	.*//' | head -n 1`"
      ;;
# display description only in case of time-based entries
# ("now*=" to permit delta time values like "now,5,10=")
     now*=*|day=*) field=${field##*=} ;;
    esac
    cat <<EOH
<th><a href="$myself?db=$db&pg=$pg&vw=$vw&sc=$nc&sd=$nd&fa=$fa">$field</a></th>
EOH
   fi
   nc=$(( $nc+1 ))
  done
 }
 echo '</tr>'
# return number of last field
 return `tail -n 1 $tmpf | sed -e 's/:.*//'`
}

# generate table body from stdin for item/page entry, using $totalcols and
# header list in $tmpf reported by 'tablehead', arg.1 = start column
tableentry(){
 local en fn ffn af
 fn=${1:-1}
# form entry number
 en=$(( $fn-1 ))
 af=autofocus # for first field
# loop for all necessary input fields
 while test $fn -le $totalcols
 do read field
  echo '  <td>'
# get field name as reported by 'tablehead'
  ffn=`grep "^$fn:" $tmpf`
# and check after removal of characters up to first ':'
  case ${ffn#*:} in
# if field name is reference to list file ..
# start selection field
  list=*|xlist=*) cat <<EOH
  <select name="f$en">
EOH
# get contents of file with name from field where all up to '=' is removed,
# only using lines beginning with '+'
    cat "`pagefile list ${ffn#*=}`" | getlines '[+]' | { IFS="	"
    while read itm maxnum xpr
# and generate options from file contents
# (sanitizing of file contents not necessary, as done when entry is saved)
# possibly preselecting option already present in database
    do
# if expression is non-empty and xlist permitted
     if test "$xpr" != "" -a $xlists = yes
     then case ${ffn#*:} in
# and xlist, then evaluate value
      xlist=*) itm=`eval echo $xpr` ;;
# else just copy expression (unsatisfying but best solution)
      *) itm="$xpr" ;;
      esac
     fi
# if there is a limit for this option
# ('=' or '-' count as no limit, to be used in case of expression)
     if test "$maxnum" != "" -a "$maxnum" != "=" -a "$maxnum" != "-"
     then
# get all other active entries of this field, filter for this option, and count
      if test `grepothers "$in" <"$pagef" | getlines '[+]' | cut -f $fn | grep "$itm" | wc -l` -ge $maxnum
# if maximum reached, generate unavailable entry
      then itm=$itm:UNAVAILABLE/FULL
      fi
     fi
# preselect former value
     if test "$itm" = "$field"
     then cat <<EOF
   <option value="$itm" selected>$itm</option>
EOF
     else cat <<EOF
   <option value="$itm">$itm</option>
EOF
     fi
    done
# end of selection field
   echo '   </select>'
   }
   ;;
  now*=*)
# offer empty/block/old/current/delta daytime value
# (use epoch minutes internally, but remove for selection tag)
   cat <<EOH
  <select name="f$en">
   <option value="">[empty]</option>
   <option value="--">--</option>
   <option value="$field" selected>${field%=*}</option>
   <option value="$nowstring=$nowminutes">$nowstring</option>
EOH
# get delta time values if present, only numbers, separated by spaces, set as arguments
   set -- `echo ${ffn#*:now} | sed -e 's/=.*//;' | tr -c '0-9' ' '`
   while test $# -gt 0
   do cat <<EOD
   <option value="$nowstring+${1}min=$(( $nowminutes+$1 ))">$nowstring +$1 min</option>
EOD
    shift
   done
   cat <<EOH
  </select>
EOH
   ;;
  day=*)
# offer empty/block/old/current date value
   cat <<EOH
  <select name="f$en">
   <option value="">[empty]</option>
   <option value="--">--</option>
   <option value="$field" selected>${field%=*}</option>
   <option value="$today">$today</option>
  </select>
EOH
   ;;
# .. else populate with current values (or empty, if nothing read)
  *) cat <<EOH
 <input type="text" name="f$en" value="$field" maxlength="$maxflength" $af />
EOH
   ;;
  esac
  echo '  </td>'
  en=$(( $en+1 ))
  fn=$(( $fn+1 ))
  af=''
 done
}

tablefoot(){ echo '</table>' ; }

# attempt to get a lockfile (arg.1)
lockfile(){
 local lf lc lt
 lc=9 # timeout counter
# delay, somewhat random per instance
 lt=$(( $$%3+1 ))
 lf="$1.lock"
# while file already present, and not yet timeout
 while test -f "$lf" -a $lc -gt 0
 do lc=$(( $lc-1 ))
  sleep $lt
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

# sort according to field defined by $sc and $sd
# with separator TAB, ignore case and nonprintable characters
fieldsort(){
 sort -t '	' -f -i -k $sc $sortopt
}

# grep for other indices, with additional trailing TAB, removed afterwards
grepothers(){
 sed -e 's/$/	/' | grep -v "^[+-][	]$1[	]" | sed -e 's/	$//'
}

# function for displaying index entries
# maxindex must be initialised globally, as well as CGI variables db and pg
# arg.1,2 = additional tags for each index entry
renderindices(){
 local pastind i ofs
 ofs="$IFS"
 IFS="	"
 i=${maxindex:-1}
 while read in desc
# use index for link to edit view, marked with tags
 do cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$pg&in=$in&vw=editindex">$1$in$2</a></td>
EOH
# split description into table fields
  echo "<td>$desc</td>" | sed -e 's:	:</td><td>:g'
  echo '</tr>'
# create temporary last index containing nothing but numbers
  pastind=`echo "$in" | tr -c -d '0-9'`
# if same as original, convert to numeric value and increment,
  if test "$pastind" = "$in"
  then pastind=$(( $in+1 ))
# ignore otherwise
  else pastind=''
  fi
# and set to counter value, if non-numeric
  pastind=${pastind:-$i}
  if test $maxindex -lt $pastind
  then maxindex=$pastind
  fi
  i=$(( $i+1 ))
 done
# report outside
 echo $maxindex >$tmpf
 IFS="$ofs"
}

# functions for sed pattern generation for showindex handling
# (TABs in IFS and [^..])

# search pattern: subpatterns for non-skip fields
showindexsrch(){
 local out
 out=''
 while test "$1" != ""
 do case $1 in
  -) out="$out	[^	][^	]*" ;;
  *) out="$out	\\([^	][^	]*\\)" ;;
  esac
  shift
 done
# add wildcard to consume/delete all remaining fields
 echo "$out.*"
}

# replace pattern: delete skip fields, replace non-skips with references
showindexrepl(){
 local out cnt
 out=''
 cnt=1
 while test "$1" != ""
 do case $1 in
  -) : ;; # NO-OP
  *) out="$out	:$cnt"
     cnt=$(( $cnt+1 ))
   ;;
  esac
  shift
 done
# replace ':' with '\', note TABs in patterns!
# (cannot put '\' directly further above due to shell expansion for "$out")
 echo "$out" | sed -e 's/	:/	\\/g'
}

# # now preparations for the main script!

# set root for configuration files / working directory
# (this could be set to some hardcoded directory for improved security)
wdir=${WEBFORMSDIR:-$mydir}
# default/fallback
defcfg=default

# define config file name
db=`inptvar db '.0-9A-Za-z_-'`
cfg="$wdir/${db:-$defcfg}.cfg"
if test ! -r "$cfg"
then fatal "configuration file $cfg not readable"
# this should never be reached, but just to be sure:
 exit 9
fi

# if maintenance entry is active, print message and abort execution
maintuntil=`getlines maintenance <"$cfg"`
if test "$maintuntil" != ""
then
 header MAINTENANCE 'database not available' "under maintenance, probably until $maintuntil"
 echo '<p><em>You may try to reload the page, when the database is available again.<em></p>'
 footer
 finish 0
fi

# define index/base file name
idx=`pagefile base file <"$cfg"`
if test ! -r "$idx"
then fatal "index/base file $idx not readable"
 exit 9
fi

permadmin=100
permeditor=10
permvisitor=1
# establish permissions (the higher, the better)
# admin and editor can have '*' entries, granting permissions to *any user*
perms=0
# sanitize to be sure (we prefer script failure to possible security risk)
usr=`echo ${REMOTE_USER:-nobody}|tr -c -d '0-9A-Za-z.-'`
if checkline admin "$usr" <"$cfg" || checkline admin '\*' <"$cfg"
then perms=$permadmin
else
 if checkline editor "$usr" <"$cfg" || checkline editor '\*' <"$cfg"
 then perms=$permeditor
 else
# if "visitor" entries exist, user must be explicitly allowed
  if grep "^visitor" "$cfg" 2>&1 >/dev/null
  then
   if checkline visitor "$usr" <"$cfg"
   then perms=$permvisitor
   else perms=0
   fi
# otherwise all unknown users are visitors
  else perms=$permvisitor
# visitor:
  fi
# editor:
 fi
# admin:
fi

# define link field for page view
nopageindex=0
# set to first record field, if nopageindex present with any value
if checkline nopageindex '.*' <"$cfg"
then nopageindex=1
fi
# reset to index field, if false or 0
if checkline nopageindex false <"$cfg"
then nopageindex=0
fi
if checkline nopageindex 0 <"$cfg"
then nopageindex=0
fi

# define warning for empty fields
emptywarn=`getlines emptywarn <"$cfg" | head -n 1`
emptywarn=${emptywarn:-' '}

# define helpfile
helpfile="`pagefile help file <"$cfg" | head -n 1`"
# if undefined, use default
if test "$helpfile" = ""
then helpfile="$defhelp"
fi

# define logfile
logfile="`pagefile log file <"$cfg" | head -n 1`"
# if unwritable, simply ignore
if test ! -w "$logfile"
then logfile=/dev/null
fi

# define permitted characters for record fields
fieldchars=`getlines fieldchars <"$cfg" | head -n 1`
fieldchars="${fieldchars:-$defaultfieldchars}"
# get additional index fields to be shown in page view
# get arguments after "showindex" config var, only first line,
showindex=`getlines showindex <"$cfg" | head -n 1`

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

# get and sanitize values
in=`inptvar in '0-9a-zA-Z_-'`
pg=`inptvar pg '.0-9a-zA-Z-'`
vw=`inptvar vw '0-9A-Za-z'`

# if page is missing, force listpages instead of page view
if test "$pg" = "" -a "$vw" = "page"
then vw=listpages
fi

# # now the real work!

# additional filter depending on REMOTE_USER normally inactive (pass all)
usrfilter='.*'
ptype=nil

# get page file name, and set ptype flag for later
for pft in page upag ulog
do pagef="`pagefile $pft $pg`"
 if test -r "$pagef"
 then ptype=$pft
  break
 fi
done

# for user type pages and non-admins, only allow user name from environment
case $ptype in
upag|ulog)
 if test $perms -lt $permadmin
 then usrfilter="$usr"
 fi
 ;;
esac

# get view/command, and process info / render page
vw=${vw:-default}
cat <<EOH >>"$logfile"
`date -u +%y-%m-%d,%H:%M:%S` db=$db vw=$vw pg=$pg in=$in usr=$usr/$perms remote=$REMOTE_ADDR:$REMOTE_PORT # $REMOTE_HOST
EOH
case $vw in

 page)
  fa=`inptvar fa '0-9a-z'`
# set pattern for hidden/active line filter
  case $fa in
  hidden) fa=hidden ; i='[-]' ;;
  all) fa=all ; i='[+-]' ;;
  *) fa=shown ; i='[+]' ;;
  esac
  if test -r "$pagef"
  then
   case $ptype in
   page|ulog) header "$pg" "`pageinfo $ptype $pg`" ""
# display all entries in case of page and ulog pages
    usrfilter='.*' ;;
   upag) header "$pg" "`pageinfo $ptype $pg`" "<em>user filtered</em>" ;;
   *) header "ERROR" "unknown pagetype" "internal error"
    fatal "cannot handle pagetype $ptype!" ;;
   esac
   cat <<EOH
<p>select index name to modify entry, or
<a href="$myself?db=$db&pg=$pg&in=&vw=editentry">create new entry</a></p>
EOH
# make header for user columns of page file,
# possibly adding showindex fields
   if test "$showindex" = ""
   then tablehead "$pagef" $nopageindex
   else tablehead "$pagef" $nopageindex showindex
# create sed patterns for showindex
    sis=`IFS="	";showindexsrch $showindex`
    sir=`IFS="	";showindexrepl $showindex`
# generate showindex filtered index list
    getlines '[+-]' <"$idx" | sed -e "s/$sis/$sir/" >$tmpi
   fi
# get lines with appropriate flag and apply user-dependant filter
   getlines $i <"$pagef" | grep "^$usrfilter" | {
    if test "$showindex" = ""
# if no showindex, just copy everything
    then cat
    else IFS="	"
     while read in rem
# else insert showindex fields after index
     do ins=`getlines "$in" <$tmpi | head -n 1`
      echo "$in	$ins	$rem"
     done
    fi
# sort
   } | fieldsort | { IFS="	"
    count=0
    while read in f1 desc
# create link to edit view
    do
     count=$(( $count+1 ))
# link to user (without timestamp) for ulog page
     case $ptype in
     ulog) din="${in%_*}" ;;
     *) din="$in" ;;
     esac
     if test $nopageindex = 1
# use first field as link text
     then cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$pg&in=$in&vw=editentry">$f1</a>(<a href="$myself?db=$db&pg=$pg&in=$din&vw=descindex">?</a>)</td>
EOH
# use index field, and also show first field (possibly with warning)
     else sed -e "s|<td> *</td>|<td>$emptywarn</td>|g" <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$pg&in=$in&vw=editentry">$in</a>(<a href="$myself?db=$db&pg=$pg&in=$din&vw=descindex">?</a>)</td>
<td>$f1</td>
EOH
     fi
# split remaining description into table fields, add warnings
     echo "<td>$desc</td>" | sed -e 's|	|</td><td>|g' |
      sed -e "s|<td> *</td>|<td>$emptywarn</td>|g"
     echo '</tr>'
    done
    echo '</table>'
    cat <<EOH
<p><i>display <a href="$myself?db=$db&pg=$pg&vw=page&fa=all">all</a> or only
<a href="$myself?db=$db&pg=$pg&vw=page&fa=shown">shown</a> or only
<a href="$myself?db=$db&pg=$pg&vw=page&fa=hidden">hidden</a> entries,
currently $fa $count</i></p>
EOH
    }
  else
   header "$pg" "`pageinfo $ptype $pg`" "<em>ERROR</em>"
   cat <<EOH
<p>Sorry, but page "$pg" of type "$ptype" with <b>file name "$pagef" cannot be read!</b></p>
EOH
  fi
  footer ;;
# page.

 listpages)
  header "available pages" "List of Available Pages" "This is the list of all pages available for database <tt>$db</tt>."
  echo '<table><tr><th>name</th><th><i>description</i></th></tr>'
  getlines 'page\|upag\|ulog' <"$cfg" | { IFS="	"
   while read name file desc
   do cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$name&vw=page">$name</a></td>
<td><i>$desc</i></td></tr>
EOH
   done
   }
  echo '</table>'
  footer ;;
# listpages.

 listindex) 
  header "index" "List of Index/Base Values" "This is the list of all index/base values available for database '<tt>$db</tt>'. Inactive/hidden indices are marked like <strike>this</strike>, active ones like <b>this</b>.<br />Select links in first column to edit."
# make header for all columns of index file
  tablehead "$idx" 0
# will be used by renderindices()
  maxindex=1
# active ones
  getlines '[+]' <"$idx" | fieldsort | renderindices '<b>' '</b>'
# get counter value reported via tmpf
  maxindex=`head -n 1 $tmpf`
# hidden ones
  echo '<tr><td>---</td></tr>'
  getlines '[-]' <"$idx" | fieldsort | renderindices '<strike>' '</strike>'
  maxindex=`head -n 1 $tmpf`
  maxindex=${maxindex:-0}
  cat <<EOH
</table>
<p>create
 <a href="$myself?db=$db&pg=$pg&in=$maxindex&vw=editindex">new index entry</a>
</p>
EOH
  footer ;;
# listindex.

 descindex)
  header "index/base $in" 'Index/base description' "Values associated with index <tt>$in</tt>"
  echo '<pre>'
  getlines '[+-]' <"$idx" | getlines "$in"
  echo '</pre>'
  cat <<EOH
<p><a href="$myself?db=$db&pg=$pg&in=$in&vw=editindex">EDIT</a></p>
EOH
  footer ;;
# descindex.

 editindex)
  header "edit index" "Edit index/base fields" "Edit fields and SAVE.<br />Notes: first field (index) must be unique, will overwrite old entry if already present! To suppress listing of this index on record page, deselect SHOW."
  permwarn $permadmin
  cat <<EOH
 <form enctype="application/x-www-form-urlencoded" method="post" action="$myself">
EOH
  tablehead "$idx" 0
# get number of rendered header fields reported by 'tablehead'
  totalcols=$?
  cat <<EOH
 <tr>
  <td><input type="text" name="in" value="$in" maxlength="$maxflength" /></td>
EOH
# get selected index (but only the first one) and add entry line,
# starting at field 2 (after index)
  getlines '[+-]' <"$idx" | getlines "$in" | head -n 1 | sed -e 's:	:\
:g;s/"/\\"/g' | tableentry 2
  echo ' </tr>'
  tablefoot
  cat <<EOH
SHOW<input type="checkbox" name="fa" value="show" checked />
(also apply to all PAGES<input type="checkbox" name="pages" value="all">)
 <input type="hidden" name="db" value="$db" />
 <input type="hidden" name="pg" value="$pg" />
 <input type="hidden" name="vw" value="saveindex" />
 <input type="submit" name="submit" value="SAVE" />
 </form>
EOH
  footer ;;
# editindex.

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
# copy everything not containing selected index
   grepothers "$in" <"$idx" >$tmpf
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
    i=$(( $i+1 ))
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
     getlines page <"$cfg" | { while read pname _
     do
      pagef="`pagefile 'page\\|upag\\|ulog' $pname`"
      plock="`lockfile \"$pagef\"`"
      if test "$plock" != "" -a -r "$pagef" -a -w "$pagef"
      then cat <<EOH
<li><tt>$pname</tt></li>
EOH
# copy everything not containing selected index
       grepothers "$in" <"$pagef" >$tmpf
# replace flag for selected index, with limiting TAB added/removed
       sed -e 's/$/	/' <"$pagef" | grep "^[+-][ 	]$in	" |
        sed -e "s|.	|$flg	|;s|	$||" >>$tmpf
       cat $tmpf >"$pagef"
       dobackup "$pagef" "set index for $in on $pname"
      else cat <<EOH
<li>FAILED for pagefile <tt>$pagef</tt> of page <tt>$pname</tt></li>
EOH
      fi
      releasefile "$plock"
     done
     echo '</ul>'
     }
    fi
# (apply to all pages.)
   else cat <<EOH
<p>FAILED due to bad permissions $perms &lt; $permadmin</p>
EOH
   fi
  fi
  releasefile "$inlock"
  footer ;;
# saveindex.

 editentry)
  header 'edit entry' "Edit entry for page <tt>$pg</tt>" "Edit fields and SAVE, uncheck SHOW to hide entry"
  permwarn $permeditor
  maxflength=`getlines maxlength <"$cfg" | head -n 1`
  maxflength=${maxflength:-999}
# make sure in case of user/ulog pages, only permitted user name is passed
  if test "$usrfilter" != '.*'
  then case $ptype in
   upag) in="$usr" ;;
# for ulog page, keep time stamp if present
   ulog) if test "$in" = ""
    then in=$usr
    else in="${usr}_${in#*_}"
    fi ;;
   esac
  fi
  if test -r "$pagef"
  then
   cat <<EOH
 <form enctype="application/x-www-form-urlencoded" method="post" action="$myself">
EOH
# make header for user columns of page file, with all columns
   tablehead "$pagef" 0
# get number of rendered header fields reported by 'tablehead'
   totalcols=$?
   case $ptype in
   page)
# in case of normal page
# add empty option value (to fail if nothing selected)
   cat <<EOH
 <tr><td><select name="in"><option value=""> </option>
EOH
# get all possible index entries, get two fields and some more info,
# sort, and only uniques
# (replace all TABs with ' | ', and add some more chars after 2nd)
   getlines '[+]' <"$idx" |
    sed -e 's/	/|/;s/	\(.\{1,9\}\).*/|\1../;s/[|	]/ | /g' |
    sort -u | {
# read index and additional remarks
    while read nin rem
    do if test "$nin" = "$in"
# mark&select already present value
     then cat <<EOH
  <option value="$nin" selected>$nin $rem ###</option>
EOH
     else cat <<EOH
  <option value="$nin">$nin $rem</option>
EOH
     fi
    done
   }
   cat <<EOH
 </select></td>
EOH
   ;;
   upag)
# in case of user page
    cat <<EOH
 <tr><td>
 <input type="text" name="in" value="$in" maxlength="$maxflength" $af />
 </td>
EOH
   ;;
   ulog)
# in case of ulog page, add number-only timestamp if missing
    if test "$in" = "" -o "$in" = "$usr"
    then in="${usr}_`echo $nowstring|tr -c -d '0-9'`"
    fi
    cat <<EOH
 <tr><td>
 <input type="text" name="in" value="$in" maxlength="$maxflength" $af />
 </td>
EOH
   ;;
   esac
# read record fields of current index, split onto separate lines, and
# generate table entry, starting at field 2 (after index)
   getlines '[+-]' <"$pagef" | getlines "$in" | head -n 1 | sed -e 's:	:\
:g;s/"/\\"/g' | tableentry 2
   echo ' </tr>'
   tablefoot
   cat <<EOH
 <input type="hidden" name="db" value="$db" />
 <input type="hidden" name="pg" value="$pg" />
 <input type="hidden" name="vw" value="saveentry" />
 <input type="checkbox" name="fa" value="show" checked />SHOW
 <input type="submit" name="submit" value="SAVE" />
 </form>
EOH
  else cat <<EOH
<p>Sorry, but page "$pg" with <b>file name "$pagef" cannot be read!</b></p>
EOH
  fi
  footer ;;
# editentry.

 saveentry)
  header 'save entry' "Saving page entry" "Attempting to save entry for index '$in' on page $pg ..."
# make sure in case of user/ulog pages, only permitted user name is passed
  if test "$usrfilter" != '.*'
  then case $ptype in
   upag) in="$usr" ;;
# for ulog page, keep time stamp if present
   ulog) in="${usr}_${in#*_}" ;;
   esac
  fi
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
# copy everything not containing selected index
   grepothers "$in" <"$pagef" >$tmpf
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
    i=$(( $i+1 ))
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
    cat <<EOH
<p><i>comparison between former (&lt;) and updated (&gt;) database:</i></p>
<pre>`diff "$pagef" $tmpf | grep '^[<>]'`</pre>
EOH
    cat $tmpf > "$pagef"
    dobackup "$pagef" "saveentry for $in on $pg"
    cat <<EOH
<p>OK, done! (+ indicates shown entry, - hidden entry)</p>
<p>Now you can
 <a href="$myself?db=$db&pg=$pg&in=$in&vw=editentry">edit again</a>
this entry, or
 <a href="$myself?db=$db&pg=$pg&vw=page&sc=1&sd=1">display the page</a>
with the modified entry.</p>
EOH
   else cat <<EOH
<p>FAILED due to bad permissions $perms &lt; $permeditor</p>
EOH
   fi
  fi
  releasefile "$inlock"
  footer ;;
# saveentry.

 *)
# default
  header "$myself" "$myself $db" ""
  footer ;;
esac

# cleanup and quit
finish
