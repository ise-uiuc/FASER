#!/usr/bin/env bash
# ./cleverhans_setup.sh [dir]
cd $1
if [ -e "${1}/trax" ]; then
  echo "Already installed"
  exit 0
fi

source ~/anaconda3/etc/profile.d/conda.sh
conda create -n trax python=3.7 -y
git clone https://github.com/google/trax.git
cd trax
git checkout d6cae2067dedd0490b78d831033607357e975015 -b evalcommit

conda activate trax
conda install -y pip pytest
pip install -e .[develop]
pip install -e .[tensorflow]
pip install -e .[tensorflow_gpu]
pip install -e .[t5]
pip install -e .[tests]
pip install -e .[t2t]
pip install coverage
conda deactivate
