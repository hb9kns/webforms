#!/bin/sh
# webforms.cgi (2015 Y.Bonetti)
# CGI script for handling flat file databases with common index/base

if test "$REQUEST_METHOD" != "POST" -a "$REQUEST_METHOD" != "GET"
then cat <<EOT

This is $0
which must be run as a CGI script, expecting input from POST or GET requests.

See accompanying README file, or online repository at
    http://gitlab.com/yargo/webforms
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

# get values from decoded input data
inptvar(){
 grep "^$1=" $inpt | head -n 1 | sed -e 's/[^=]*=//'
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
getlines "$1" | { IFS="	" # TAB
 while test "$1" != ""
 do if test "$entry" = "$1"
  then found=1
   break
  else shift
  fi
 done
 }
if test $found = 0
then false
else true
fi
}

# display header, arg.1 = page title, arg.2 = main title, arg.3 = description
header(){
cat <<EOH
Content-type: text/html

<html><head><title>$1</title></head>
<body>
<p>
:: <a href="$myself?db=$db&vw=listpages">show all pages</a>
:: <a href="$myself?db=$db&vw=listindex">show index</a>
:: <a href="$myself?db=$db&vw=none">none</a>
:: <a href="test.html">form</a>
:: </p>
<hr />
<h1>$2</h1>
EOH
shift
shift
cat <<EOH
<p>$*</p>
<hr />
EOH
}

# display footer with some additional info
footer(){
sleep 1 # reduce load in case of runaway issues
cat <<EOH
<hr />
<p><tt>:: `date` :: db=$db :: user=$usr ::</tt></p>
<p><small>$myself (2015 YCB)</small></p>
</body></html>
EOH
}

# get file name for arg.1=type, arg.2=page
pagefile(){
# get file name
 getlines $1 <$cfg | getlines $2 | { IFS="	" # TAB
  read pfile _
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
 }
 echo '</tr>'
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
if checkline admin $usr
then perm=100
else
 if checkline editor $usr
 then perm=10
 else
# if "visitor" entries exist, user must be explicitly allowed
  if grep "^visitor" $cfg 2>&1 >/dev/null
  then
   if checkline visitor $usr
   then perm=1
   else perm=0
   fi
# otherwise all unknown users are visitors
  else perm=1
  fi # visitor
 fi # editor
fi # admin

# at least permission 1 is necessary for running script at all
if test $perm -lt 1
then fatal user $usr is not allowed
 exit 9
fi

### now the real work!

# get and normalize sort column and order
sc=`inptvar sc | tr -c -d '0-9'`
sc=${sc:-1}
if test $sc -lt 1
then sc=1
fi
sd=`inptvar sd | tr -c -d '0-9'`
# define option flag for sort command
case $sd in
 0) sortopt='' ;;
 1) sortopt='-r' ;;
 *) sd=0 ; sortopt='' ;;
esac

# get view/command, and process info / render page
vw=`inptvar vw`
vw=${vw:-default}
case $vw in
 page)
 ;; # page.
 listpages)
  header "available pages" "List of Available Pages" "This is the list of all pages available for the current database."
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
  header "index" "List of Index Values" "This is the list of all index values defined for the current database."
# make header for all columns of index file
  tablehead $idx 0
# get lines with '+' or '-'
  getlines '[+-]' <$idx | sort $sortopt -k $sc | { IFS="	" # TAB
   while read in desc
# use index for link to edit view
   do cat <<EOH
<tr>
<td><a href="$myself?db=$db&in=$in&vw=editindex">$in</a></td>
EOH
# split description into table fields
    echo "<td>$desc</td>" | sed -e 's:	:</td><td>:g'
    echo '</tr>'
   done
   }
  echo '</table>'
  footer ;; # listindex.
 descindex) ;;
 editindex) ;;
 saveindex) ;;
 editentry) ;;
 saveentry) ;;
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
