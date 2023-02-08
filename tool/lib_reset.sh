#!/usr/bin/env bash
maindir=$1
for d in `ls $maindir`; do
    echo $d
    cd $maindir/$d
    git checkout -- .
    #find -name "__pycache__" -exec rm -rf {} \; &> /dev/null
    cd - #&> dev/null
done


