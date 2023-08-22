import argparse
import json
import os
import re
from atomicwrites import atomic_write

'''This script splits our data into either input or output only, this is useful when we want to generate
a series of prompts from one call and generate a series of responses on another call'''

# Keys that should be excluded when processing the input data
EXCLUDED_KEYS = {'messages', 'messages_id', 'messages_list_size', 'messages_complete', 'messages_assistant_prompt'}

def split_last_message(entry, split_on, new_key):
    # Extract the last message by the assistant from the list of messages
    last_message = next((msg for msg in reversed(entry['messages']) if msg['role'] == 'assistant'), None)
    # If there's no last message, return an empty list
    if not last_message:
        return []

    response_content = last_message['content']
    # Split the content into parts based on the provided delimiter
    parts = [part for part in response_content.split(split_on) if part]

    if entry.get('messages_list_size', 0) > 0:
        parts = [re.sub(r'^\d+\. ', '', part).strip() for part in parts]
    # Return a new list of entries, preserving the original keys (excluding some) and appending the split content
    return [{**{key: entry[key] for key in entry if key not in EXCLUDED_KEYS}, **{new_key: part}} for part in parts]

def main(args):
    with open(args.input_json, 'r') as f:
        input_data = json.load(f)

    output_data = []
    for entry in input_data:
        # warn and skip if entry is not complete
        if not entry.get('messages_complete', False):
            print(f"Warning: Entry with messages_id {entry.get('messages_id')} discarded.")
            continue
        
        # Split the last assistant message in the entry
        new_entries = split_last_message(entry, args.split_on, args.new_key)
        expected_size = entry.get('messages_list_size')

        # warn and skip if number of split parts do not match
        if expected_size is not None and len(new_entries) != expected_size:
            print(f"Warning: Entry with messages_id {entry.get('messages_id')} discarded.")
            continue
        
        # Add the new entries to the output data
        output_data.extend(new_entries)

    with atomic_write(args.output_json, overwrite=True) as f:
        json.dump(output_data, f, indent=4)

    print(f"split_response: Successfully Output {args.output_json} with {len(output_data)} entries.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split response content in JSON entries.')
    parser.add_argument('-input_json', required=True, help='Input JSON file')
    parser.add_argument('-output_json', default=None, help='Output JSON file')
    parser.add_argument('-split_on', default='\n', help='String to split the response content on')
    parser.add_argument('-new_key', required=True, help='New key to assign the split parts to')
    args = parser.parse_args()

    # Ensure input and output filenames end with .json
    args.input_json = args.input_json if args.input_json.endswith('.json') else args.input_json + '.json'
    args.output_json = args.output_json if (args.output_json and args.output_json.endswith('.json')) else re.sub(r'_([^_]*)$', '_split', args.input_json) + '.json'

    # Prepend 'jsons/' to the input and output JSON file paths
    args.input_json = os.path.join('jsons', args.input_json)
    args.output_json = os.path.join('jsons', args.output_json)

    main(args)
