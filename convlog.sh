#!/bin/sh
# shell script for converting logfiles created with webforms
info='convlog.sh // 2018-05-01 Y.Bonetti // http://github.com/hb9kns/webforms'

# minutes/day
dm=$(( 24*60 ))

if test "$1" = ""
then cat <<EOT

$info

convert logfile (from STDIN) generated with webforms.cgi

usage: $0 [-m MM|-n] [-x XX] <c>
 convert STDIN using columns <c> and <c+1> with absolute minute stamps,
 adding (<c+1>)-(<c>) in column <c+2>, using maximum value MM (-m)
 or $dm-(<c>) (-n, midnight logout) if <c+1> is unreadable as minutes,
 using maximum value XX (-x, or $dm if not given),
 keeping all other columns and printing to STDOUT
 Notes:
 - assumes first column <0> contains flag (+/-/*) which will be ignored
 - column counting starts at 1 which is effectively the *second* column
 - if several options are given, the last has priority

EOT
exit 9
fi

# preset all options to invalid or maximum
daymin=-1
maxmin=-1
maxmax=$dm

while test "$1" != ""
do
 case $1 in
# only one option of -m or -n is valid
 -n) daymin=0 ; maxmin=-1 ;;
 -m) maxmin=${2:-0} ; daymin=-1 ; shift ;;
# absolute maximum in minutes
 -x) maxmax=${2:-$dm} ; shift ;;
 *) begcol=$1 ;;
 esac
 shift
done

cat <<EOI >&2
: $0
: logical timestamp start column: $begcol
: daymin: $daymin
: maxmin: $maxmin
: maxmax: $maxmax
: processing...
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
# preset upper limit to one day
  limmin=$dm
# check for numerical begin and end minutes
  if echo $(( $begmin+0 )) >/dev/null && echo $(( $endmin+0 )) >/dev/null
  then effmin=$(( $endmin-$begmin ))
# calculate upper limit as max.minutes or minutes up to midnight
   if test $maxmin -lt 0
   then limmin=$(( $dm-$daymin-$begmin ))
   else limmin=$maxmin
   fi
  else effmin=-1
  fi
# in case of illegal minutes (negative or more than a day)
  if test $effmin -le 0 -o $effmin -gt $dm
  then effmin=$limmin
  fi
# limit value
  if test $effmin -gt $maxmax
  then effmin=$maxmax
  fi
# output line with additional column (note: TABs!)
   cat <<EOT
$front	$begval	$endval	$effmin	$rear
EOT
  ;;
# echo all other lines
 *) echo "$inpt" ;;
 esac
done
