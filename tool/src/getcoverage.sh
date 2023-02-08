#!/usr/bin/env bash
#export MKL_THREADING_LAYER=gnu
export GEOMSTATS_BACKEND=tensorflow
projectdir=`echo $1 | grep -o ".*/projects/[a-zA-Z0-9_-]\+"`
testfile=$1
envname=$2
echo $projectdir
echo $testfile
echo $envname

source ~/anaconda3/etc/profile.d/conda.sh
which conda
# make the virtual environment name parameterizable
conda activate ${envname}
conda env list

cd $projectdir
echo $projectdir

export PYTHONDONTWRITEBYTECODE=1
coverage json -i --pretty-print
retcode=$?

conda deactivate
cd -
exit $retcode

