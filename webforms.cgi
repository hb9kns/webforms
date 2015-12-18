#!/bin/sh
# webforms.cgi (2015 Yargo Bonetti)
# CGI script for handling flat file databases with common index/base
GITHOME=http://gitlab.com/yargo/webforms

if test "$REQUEST_METHOD" != "POST" -a "$REQUEST_METHOD" != "GET"
then cat <<EOT

This is $0
which must be run as a CGI script, expecting input from POST or GET requests.

See accompanying README file, or online repository at
	$GITHOME
for further information.

EOT
exit 9
fi

myself="$0"
mydir=`dirname "$0"`

# set root for temporary files
TMPR=${TMP:-/tmp}/webformtmp$$

# temp files for input
tmpf=$TMPR.tmp
inpt=$TMPR.inp

cat >$tmpf
echo "$QUERY_STRING" >>$tmpf

# save STDIN (POST input) in decoded form:
# first translate '+' into SPC and ';&' (separators) into new lines
# (note: after the last "'" there is a SPC!)
# then permitted escaped characters (restricted for security reasons)
cat $tmpf | tr '+;&' ' 
' | sed -e "s/%C2%B0/deg/g;
 s/%C3%A4/ae/g;s/%C3%B6/oe/g;s/%C3%BC/ue/g;
 s/%C3%84/Ae/g;s/%C3%96/Oe/g;s/%C3%9C/Ue/g;
 s/%2B/+/g;s/%22/'/g;s/%25/&/g;s/%2F/\//g;s/%28/(/g;s/%29/)/g;s/%3D/=/g;
 s/%3F/?/g;s/%27/'/g;s/%5E/^/g;s/%7E/~/g;s/%3C/</g;s/%3E/>/g;
 s/%7B/{/g;s/%7D/}/g;s/%5B/[/g;s/%5D/]/g;s/%21/!/g;s/%24/\$/g;
 s/%2C/,/g;s/%3B/;/g;s/%3A/:/g;s/%23/#/g;s/%7C/|/g;s/%60/'/g;
 s/%26/%/g" >$inpt

### now some functions!

# end script after cleanup with exit code as arg.1
finish(){
/bin/rm -f ${TMPR}*
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
 permchar=${2:-'0-9.A-Za-z_-'}
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
<tt>`date '+%a %Y-%m-%d %H:%M'` // db=$db // $usr($perm)</tt>
</p>
<p>
:: <a href="$myself?db=$db&vw=listpages">page list</a>
:: <a href="$myself?db=$db&vw=listindex">index list</a>
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
<p><small><i>processed by <a href="$GITHOME">$myself</a></i></small></p>
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
<th><a href="$myself?db=$db&vw=$vw&sc=$nc&sd=$nd">$field</a></th>
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

### now preparations for the main script!

# set root for configuration files / working directory
# (this could be set to some hardcoded directory for improved security)
wdir=${WEBFORMSDIR:-$mydir}
# default/fallback
defcfg=default

# define config file name
db=`inptvar db`
cfg="$wdir/${db:-defcfg}.cfg"
if test ! -r "$cfg"
then fatal "configuration file $cfg not readable"
# this should never be reached, but just to be sure:
 exit 9
fi

# define index/base file name, '.' is wildcard for index name
idx=`pagefile base . <$cfg`
if test ! -r "$idx"
then fatal "index/base file $cfg not readable"
 exit 9
fi

# establish permissions (the higher, the better)
perm=0
usr=${REMOTE_USER:-nobody}
if checkline admin $usr <$cfg
then perm=100
else
 if checkline editor $usr <$cfg
 then perm=10
 else
# if "visitor" entries exist, user must be explicitly allowed
  if grep "^visitor" $cfg 2>&1 >/dev/null
  then
   if checkline visitor $usr <$cfg
   then perm=1
   else perm=0
   fi
# otherwise all unknown users are visitors
  else perm=1
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

# at least permission 1 is necessary for running script at all
if test $perm -lt 1
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

# get and sanitize index value
in=`inptvar in '0-9a-zA-Z.-'`

### now the real work!

# get view/command, and process info / render page
vw=`inptvar vw '0-9A-Za-z'`
vw=${vw:-default}
case $vw in

 page)
  pg=`inptvar pg '0-9A-Za-z'`
  header "$pg" "`pageinfo page $pg`" "For modification, select index name, or
