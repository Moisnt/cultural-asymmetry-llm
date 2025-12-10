import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Create dummy data to reproduce
data = {
    'layer': list(range(10)),
    'ground_truth_prob': [0.1 * i for i in range(10)],
    'category': ['A'] * 5 + ['B'] * 5
}
df = pd.DataFrame(data)

print("DataFrame dtypes:")
print(df.dtypes)

try:
    # Workaround: Pass numpy arrays directly
    sns.lineplot(x=df['layer'].values, y=df['ground_truth_prob'].values, hue=df['category'].values)
    print("Plot success with values")
except Exception as e:
    print(f"Plot failed with values: {e}")
