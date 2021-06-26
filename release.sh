#!/bin/bash -e

###########################################################################
# Constants...
###########################################################################

SOURCE_REMOTE=origin
SOURCE_BRANCH=develop

TARGET_REMOTE=origin
TARGET_BRANCH=release
TARGET_REPO='git@github.com:hetida/hetida-designer.git'

SOURCE_REMOTE_BRANCH="$SOURCE_REMOTE/$SOURCE_BRANCH"
TARGET_REMOTE_BRANCH="$TARGET_REMOTE/$TARGET_BRANCH"

###########################################################################
# Usage...
###########################################################################

print_usage() {
 echo
 echo "Usage:"
 echo
 echo "  release.sh --help"
 echo "    Displays this help message."
 echo
 echo "  release.sh <VERSION>"
 echo "    Creates (or checks out) a local '$TARGET_BRANCH' branch,tags the commit and pushes the result to github."
 echo
 echo "  Note: If a local branch named '$TARGET_BRANCH' already exists, it will be overwritten with the content of the remote release branch WITHOUT WARNING!"
 echo
}

if [ "$1" == '-h' -o "$1" == '--help' ]; then
 print_usage
 exit 0
fi

RELEASE_VERSION="$1"
if [ -z "$RELEASE_VERSION" ]; then
 print_usage
 exit 1
else
 echo
 echo "Releasing version '$RELEASE_VERSION' from '$SOURCE_REMOTE_BRANCH' to '$TARGET_REMOTE_BRANCH'."
fi

###########################################################################
echo
echo "Testing preconditions..."
###########################################################################

# 1. Test presence of the source repository.
echo -n "source remote '$SOURCE_REMOTE'"
REMOTE_ORIGIN=`git remote get-url "$SOURCE_REMOTE" 2>/dev/null || true`
if [ -z "$REMOTE_ORIGIN" ]; then
 echo " - not ok: missing"
 exit 1
else
 echo " - ok"
fi

# 2. Ensure presence of the correct target repository with correct url.
echo -n "target remote '$TARGET_REMOTE'"
REMOTE_URL=`git remote get-url "$TARGET_REMOTE" 2>/dev/null || true`
if [ -z "$REMOTE_URL" ]; then
 git remote add "$TARGET_REMOTE" "$TARGET_REPO"
 echo " - ok: added"
elif [ "$REMOTE_URL" == "$TARGET_REPO" ]; then
 echo " - ok"
else
 echo " - not ok: wrong remote URL '$REMOTE_URL'"
 exit 1
fi

git fetch --multiple "$SOURCE_REMOTE" "$TARGET_REMOTE" >/dev/null

# Usage: branch_exists <branch name> --extra --args
branch_exists() {
 EXISTING_BRANCH=`git branch $2 '--format=%(refname)' --list "$1"`
 if [ -n "$EXISTING_BRANCH" ]; then
  return 0
 else
  return 1
 fi
}

# Usage: remote_branch_exists <remote branch name>
remote_branch_exists() {
 branch_exists "$1" --remote
 return $?
}

# Usage: local_branch_exists <local branch name>
local_branch_exists() {
 branch_exists "$1"
 return $?
}

# 3. Test presence of the source branch
echo -n "remote source branch '$SOURCE_REMOTE_BRANCH'"
if remote_branch_exists "$SOURCE_REMOTE_BRANCH"; then
 echo " - ok"
else
 echo " - not ok: missing"
 exit 1
fi

# 4. Ensure local presence of the target branch.
echo -n "local target branch '$TARGET_BRANCH'"
if remote_branch_exists "$TARGET_REMOTE_BRANCH"; then
 git checkout --quiet -B "$TARGET_BRANCH" "$TARGET_REMOTE_BRANCH"
 echo " - ok: created"
else
 if local_branch_exists "$TARGET_BRANCH"; then
  echo " - ok: checked out'"
  git checkout --quiet "$TARGET_BRANCH"
 else
  git checkout --quiet --orphan "$TARGET_BRANCH"
  echo " - ok: initialized"
 fi
fi

# 5. Test whether the release version already exists.
RELEASE_TAG="v$RELEASE_VERSION"
echo -n "release tag availability '$RELEASE_TAG'"
EXISTING_TAG=`git tag --list "$RELEASE_TAG"` 
if [ -n "$EXISTING_TAG" ]; then
 echo " - not ok: exists"
 exit 1
else
 echo " - ok"
fi

###########################################################################
echo
echo "Preparing release..."
###########################################################################
# git restore --quiet --source "$SOURCE_REMOTE_BRANCH" .

echo "Get newest develop branch from remote"
git checkout --quiet "$SOURCE_BRANCH"
git pull "$SOURCE_REMOTE" "$SOURCE_BRANCH"

echo "Get newest release branch from remote"
git checkout --quiet "$TARGET_BRANCH"
git pull "$TARGET_REMOTE" "$TARGET_BRANCH"


echo "Checkout source branch and merge in target branch"
git checkout --quiet "$SOURCE_BRANCH"
git merge "$TARGET_BRANCH"

# Make sure changelog has been updated
CHANGELOG_DIFF=$(git diff "$SOURCE_BRANCH" "$TARGET_BRANCH" -- CHANGELOG.md)
if [ -z "$CHANGELOG_DIFF" ]; then
    echo "no changelog entry. Aborting. Please edit changelog."
    exit 1
else
    echo "- ok: found changelog edits"
fi

echo "add VERSION and CHANGELOG.md"
echo "$RELEASE_VERSION" > VERSION     # Version into version file
# git add --all
git add VERSION CHANGELOG.md
git commit --allow-empty --quiet --message="Release $RELEASE_TAG"
git tag "$RELEASE_TAG"


###########################################################################
echo
echo "Publishing release..."
###########################################################################
git push --tags --no-verify "$SOURCE_REMOTE" "$SOURCE_BRANCH"

git checkout --quiet "$TARGET_BRANCH"
git merge "$SOURCE_BRANCH"
git push --tags --no-verify "$TARGET_REMOTE" "$TARGET_BRANCH"
