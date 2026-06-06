import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
from pathlib import Path

def render_table_to_image(csv_path, output_path):
    print(f"Rendering {csv_path} to {output_path}...")
    try:
        # Check if the first column is an index column (starts empty)
        # We can just read and drop an Unnamed: 0 if it exists
        df = pd.read_csv(csv_path)
        if df.columns[0].startswith("Unnamed"):
            df = pd.read_csv(csv_path, index_col=0)
            # Reset index so we can show it as a column in the image
            df.reset_index(inplace=True)
            df.rename(columns={'index': ''}, inplace=True)

        # For very large tables, truncate them to avoid giant unreadable images
        if len(df) > 50:
            df = df.head(50)
            print(f"Truncated {csv_path} to 50 rows for image rendering.")
            
        fig, ax = plt.subplots()
        # hide axes
        fig.patch.set_visible(False)
        ax.axis('off')
        ax.axis('tight')

        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
        
        # Adjust font size and layout based on the number of columns and rows
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.8, 1.8)  # Increased from 1.2 to 1.8 for larger slots
        
        # Determine figure size
        num_cols = len(df.columns)
        num_rows = len(df)
        
        fig_width = max(num_cols * 2.0, 8)    # Increased width multiplier
        fig_height = max(num_rows * 0.6, 4)   # Increased height multiplier
        fig.set_size_inches(fig_width, fig_height)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"Success: {output_path}")
    except Exception as e:
        print(f"Failed to render {csv_path}: {e}")

folders = [
    r"c:\Users\danie\My Drive\ArchAware-PDDL-Configurator\analysis\output\cross_stage\1_Global_IPC_Score\tables\Configuration_Sensitivity",
    r"c:\Users\danie\My Drive\ArchAware-PDDL-Configurator\analysis\output\cross_stage\1_Global_IPC_Score\tables\Simulated_Competition"
]

for folder in folders:
    print(f"Processing folder: {folder}")
    csv_files = glob.glob(os.path.join(folder, "*.csv"))
    for csv_file in csv_files:
        base_name = os.path.basename(csv_file)
        name_no_ext = os.path.splitext(base_name)[0]
        # output in the same folder with .png extension
        output_file = os.path.join(folder, f"{name_no_ext}.png")
        render_table_to_image(csv_file, output_file)

print("Done.")
