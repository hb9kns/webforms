#!/bin/sh
# shell script for forcing illegal logfiles timestamps into limits
# reusing parts of webforms.cgi (file locking and backup routines)
info='forcelog.sh // 2018-06-15 Y.Bonetti // http://gitlab.com/yargo/webforms'

# presets for reusing of webforms.cgi backup routine
REMOTE_ADDR=${HOSTNAME:-localhost}
usr=${USER:-localuser}

if test "$1" = "" -o "$2" = ""
then cat <<EOT

$info

force logfile entries using convlog script
with in-place modification and file locking

usage: $0 <logfile> <convlog script> <arguments to convlog>
 convert logfile in-place using <convlog script> with -s option
 Notes:
 - <convlog script> must be name of executable script, e.g './convlog.sh'
 - see convlog.sh usage for additional arguments/options
 - logfile '-' means to read from STDIN and print to STDOUT (pipe mode)

EOT
exit 9
fi

logf="$1"
if test "$logf" = "-"
then mode=pipe
else mode=inplace
fi
shift

if test -r "$1" -a -x "$1"
then convscr="$1"
else cat <<EOT
error: $1
 is not readable and executable, aborting!
EOT
exit 9
fi
shift

# save remaining arguments for convlog script, prepending "same" option
convargs="-s $@"

# set root for temporary files
# (make sure this is a pattern only for temporary files, because
# there is an 'rm -f $tmpr*' command at the end of the script!)
# if `$TMPDIR` contains whitespace or other crap, anything might happen!
tmpr=${TMPDIR:-/tmp}/webform-$user-forcetmp$$

# temp file
tmpf=$tmpr.tmp

# message to STDERR
notify () { echo ":: $*" >&2 ; }

#### routines from webforms.cgi

# save new version of database; arg.1 = modified file, arg.2 = remarks
# (user name and REMOTE_ADDR will be added to the remarks)
dobackup(){
 dmesg="$2 (user=$usr, remote=$REMOTE_ADDR)"
# comment/uncomment below as desired! commenting out all is also possible
## git version
 #git add "$1" && git commit -m "$dmesg"
## rcs version
 #ci -l -w"$usr" -m"$dmesg" "$1"
## poor man's version -- if commenting, do all lines of <<EOH document!
 cat <<EOH >>"$1.diff"

## $nowstring : $dmesg
EOH
# ed-like inverse (new to old) diff: short, and can be more easily replayed
 diff -e "$1" "$1.old" >>"$1.diff"
 cat "$1" > "$1.old"
# make sure backup files cannot be read by others/all
 chmod o-rwx "$1.old" "$1.diff"
}

# end script after cleanup with exit code as arg.1
finish(){
/bin/rm -f ${tmpr}*
# exit code arg.1, or 0 if missing
exit ${1:-0}
}

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

#### main program

if test $mode = inplace
then notify "inplace processing $logf"
 lockit=`lockfile "$logf"`
 if test "$lockit" = ""
 then notify "cannot get lockfile, giving up!"
 finish 9
 else
  "$convscr" $convargs <"$logf" >$tmpf && cat $tmpf >"$logf" && dobackup "$logf"
  releasefile "$lockit"
 fi
else notify 'pipe mode'
 "$convscr" $convargs
fi

# cleanup and quit
notify done
finish
