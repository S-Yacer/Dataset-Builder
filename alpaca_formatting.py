import json
import re
import os
import argparse
from atomicwrites import atomic_write

'''This script formats our data into the most common dataset format called alpaca:
it contains 3 features: instruction/ input/ output or system prompt/ instruction/ output'''

def alpaca_format(data):
    # Format data in alpaca format: system, instruction and output
    formatted_data = []
    for entry in data:
        new_entry = {}
        first_message_content = entry["messages"][0]["content"].split('## SYSTEM INSTRUCTION:')
        system_instruction = first_message_content[1].split('## USER INSTRUCTION:')[0].strip() if len(first_message_content) > 1 else ""
        user_instruction = first_message_content[1].split('## USER INSTRUCTION:')[1].strip() if len(first_message_content) > 1 else ""
        new_entry["instruction"] = system_instruction
        new_entry["input"] = user_instruction
        new_entry["output"] = entry["messages"][1]["content"]
        # Append entries
        formatted_data.append(new_entry)
    return formatted_data

def main(args):
    with open(args.input_json, 'r') as f:
        data = json.load(f)

    formatted_data = alpaca_format(data)

    with atomic_write(args.output_json, overwrite=True) as f:
        json.dump(formatted_data, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Conform JSON data to Alpaca format')
    parser.add_argument('-input_json', required=True, help='Input JSON file')
    parser.add_argument('-output_json', help='Output JSON file')
    args = parser.parse_args()

    # Remove new lines shell tries to add
    for arg in vars(args):
        value = getattr(args, arg)
        if isinstance(value, str):
            setattr(args, arg, value.replace('\\n', '\n'))

    # Ensure input file with .json
    if args.input_json and not args.input_json.endswith('.json'):
        args.input_json += '.json'

    # if output_json is none:
    if args.input_json and not args.output_json:
        args.output_json = re.sub(r'_([^_]*)$', '_alpaca', args.input_json)

    # Ensure output file with .json
    if not args.output_json.endswith('.json'):
        args.output_json += '.json'

    # save to ./jsons
    args.input_json = os.path.join('jsons', args.input_json)
    args.output_json = os.path.join('jsons', args.output_json)

    main(args)
