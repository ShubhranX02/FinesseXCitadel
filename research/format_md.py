import pandas as pd
df = pd.read_csv('results.csv') if __import__('os').path.exists('results.csv') else None
# Wait, I didn't save it to csv. I'll modify the previous script to generate standard output.
