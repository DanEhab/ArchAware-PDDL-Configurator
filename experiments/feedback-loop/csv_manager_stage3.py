import os
import csv
import threading

# Global lock for thread-safe CSV writes
csv_lock = threading.Lock()

def log_to_csv(csv_path, row_data):
    """
    Appends a row of data to the specified CSV file.
    Writes the header if the file does not exist.
    """
    file_exists = os.path.isfile(csv_path)
    with csv_lock:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)
