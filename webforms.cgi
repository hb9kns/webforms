#!/bin/sh
# webforms.cgi (2015 Y.Bonetti)
# CGI script for handling flat file databases with common index/base

if test "$REQUEST_METHOD" != "POST"
then cat <<EOT

This is the script $0
which must be run as a CGI script with REQUEST_METHOD=POST.

See accompanying README file, or online repository at
    http://gitlab.com/yargo/webforms
for further information.

EOT
exit 9
fi

# set root for temporary files
TMPR=${TMP:/tmp}/webformtmp$0
inpt=$TMPR.inp

# save STDIN (POST input) in decoded form:
# first translate '+' into SPC and ';&' (separators) into new lines
# (note: after the last "'" there is a SPC!)
# then permitted escaped characters
tr '+;&' ' 
' | sed -e "s/%C2%B0/deg/g;
 s/%C3%A4/ae/g;s/%C3%B6/oe/g;s/%C3%BC/ue/g;
 s/%C3%84/Ae/g;s/%C3%96/Oe/g;s/%C3%9C/Ue/g;
 s/%2B/+/g;s/%22/'/g;s/%25/&/g;s/%2F/\//g;s/%28/(/g;s/%29/)/g;s/%3D/=/g;
 s/%3F/?/g;s/%27/'/g;s/%5E/^/g;s/%7E/~/g;s/%3C/</g;s/%3E/>/g;
 s/%7B/{/g;s/%7D/}/g;s/%5B/[/g;s/%5D/]/g;s/%21/!/g;s/%24/\$/g;
 s/%2C/,/g;s/%3B/;/g;s/%3A/:/g;s/%23/#/g;s/%7C/|/g;s/%60/'/g;
 s/%26/%/g" >$inpt

# function for getting values from POST string
postvar(){
:
}
