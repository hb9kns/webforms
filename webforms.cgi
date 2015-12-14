#!/bin/sh
# webforms.cgi (2015 Y.Bonetti)
# CGI script for handling flat file databases with common index/base

if test "$REQUEST_METHOD" != "POST" -a "$REQUEST_METHOD" != "GET"
then cat <<EOT

This is the script $0
which must be run as a CGI script.

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

# get values from decoded input data
inptvar(){
 grep "^$1=" $inpt | head -n 1 | sed -e 's/[^=]*=//'
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
exit 5
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
entry=$2
found=0
getlines $1 | { IFS="	" # TAB
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

# end script with cleanup
finish(){
/bin/rm -f ${TMPR}*
exit 0
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

# generate HTML table head for arg.1=type, arg.2=page and arg.3=start column
tablehead(){
 local pf skip
 pf=`pagefile $1 $2`
#echo "pagefile <tt>$1:$pf</tt>"
 skip=$3
 echo '<table><tr>'
# get first line beginning with '*'
 getlines '*' <$pf | head -n 1 | sed -e 's/	/
/g' | { while read field
  do if test $skip -gt 0
   then skip=`expr $skip - 1`
   else echo "<th>$field</th>"
   fi
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
then fatal configuration file $cfg not readable
# this should never be reached, but just to be sure:
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
# if "visitor" entries exist, user must be listed
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

# get view/command, and process info / render page
vw=`inptvar vw`
vw=${vw:-default}
case $vw in
 page)
 ;;
 listpages)
  header "available pages" "List of Available Pages" "Here is the list of all pages available for the current database."
# generate tablehead, starting at column 2 (after index, skipping 2)
  cat <<EOH
  <table><tr><th>page name</th><th>page description</th></tr>
EOH
  getlines page $cfg | { IFS="	" # TAB
   while read name file desc
   do echo "<tr><td>$name</td><td>$desc</td></tr>"
   done
   }
  echo '  </table>'
  footer ;;
 listindex) ;;
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
   echo pageinfo=$pinfo
   echo pagefile=$pfile
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
