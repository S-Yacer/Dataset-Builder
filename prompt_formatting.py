import json
import argparse
import re
import os
from atomicwrites import atomic_write

'''The aim of the script is to format our input into a format that is acceptable by chatcompletions API'''

# Formats the prompt using a given format, i.e adding placeholder objects
def format_prompt(obj, prompt_format, list_size=None, list_start=1):
    obj = {**obj, 'list_size': list_size, 'list_number': list_start}
    return prompt_format.format(**obj)

# Processes the filename by appending ".json" and ensures files are in "/jsons"
def process_filename(filename, default_suffix):
    if not filename.endswith('.json'):
        filename += '.json'
    return os.path.join('jsons', filename)

def main(args):
    # Initialize input data
    input_data = [{}]
    if args.input_json:
        with open(args.input_json, 'r') as input_file:
            input_data = json.load(input_file)

    # Loop over each data object and update its properties. 
    for i, obj in enumerate(input_data):
        obj.update({
            'messages_id': str(i + 1).zfill(5),
            'messages_list_size': args.list_size,
            'messages_assistant_prompt': args.assistant_prompt,
            'messages_complete': False
        })
        # If list_size is called, calculate list_size position
        list_start = 1 + i * args.list_size if args.list_size else None
        
        # Formatting the prompt and appending messages.
        prompt = format_prompt(obj, args.first_prompt if not args.next_prompt or i == 0 else args.next_prompt, args.list_size, list_start)
        assistant_prompt = args.assistant_prompt.format(**obj) if args.assistant_prompt else ''
        obj['messages'] = obj.get('messages', []) + [{'role': 'user', 'content': prompt}, {'role': 'assistant', 'content': assistant_prompt}]

    # Use atomic write to prevent data corruption
    with atomic_write(args.output_json, overwrite=True) as f:
        json.dump(input_data, f, indent=4)

    print(f"prompt_formatting: Successfully Output {args.output_json} with {len(input_data)} entries.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Define cli arguments.
    parser.add_argument("-input_json", help="Input JSON file", type=str)
    parser.add_argument("-output_json", help="Output JSON file", type=str)
    parser.add_argument("-list_size", help="Number of expected list entries in response", type=int, default=0)
    parser.add_argument("-first_prompt", help="First generated prompt", type=str, required=True)
    parser.add_argument("-next_prompt", help="Next generated prompt", type=str)
    parser.add_argument("-assistant_prompt", help="Beginning of assistant message", type=str)
    args = parser.parse_args()

    # Update string arguments
    for arg in vars(args):
        value = getattr(args, arg)
        if isinstance(value, str):
            setattr(args, arg, value.replace('\\n', '\n'))

    # Process filenames and handle suffixes
    if args.input_json:
        args.input_json = process_filename(args.input_json, '_prompted')
    args.output_json = process_filename(args.output_json if args.output_json else re.sub(r'_([^_]*)$', '_prompted', args.input_json), '')
    
    main(args)