<a href=\"$myself?db=$db&in=&vw=editentry\">create new entry.</a>"
  pagef="`pagefile page $pg`"
  if test -r "$pagef"
  then
# make header for user columns of page file
   tablehead $pagef $nopageindex
   getlines '[+]' <$pagef | sort $sortopt -k $sc | { IFS="	" # TAB
    while read in f1 desc
# create link to edit view
    do
     if test $nopageindex = 1
# use first field as link text, and for description of index/base
     then cat <<EOH
<tr>
<td><a href="$myself?db=$db&in=$in&vw=editentry">$f1</a>
    <a href="$myself?db=$db&in=$in&vw=descindex">?</a></td>
EOH
# use index field, and also render first field
     else cat <<EOH
<tr>
<td><a href="$myself?db=$db&in=$in&vw=editentry">$in</a>
    <a href="$myself?db=$db&in=$in&vw=descindex">?</a></td>
<td>$f1</td>
EOH
     fi
# split remaining description into table fields and render
     echo "<td>$desc</td>" | sed -e 's:	:</td><td>:g'
     echo '</tr>'
    done
    }
   cat <<EOH
</table>
EOH
  else cat <<EOH
<p>Sorry, but page "$pg" with <b>file name "$pagef" cannot be read!</b></p>
EOH
  fi
  footer ;; # page.

 listpages)
  header "available pages" "List of Available Pages" "This is the list of all pages available for database <tt>$db</tt>."
  echo '<table><tr><th>page name</th><th>page description</th></tr>'
  getlines page <$cfg | { IFS="	" # TAB
   while read name file desc
   do cat <<EOH
<tr>
<td><a href="$myself?db=$db&pg=$name&vw=page">$name</a></td>
<td>$desc</td></tr>
EOH
   done
   }
  echo '</table>'
  footer ;; # listpages.

 listindex) 
  header "index" "List of Index Values" "This is the list of all index values available for database <tt>$db</tt>.<br />Click links in first column to edit."
# make header for all columns of index file
  tablehead $idx 0
# get lines with '+' or '-'
  getlines '[+-]' <$idx | sort $sortopt -k $sc | { IFS="	" # TAB
# some local variables for new index values
   local maxind pastind i
   maxind=0
   i=1
   while read in desc
# use index for link to edit view
   do cat <<EOH
<tr>
<td><a href="$myself?db=$db&in=$in&vw=editindex">$in</a></td>
EOH
# split description into table fields
    echo "<td>$desc</td>" | sed -e 's:	:</td><td>:g'
    echo '</tr>'
# convert last index to numeric value and increment,
# or set to counter value, if non-numeric
    pastind=`expr $in + 1` ; pastind=${pastind:-$i}
    if test $maxind -lt $pastind
    then maxind=$pastind
    fi
    i=`expr $i + 1`
   done
# report next index outside of loop
   echo $maxind >$tmpf
   }
  newindex=`head -n 1 $tmpf`
  cat <<EOH
</table>
 <p>create
 <a href="$myself?db=$db&in=$newindex&vw=editindex">new index entry</a>
</p>
EOH
  footer ;; # listindex.

 descindex)
  header "index/base $in" 'Index/base description' "Values associated with index <tt>$in</tt>"
  echo '<pre>'
  getlines '[+-]' <$idx | getlines $in
  echo '</pre>'
  cat <<EOH
<p><a href="$myself?db=$db&in=$in&vw=editindex">EDIT</a></p>
EOH
  footer ;; # descindex.

 editindex)
  header "edit index" "Edit index/base fields" "Edit fields and SAVE.<br />Notes: first field (index) must be unique, will overwrite old entry if already present! To suppress listing of this index on record page, deselect SHOW!"
