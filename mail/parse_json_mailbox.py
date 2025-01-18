import concurrent.futures
import json
import os

def parse_file(file_path):
    with open(file_path, 'r') as file:
        return json.loads(file.read())

def parse_mailbox(_dir):
    total_items = []
    files = [f'{_dir}/{f}' for f in os.listdir(_dir)]
    
    # read files currently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(parse_file, files)
        for i, result in enumerate(results):
            print(i, end=' ')
            total_items.extend(result)
    
    return total_items