_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

export PYTHONPATH=$_DIR/source/python:$PYTHONPATH
