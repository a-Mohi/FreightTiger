import hashlib
import subprocess
import sys

hashes = []
for i in range(3):
    subprocess.run([sys.executable, "main.py"], check=True, stdout=subprocess.DEVNULL)
    hashes.append(hashlib.sha256(open("outputs/output.csv", "rb").read()).hexdigest())
    print(f"run {i + 1}: {hashes[-1][:16]}")
print("IDENTICAL on all 3 runs" if len(set(hashes)) == 1 else "DIFFERENT - something is random!")
