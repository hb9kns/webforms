#!/bin/sh
# shell script for converting logfiles created with webforms
info='convlog.sh // 2018-05-01 Y.Bonetti // http://github.com/hb9kns/webforms'

# minutes/day
dm=$(( 24*60 ))

if test "$1" = ""
then cat <<EOT

$info

convert logfile (from STDIN) generated with webforms.cgi

usage: $0 [-m MM|-d NN] <c>
 convert STDIN using columns <c> and <c+1> with absolute minute stamps,
 adding value=(<c+1>)-(<c>) in column <c+2>, using maximum value MM or
 value=$dm-NN-(<c>) if <c+1> is unreadable as minute stamp,
 keeping all other columns and printing to STDOUT
 Notes:
 - assumes first column <0> contains flag (+/-/*) which will be ignored
 - column counting starts at 1 which is effectively the *second* column
 - if several options are given, the last has priority

EOT
exit 9
fi

# invalidate all options
daymin=-1
maxmin=-1

while test "$1" != ""
do
 case $1 in
# only last option is valid
 -d) daymin=${2:-0} ; maxmin=-1 ; shift ;;
 -m) maxmin=${2:-0} ; daymin=-1 ; shift ;;
 *) begcol=$1 ;;
 esac
 shift
done

cat <<EOI >&2
## $0
## logical timestamp start column: $begcol
## daymin: $daymin
## maxmin: $maxmin
## processing...
EOI

# physical columns up to, begin, end, from/after time stamp
tocol=$begcol
begcol=$(( $tocol+1 ))
endcol=$(( $tocol+2 ))
fmcol=$(( $tocol+3 ))

while read inpt
do
# get line parts before and after time stamp
 front=`echo "$inpt" | cut -f -$tocol`
 rear=`echo "$inpt" | cut -f $fmcol-`
# get timestamp parts
 begval=`echo "$inpt" | cut -f $begcol`
 endval=`echo "$inpt" | cut -f $endcol`
 case $inpt in
# if line begins with *
# output header line with additional column (note: TABs!)
 \**) cat <<EOT
$front	$begval	$endval	minutes	$rear
EOT
  ;;
# if line begins with +/-
 -*|+*)
#echo ":: $front :: '$begval' -- '$endval' :: $rear //" >&2
# get minute values: remove everything up to '=' from timestamp
# and set to 0, if no '=' found
  begmin=${begval##*=}
  if test "$begmin" = "$begval"
  then begmin=0
  fi
  endmin=${endval##*=}
  if test "$endmin" = "$endval"
  then endmin=0
  fi
# check for numerical begin minutes
  if echo $(( $begmin+0 )) >/dev/null
  then
# check for numerical end minutes
   if echo $(( $endmin+0 )) >/dev/null
# if ok, use difference between column entries
   then effmin=$(( $endmin-$begmin ))
# otherwise, use max.value (depending on whether -m or -d option)
   else if test $maxmin -lt 0
    then effmin=$(( $dm-$daymin-$begmin ))
    else effmin=$maxmin
    fi
   fi
# output line with additional column (note: TABs!)
   cat <<EOT
$front	$begval	$endval	$effmin	$rear
EOT
# if invalid, just echo entire line with prepended warning and max value
# (note: TABs!)
  else cat <<EOT
# ## no valid minutes for begin: $begmin
$front	$begval	$endval	$maxmin	$rear
EOT
  fi
  ;;
# echo all other lines
 *) echo "$inpt" ;;
 esac
done
