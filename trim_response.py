import argparse
import json
import os
from atomicwrites import atomic_write
import re

'''The following script trims and cleans the messages any unnecessary detail'''

def trim_response_content(response_content, entry, args):
    # Clean start and end list
    list_size = entry.get('messages_list_size', 0)
    if list_size > 0:
        # Trimming before first item in list
        response_content = re.sub(r'^.*?1\. ', '1. ', response_content, flags=re.DOTALL)
        response_content = re.sub(r'(\n{list_number}\..*?)\n.*$'.format(list_number=list_size), r'\1', response_content, flags=re.DOTALL)

    # Split responses individually
    lines = response_content.split('\n')
    non_blank_lines = [i for i, line in enumerate(lines) if line.strip() != '']

    # Trim lines from the end if args
    if args.trim_lines_from_end > 0 and len(non_blank_lines) > args.trim_lines_from_end:
        last_kept_line_index = non_blank_lines[-args.trim_lines_from_end-1]
        lines = lines[:last_kept_line_index + 1]

    # Trim lines from the start if args
    if args.trim_lines_from_start > 0 and len(non_blank_lines) > args.trim_lines_from_start:
        first_kept_line_index = non_blank_lines[args.trim_lines_from_start]
        lines = lines[first_kept_line_index:]
    
    # Keep lines only up to the line that starts with a specified string in args
    if args.last_line_starts_with:
        try:
            start_str = args.last_line_starts_with.format(**entry).lower()
            for i in reversed(range(len(lines))):
                if lines[i].strip() and lines[i].lower().startswith(start_str):
                    lines = lines[:i+1]
                    break
        except KeyError as e:
            print(f"Warning: Property {str(e)} not found in the entry. Skipping 'last_line_starts_with' for this entry.")

    # Return the processed lines
    return '\n'.join(lines).strip() if args.trim_blanks else '\n'.join(lines)

def main(args):
    with open(args.input_json, 'r') as f:
        input_data = json.load(f)

    for entry in input_data:
        # Check for the presence of necessary keys and skip entries without them
        if 'messages' not in entry or 'messages_assistant_prompt' not in entry:
            print(f"Warning: Entry does not have 'messages' or 'messages_assistant_prompt'. Skipping this entry.")
            continue
        
        # Get the last assistant's message
        last_message = next((message for message in reversed(entry['messages']) if message['role'] == 'assistant'), None)
        if not last_message:
            print(f"Warning: No assistant message found in the entry. Skipping this entry.")
            continue
        
        # Trim the content of the last message
        last_message['content'] = trim_response_content(last_message['content'], entry, args)
        # Remove the prompt content from the beginning of the message if args
        if args.trim_assistant_prompt and last_message['content'].startswith(entry['messages_assistant_prompt']):
            last_message['content'] = last_message['content'][len(entry['messages_assistant_prompt']):]

    # Write to file...
    with atomic_write(args.output_json, overwrite=True) as f:
        json.dump(input_data, f, indent=4)

    print(f"trim_response: Successfully Output {args.output_json} with {len(input_data)} entries.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Trim lines in JSON responses.')
    parser.add_argument('-input_json', required=True, help='Input JSON file')
    parser.add_argument('-output_json', default=None, help='Output JSON file')
    parser.add_argument('-trim_lines_from_start', type=int, default=0)
    parser.add_argument('-trim_lines_from_end', type=int, default=0)
    parser.add_argument('-trim_assistant_prompt', action='store_true')
    parser.add_argument('-trim_blanks', action='store_true')
    parser.add_argument('-last_line_starts_with', default="")
    args = parser.parse_args()

    args.input_json = args.input_json if args.input_json.endswith('.json') else args.input_json + '.json'
    args.output_json = args.output_json or re.sub(r'_([^_]*)$', '_trimmed', args.input_json)
    if not args.output_json.endswith('.json'):
        args.output_json += '.json'

    args.input_json = os.path.join('jsons', args.input_json)
    args.output_json = os.path.join('jsons', args.output_json)

    main(args)
