RED='\033[0;31m'
NC='\033[0m'
PX4_DIR=./Dependencies/PX4-Autopilot
echo $PX4_DIR

echo "[🍴] Fethcing CAELUS fork for PX4-Autopilot"
if [ ! -d $PX4_DIR ]; then
    git clone https://github.com/strathclyde-artificial-intelligence/PX4-Autopilot $PX4_DIR --recursive
fi

echo "[🚚] Installing PX4-Autpilot python dependencies"
pip3 install -r px4_python_requirements.txt
(cd $PX4_DIR; make)

echo -e "Make sure to issue '${RED}export PX4_ROOT_FOLDER=$PX4_DIR${NC}' before starting the digital twin."