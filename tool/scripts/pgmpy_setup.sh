#!/usr/bin/env bash

cd $1
if [ -e "${1}/pgmpy" ];then
    echo "Already installed"
    exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n pgmpy -y python=3.7
git clone https://github.com/pgmpy/pgmpy.git
cd pgmpy
git checkout c427cfd41afe1eaa83b7be699e7cc8c783edef06 -b evalcommit
conda activate pgmpy
conda install -y pip pytest
pip install -r requirements.txt
pip install -r requirements/tests.txt
conda deactivate
cd -