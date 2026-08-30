import os

script_path = "research/generate_modern_pdf.py"
with open(script_path, "r") as f:
    content = f.read()

old_str = "Strategy Arithmetic Ann = 28.75%, Benchmark Arithmetic Ann = 15.81%, Risk-Free = 6.0%. Thus, Alpha = (28.75% - 6.0%) - 1.01 * (15.81% - 6.0%) = 12.8%"
new_str = "Strategy Arithmetic Ann = 28.75%, Benchmark Arithmetic Ann = 15.81%, Risk-Free = 0.0% (per rules). Thus, Alpha = 28.75% - 1.01 * 15.81% = 12.8%"

content = content.replace(old_str, new_str)

with open(script_path, "w") as f:
    f.write(content)
