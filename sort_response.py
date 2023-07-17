import argparse
import json
import os
import re

def extract_id(json_data):
    try:
        return int(json_data['messages_id'])
    except KeyError:
        return 0

def main(input_json, output_json):
    # Open the JSON file
    with open(input_json, 'r') as f:
        data = json.load(f)

    # Filter out elements where 'messages_complete' is False
    data = [item for item in data if item.get('messages_complete', False)]

    # Sort the data based on the 'messages_id'
    data.sort(key=extract_id)

    # Write the sorted data back into a new JSON file
    with open(output_json, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"sort_response: Successfully output {output_json} with {len(data)} entries.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-input_json', required=True, help='Input JSON file')
    parser.add_argument('-output_json', required=True, help='Output JSON file')
    args = parser.parse_args()

    # Ensure input filename ends with .json
    if args.input_json and not args.input_json.endswith('.json'):
        args.input_json += '.json'

    # If output_json argument is not provided, use the input filename with modified suffix
    if args.input_json and not args.output_json:
        args.output_json = re.sub(r'_([^_]*)$', '_sorted', args.input_json) 

    # Ensure output filename ends with .json
    if not args.output_json.endswith('.json'):
        args.output_json += '.json'

    # prepend 'jsons/' to the input and output JSON file paths
    args.input_json = os.path.join('jsons', args.input_json)
    args.output_json = os.path.join('jsons', args.output_json)   

    main(args.input_json, args.output_json)
