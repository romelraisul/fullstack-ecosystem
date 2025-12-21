import time
import os
from logger import setup_logger
from validator import validate_file_path, validate_csv_format, validate_json_format, ValidationError

class DataProcessor:
    def __init__(self, output_dir="output"):
        self.logger = setup_logger(name="Processor")
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_file(self, file_path: str) -> bool:
        """
        Simulates processing a single file. 
        In a real scenario, this would extract data and transform it.
        """
        try:
            # 1. Validation Phase
            self.logger.debug(f"Validating {file_path}...")
            validate_file_path(file_path, allowed_extensions=['.csv', '.json', '.txt'])
            
            # Content-specific validation
            if file_path.endswith('.csv'):
                validate_csv_format(file_path, required_columns=['id', 'name'])
            elif file_path.endswith('.json'):
                validate_json_format(file_path)

            # 2. Processing Phase (Simulation)
            self.logger.info(f"Processing: {os.path.basename(file_path)}")
            
            # Simulate CPU work
            # time.sleep(0.01) # fast processing
            
            # 3. "Report Generation" (Simulation)
            # In a real app, we'd write to self.output_dir
            
            return True

        except ValidationError as ve:
            self.logger.error(f"Validation Failed for {file_path}: {ve}")
            return False
        except Exception as e:
            self.logger.critical(f"System Error processing {file_path}: {e}", exc_info=True)
            return False

    def process_batch(self, file_paths: list):
        """
        Processes a batch of files and calculates performance metrics.
        """
        total_files = len(file_paths)
        if total_files == 0:
            self.logger.warning("No files provided to process.")
            return

        self.logger.info(f"Starting batch processing for {total_files} files...")
        
        start_time = time.time()
        success_count = 0
        failure_count = 0

        for file_path in file_paths:
            if self.process_file(file_path):
                success_count += 1
            else:
                failure_count += 1

        end_time = time.time()
        duration = end_time - start_time
        
        # Avoid division by zero
        files_per_min = (total_files / duration) * 60 if duration > 0 else total_files * 60

        # Final Report
        print("\n" + "="*30)
        print("     PROCESSING SUMMARY     ")
        print("="*30)
        print(f"Total Files  : {total_files}")
        print(f"Successful   : {success_count}")
        print(f"Failed       : {failure_count}")
        print(f"Duration     : {duration:.2f} sec")
        print(f"Speed        : {files_per_min:.2f} files/min")
        print("="*30 + "\n")
        
        self.logger.info(f"Batch complete. Success: {success_count}, Failed: {failure_count}, Speed: {files_per_min:.2f} files/min")
