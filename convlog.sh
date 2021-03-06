#!/bin/sh
# shell script for converting logfiles created with webforms
info='convlog.sh // 2018-07-05 Y.Bonetti // http://github.com/hb9kns/webforms'

# minutes/day
dm=$(( 24*60 ))
# general minimum value
dmin=5

if test "$1" = ""
then cat <<EOT

$info

convert logfile (from STDIN) generated with webforms.cgi

usage: $0 [-s] [-m MM|-n] [-x XX] [-i II] <c>
 convert STDIN using columns <c> and <c+1> with absolute minute stamps,
 adding (<c+1>)-(<c>) in column <c+2>, using maximum value MM (-m)
 or $dm-(<c>) (-n, midnight logout) if <c+1> is unreadable as minutes,
 using maximum value XX (-x, or $dm if not given),
 general minimum value II (-i, or $dmin if not given),
 keeping all other columns and printing to STDOUT,
 not adding column <c+2> in case of option -s
 Notes:
 - assumes first column <0> contains flag (+/-/*) which will be ignored
 - column counting starts at 1 which is effectively the *second* column
 - if several options or columns are given, the last will be used

EOT
exit 9
fi

# preset all options to invalid or maximum
begcol=-1
daymin=-1
maxmin=-1
maxmax=$dm
minmin=$dmin
same=no

args="$*"
while test "$1" != ""
do
 case $1 in
# only one option of -m or -n is valid
 -n) daymin=0 ; maxmin=-1 ;;
 -m) maxmin=${2:-0} ; daymin=-1 ; shift ;;
# absolute maximum in minutes
 -x) maxmax=${2:-$dm} ; shift ;;
 -i) minmin=${2:-$dmin} ; shift ;;
 -s) same=yes ; shift ;;
 *) begcol=$1 ;;
 esac
 shift
done

cat <<EOI
### $0 $args
### logical timestamp start column: $begcol
### daymin: $daymin
### minmin: $minmin
### maxmin: $maxmin
### maxmax: $maxmax
EOI

if test $begcol -le 0
then echo "illegal column $begcol, aborting!" >&2
 exit 1
fi

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
# output header line with additional column (note: TABs!) unless option -s
 \**) if test $same = no
  then cat <<EOT
$front	$begval	$endval	minutes	$rear
EOT
  else cat <<EOT
$front	$begval	$endval	$rear
EOT
  fi
  ;;
# if line begins with +/-
 -*|+*)
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
  if test $effmin -lt 0 -o $effmin -gt $dm
  then effmin=$limmin
  fi
# limit value
  if test $effmin -gt $maxmax
  then effmin=$maxmax
  fi
  if test $effmin -lt $minmin
  then effmin=$minmin
  fi
# output line with additional column (note: TABs!) unless option -s
  if test $same = no
  then cat <<EOT
$front	$begval	$endval	$effmin	$rear
EOT
  else cat <<EOT
$front	$begval	$endval	$rear
EOT
  fi
  ;;
# echo all other lines (comments)
 *) echo "$inpt" ;;
 esac
done