# get selected index (but only the first one)
  cat <<EOH
 <form enctype="application/x-www-form-urlencoded" method="post" action="$myself">
EOH
  tablehead $idx 0
# get number of rendered header fields
  totalcols=$?
  cat <<EOH
 <tr>
  <td>SHOW<input type="checkbox" name="fa" value="show" checked>
   <input type="text" name="in" value="$in" /></td>
EOH
  getlines '[+-]' <$idx | getlines $in | head -n 1 | sed -e 's:	:\
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
 <input type="hidden" name="db" value="$db">
 <input type="hidden" name="vw" value="saveindex">
 <input type="submit" name="submit" value="SAVE">
 </form>
EOH
  footer ;; # editindex.

 saveindex)
  header "saveindex" "Saving index entry" "Please wait..."
  cat <<EOH
<pre>
    db=`inptvar db`
    pg=`inptvar pg`
    in=`inptvar in`
    vw=`inptvar vw`
    fa=`inptvar fa`
    f1=`inptvar f1`
    f2=`inptvar f2`
    f3=`inptvar f3`
    f4=`inptvar f4`
    f5=`inptvar f5`
</pre>
<hr />
<a href="$myself?db=$db&vw=listindex&sc=1&sd=1">show index</a>
EOH
  footer ;; # saveindex.

 editentry)
  header 'edit entry' "Edit page entry" "Edit fields and SAVE (HIDE to delete an entry without saving)"
  maxflength=`getlines maxlength <$cfg | head -n 1`
  maxflength=${maxflength:-199}
  pg=`inptvar pg '0-9A-Za-z'`
  pagef="`pagefile page $pg`"
  if test -r "$pagef"
  then
   cat <<EOH
 <form enctype="application/x-www-form-urlencoded" method="post" action="$myself">
EOH
# make header for user columns of page file, with all columns
   tablehead $pagef 0
# get number of rendered header fields
   totalcols=$?
# delete link
   cat <<EOH
 <tr><td><select name="id">
EOH
# get all possible index names, only uniques
  getlines '[+]' <$idx | sed -e 's/	.*//' | sort -u | { local nin
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
   getlines '[+-]' <$pagef | getlines $in | head -n 1 | sed -e 's:	:\
:g;s/"/\\"/g' | { local fn field af
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
 <input type="hidden" name="vw" value="saveentry">
 <input type="hidden" name="fa" value="save">
 <input type="submit" name="submit" value="SAVE">
 <a href="$myself?db=$db&in=$in&vw=saveentry&fa=hide">HIDE</a>
 </form>
EOH
  else cat <<EOH
<p>Sorry, but page "$pg" with <b>file name "$pagef" cannot be read!</b></p>
EOH
  fi
  footer ;; # editentry.

 saveentry)
  header 'save entry' "Save entry" "Please wait ..."
  cat <<EOH
<pre>
    db=`inptvar db`
    pg=`inptvar pg`
    in=`inptvar in`
    vw=`inptvar vw`
    fa=`inptvar fa`
    f1=`inptvar f1`
    f2=`inptvar f2`
    f3=`inptvar f3`
    f4=`inptvar f4`
    f5=`inptvar f5`
</pre>
<hr />
<a href="$myself?db=$db&vw=listindex&sc=1&sd=1">show index</a>
EOH
  footer ;; # saveentry.

 test) header test Test TEST ; footer ;;
 *) # for debugging
   echo Content-type:text/plain
   echo
   echo "db=`inptvar db` (cfg=$cfg)"
   echo "pg=`inptvar pg`"
   echo "in=`inptvar in`"
   echo "vw=`inptvar vw`"
   echo "f1=`inptvar f1`"
   echo
   echo admins:
   getlines admin <$cfg
   echo editors:
   getlines editor <$cfg
   echo visitors:
   getlines visitor <$cfg
   echo permissions=$perm for user=$usr
   echo
   echo inpt:
   cat $inpt
 ;;
esac

# cleanup and quit
finish
