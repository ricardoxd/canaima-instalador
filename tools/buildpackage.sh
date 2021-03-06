#!/bin/sh -e
#
# ====================================================================
# PACKAGE: aguilas
# FILE: tools/buildpackage.sh
# DESCRIPTION:  Makes a new debian package of a stable release.
# USAGE: ./tools/buildpackage.sh
# COPYRIGHT:
# (C) 2012 Luis Alejandro Martínez Faneyth <luis@huntingbears.com.ve>
# LICENCE: GPL3
# ====================================================================
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# COPYING file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# CODE IS POETRY

ROOTDIR="$( pwd )"
ROOTNAME="$( basename ${ROOTDIR} )"
PROJDIR="$( dirname ${ROOTDIR} )"
VERSION="${ROOTDIR}/VERSION"
TYPE="${1}"
VERDE="\033[1;32m"
ROJO="\033[1;31m"
AMARILLO="\033[1;33m"
FIN="\033[0m"

ERROR() {
        printf "${ROJO}${1}${FIN}\n"
}

WARNING() {
        printf "${AMARILLO}${1}${FIN}\n"
}

SUCCESS() {
        printf "${VERDE}${1}${FIN}\n"
}

git checkout master
git clean -fd
git reset --hard

LASTCOMMIT="$( git rev-parse HEAD )"
OLDDEBVERSION="$( dpkg-parsechangelog | grep "Version: " | awk '{print $2}' )"
OLDDEBSTATUS="$( dpkg-parsechangelog | grep "Distribution: " | awk '{print $2}' )"
OLDRELVERSION="$( echo ${OLDDEBVERSION} | sed 's/-.*//g' )"
OLDREV="$( echo ${OLDDEBVERSION#${OLDRELVERSION}-} | sed 's/~.*//g' )"

WARNING "Merging new upstream release ..."

if [ "${TYPE}" = "final-release" ] || [ "${TYPE}" = "test-release" ]; then
	git merge -q -s recursive -X theirs --squash release
elif [ "${TYPE}" = "test-snapshot" ]; then
	git merge -q -s recursive -X theirs --squash development
fi

NEWRELVERSION="$( cat ${VERSION} | grep "VERSION" | sed 's/VERSION=//g' | sed 's/"//g' )"

if [ "${OLDRELVERSION}" = "${NEWRELVERSION}" ]; then
	if [ "${OLDDEBSTATUS}" = "UNRELEASED" ]; then
		NEWREV="${OLDREV}"
	else
		NEWREV="$[ ${OLDREV}+1 ]"
	fi
else
	NEWREV="1"
fi

NEWDEBVERSION="${NEWRELVERSION}-${NEWREV}"

WARNING "Generating Debian changelog ..."
if [ "${TYPE}" = "final-release" ]; then
	OPTIONS="-kE78DAA2E -tc --git-tag --git-retag"
	git dch --new-version="${NEWDEBVERSION}" --release --auto --id-length=7 --full
elif [ "${TYPE}" = "test-snapshot" ] || [ "${TYPE}" = "test-release" ]; then
	OPTIONS="-us -uc"
	git dch --new-version="${NEWDEBVERSION}" --snapshot --auto --id-length=7 --full
fi

WARNING "Committing changes ..."
git add .
git commit -q -a -m "Importing New Upstream Release (${NEWRELVERSION})"

WARNING "Generating tarball ..."
tar --anchored --exclude="debian" -czf ../canaima-instalador_${NEWRELVERSION}.orig.tar.gz *

WARNING "Generating Debian package ..."
git buildpackage ${OPTIONS}
git clean -fd
git reset --hard

if [ "${TYPE}" = "final-release" ]; then
	echo ""
fi

if [ "${TYPE}" != "final-release" ]; then
	git reset --hard ${LASTCOMMIT}
	git clean -fd
fi

git checkout development

exit 0
