echo "Starting subscribers..."
for ((a=0; a<5; a++)); do
    echo "Starting subscriber ${a}..."
    python ./pub_sub_node.py ${a} &
done
echo "Starting publisher..."
python ./starter.py
 