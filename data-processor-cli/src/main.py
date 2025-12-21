import argparse
import os
import glob
import sys
import random
import csv

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processor import DataProcessor

def generate_sample_data(count=10, directory="sample_data"):
    """Generates dummy CSV files for performance testing."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    print(f"Generating {count} sample files in '{directory}'...")
    for i in range(count):
        filename = os.path.join(directory, f"data_{i}.csv")
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'value', 'status']) # Header
            for _ in range(50): # 50 rows per file
                writer.writerow([
                    random.randint(1000, 9999), 
                    f"Item-{random.randint(1,100)}", 
                    random.random() * 100,
                    random.choice(['Active', 'Inactive', 'Pending'])
                ])
    print("Generation complete.")

def main():
    parser = argparse.ArgumentParser(description="High-Performance Data Processor CLI")
    
    # Mode selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input-dir', '-i', help="Directory containing files to process")
    group.add_argument('--generate-samples', '-g', type=int, metavar='N', help="Generate N sample CSV files for testing")
    
    args = parser.parse_args()

    processor = DataProcessor()

    if args.generate_samples:
        generate_sample_data(args.generate_samples)
        print(f"\nRun the tool again with: python src/main.py -i sample_data")
        return

    if args.input_dir:
        input_path = os.path.abspath(args.input_dir)
        if not os.path.exists(input_path):
            print(f"Error: Directory '{input_path}' does not exist.")
            return

        # Gather files (recursive search could be added here)
        # For now, just grab direct children
        files = []
        for ext in ['*.csv', '*.json', '*.txt']:
            files.extend(glob.glob(os.path.join(input_path, ext)))
        
        if not files:
            print(f"No compatible files (.csv, .json, .txt) found in {input_path}")
            return

        processor.process_batch(files)

if __name__ == "__main__":
    main()
