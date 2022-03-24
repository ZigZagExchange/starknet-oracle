
echo "Killing ports..."
for ((a=5559; a<5570; a++)); do
    npx kill-port ${a}
done

