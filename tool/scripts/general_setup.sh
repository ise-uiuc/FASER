#!/usr/bin/env bash
# usage: ./general_setup.sh [install-dir] [github-slug] [local or global] [commit]
function log {
    echo "[$(date --rfc-3339=seconds)]: $*"
}

function systemdeps {

  sudo apt-get install -y libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev  subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev libfreetype6-dev
  sudo apt-get install -y build-essential libasound2-dev libjack-dev portaudio19-dev libsndfile1-dev libfreetype6-dev pkg-config libgmp3-dev libopenmpi-dev
  sudo apt-get install -y libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev  subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev libfreetype6-dev libeigen3-dev
  sudo apt-get install -y git cmake build-essential libgl1-mesa-dev libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev libsdl2-gfx-dev libboost-all-dev libdirectfb-dev libst-dev mesa-utils xvfb x11vnc libsdl-sge-dev  libmysqlclient-dev
  sudo apt-get install -y libmariadbclient-dev
  sudo apt-get install -y libpq-dev gdal-bin libgdal-dev
  sudo apt-get install -y clang cmake curl swig mysql-server
  if [[ -e /usr/include/locale.h && ! -e /usr/include/xlocale.h ]]; then
   sudo  ln -s /usr/include/locale.h /usr/include/xlocale.h
  fi
  if [[ -e  /usr/include/eigen3/Eigen && ! -e /usr/include/Eigen ]]; then
    sudo ln -s /usr/include/eigen3/Eigen /usr/include/Eigen
  fi
}
set -v
PYTHON_VERSION=3.6
INSTALL_DIR=$1
PROJECT_SLUG=$2
if [[ ! -z $3 ]]; then
  LOCAL=1
else
  LOCAL=0
fi


cd ${INSTALL_DIR}


project_name=`echo $PROJECT_SLUG | cut -d"/" -f2`
LOGFILE="${project_name}_install_log.txt"
touch $LOGFILE
LOGFILE=`realpath $LOGFILE`
log "Installing ${PROJECT_SLUG}"

if [[ "$3" == "azure" ]]; then
  log "Installing system dependencies"
  systemdeps
fi

source ~/anaconda3/etc/profile.d/conda.sh
log "Creating conda environment"
conda create -n ${project_name} python=${PYTHON_VERSION} -y &>> ${LOGFILE}


log "Cloning ${project_name}"
git clone https://github.com/${PROJECT_SLUG}.git &>> ${LOGFILE}
cd ${project_name}
if [[ ! -z $4 ]]; then
  git checkout $4 -b evalcommit
fi

git log -1 --pretty=format:"%h" > ../commit.txt
conda activate ${project_name}
log "Installing python package"
conda install -y pip &>> ${LOGFILE}
#envpip=`realpath ~/anaconda3/envs/${project_name}/bin/pip`
envpip="pip"
#pip install -e .  &>> ${LOGFILE}
conda install -y pytest-timeout pytest &>> ${LOGFILE}

for k in `find -name "*requirement*.txt"`; do
  cat $k >> evalreqs.txt
  echo "" >> evalreqs.txt
done

${envpip} install astunparse

for s in `find -name "setup.py"`; do
    d=`dirname $s`
    python3 ../../tool/scripts/get_setup_extras.py `realpath $s`
    python3 $d/printExtra.py | grep "dep>" | cut -d">" -f2- >> evalreqs.txt    
done

cat evalreqs.txt | sort | uniq > allevalreqs.txt
log "Installing all requirements"

#cat allevalreqs.txt | xargs -n 1 ${envpip} install
${envpip} install -r allevalreqs.txt

log "Pip location: ${envpip}"
# check for extras
for t in `seq 1`; do
  log "Trial: $t"
  for s in `find -name "setup.py"`; do
    d=`dirname $s`
    log "Installing python package, dir: $d"
    ${envpip} install -e $d  &>> ${LOGFILE}
    ${envpip} install astunparse &>> ${LOGFILE}
  done
done

if [ -e ../../tool/scripts/extra_deps/${1}.txt ]; then
  ${envpip} install -r ../../tool/scripts/extra_deps/${1}.txt
fi


${envpip} freeze > ../evalreqs.txt
log "Installation done: ${project_name}"
conda deactivate
