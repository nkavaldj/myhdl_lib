X=$PYTHONPATH
export PYTHONPATH=$(pwd)

for f in examples/*.py; do python "$f"; done

export PYTHONPATH=$X