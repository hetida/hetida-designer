#!/bin/bash -e

# Docker build / bublish script replacing the travis build job due to travis reducing open source support.
# This script can be used until an alternative automatic and open build service is selected and set up.

set -e

SOURCE_BRANCH=develop
TARGET_BRANCH=release

DOCKER_ORGANIZATION="hetida"
DRY_RUN=false

function usage() {
  if [ -n "$1" ]; then
    echo -e "ERROR: $1\n"
  fi
  echo "Usage: $0 [-u docker-hub-user] [-p docker-hub-password]"
  echo "  -u, --docker-hub-user        Docker Hub username"
  echo "  -p, --docker-hub-password    Docker Hub password"
  echo "  -d, --dryrun                 don't run the docker build / tag / push commands"
  echo "  -h, --help                   Print this help"
  echo ""
  echo "Example: $0 --docker-hub-user user --docker-hub-password my_secret_password"
  echo ""
  echo "Builds docker images on the current release branch and pushes them to docker hub."
  echo "Uses version from VERSION file as tag and also pushes the images as 'latest'."
  echo "This should be run once after publishing a new release (see release.sh script)."
  exit 1
}

######################################################
# Parse arguments
######################################################

while [[ "$#" -gt 0 ]]; do case $1 in
  -u | --docker-hub-user)
    DOCKER_USER="$2"
    shift
    shift
    ;;
  -p | --docker-hub-password)
    DOCKER_PASSWORD="$2"
    shift
    shift
    ;;
  -d | --dryrun)
    DRY_RUN=true
    shift
    ;;
  -h | --help) usage ;;
  *)
    usage "Unknown parameter passed: $1"
    shift
    shift
    ;;
  esac done

# validate arguments:
if [ -z "$DOCKER_USER" ]; then usage "Docker Hub user is not set"; fi
if [ -z "$DOCKER_PASSWORD" ]; then usage "Docker Hub password is not set."; fi

if "$DRY_RUN"; then
  echo "Dry Run Mode active!"
  cmd=echo
else
  cmd=''
fi

######################################################
# Run Build and Push
######################################################

echo "Log into docker hub"
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin

echo "Check out release branch $TARGET_BRANCH"
git checkout --quiet "$TARGET_BRANCH"

VERSION=$(cat VERSION)
echo "Building Version: $VERSION"
sleep 7 # some time to allow arborting ;-)

build_and_push() {
  SERVICE_NAME=$1
  SERVICE_VERSION=$2
  DOCKERFILE_SUFFIX="${3:-"$SERVICE_NAME"}"
  echo "Build service $SERVICE_NAME version $SERVICE_VERSION"
  $cmd docker build -t "$DOCKER_ORGANIZATION"/designer-"$SERVICE_NAME":latest -f Dockerfile-"$DOCKERFILE_SUFFIX" .
  echo "Tag service $SERVICE_NAME version $SERVICE_VERSION"
  $cmd docker tag "$DOCKER_ORGANIZATION"/designer-"$SERVICE_NAME":latest "$DOCKER_ORGANIZATION"/designer-"$SERVICE_NAME":"$SERVICE_VERSION"
  echo "Push service $SERVICE_NAME version $SERVICE_VERSION with tag latest"
  $cmd docker push "$DOCKER_ORGANIZATION"/designer-"$SERVICE_NAME":latest
  echo "Push service $SERVICE_NAME version $SERVICE_VERSION with tag $SERVICE_VERSION"
  $cmd docker push "$DOCKER_ORGANIZATION"/designer-"$SERVICE_NAME":"$SERVICE_VERSION"
}

build_and_push frontend $VERSION
build_and_push runtime $VERSION
build_and_push backend $VERSION "runtime" # uses runtime image
build_and_push demo-adapter-python $VERSION

echo "Check out source branch $SOURCE_BRANCH"
git checkout --quiet "$SOURCE_BRANCH"

echo "Finished."
