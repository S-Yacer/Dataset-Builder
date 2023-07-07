import json
import argparse
import re
import os
from atomicwrites import atomic_write

# Function to format the prompt
def format_prompt(object, prompt_format, list_size=None, list_start=1):
    object = {**object, 'list_size': list_size, 'list_number': list_start}
    formatted_prompt = prompt_format.format(**object)
    return formatted_prompt

# Function to generate message data
# Function to generate message data
def main(args):
    # Initialize input data
    input_data = [{}]

    # Read input json file if provided
    if args.input_json:
        with open(args.input_json, 'r') as input_file:
            input_data = json.load(input_file)
    
    output_data = input_data
    messages = []    

    for i, obj in enumerate(output_data):
        obj['messages_id'] = str(i+1).zfill(5)
        obj['messages_list_size'] = args.list_size
        obj['messages_assistant_prompt'] = args.assistant_prompt
        obj['messages_complete'] = False
        
        # If list_size, calculate the list start position
        list_start = 1 + i * args.list_size if args.list_size else None

        # If next_prompt is not provided or it's the first object, use first_prompt
        if not args.next_prompt or i == 0:
            prompt = format_prompt(obj, args.first_prompt, args.list_size, list_start)
        else:
            prompt = format_prompt(obj, args.next_prompt, args.list_size, list_start)

        if args.assistant_prompt:
            assistant_prompt = args.assistant_prompt.format(**obj) # New line for formatting assistant_prompt
        else:
            assistant_prompt = ''

        # Append messages if input objects already contain them
        if 'messages' in obj:
            obj['messages'].extend([{'role':'user', 'content':prompt}, {'role':'assistant', 'content':assistant_prompt}])
        else:
            obj['messages'] = [{'role':'user', 'content':prompt}, {'role':'assistant', 'content':assistant_prompt}]
        messages.append(obj)                

    # Write to output json file
    with atomic_write(args.output_json, overwrite=True) as f:
        json.dump(output_data, f, indent=4)

    print(f"prompting: Successfully Output {args.output_json} with " + str(len(output_data)) + " entries.")


if __name__ == '__main__':
    #Argument Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-input_json", help="Input JSON file", type=str)
    parser.add_argument("-output_json", help="Output JSON file", type=str)
    parser.add_argument("-list_size", help="Number of expected list entries in response to generated prompt", type=int, default=0)
    parser.add_argument("-first_prompt", help="First generated prompt", type=str, required=True)
    parser.add_argument("-next_prompt", help="Next generated prompt", type=str)
    parser.add_argument("-assistant_prompt", help="Beginning of assistant message", type=str)
    args = parser.parse_args()

    # hack to remove new line escapes the shell tries to put in on parameters
    for arg in vars(args):
        value = getattr(args, arg)
        if isinstance(value, str):
            setattr(args, arg, value.replace('\\n', '\n'))     

    # Ensure input filename ends with .json
    if args.input_json and not args.input_json.endswith('.json'):
        args.input_json += '.json'

    # If output_json argument is not provided, use the input filename with modified suffix
    if args.input_json and not args.output_json:
        args.output_json = re.sub(r'_([^_]*)$', '_prompted', args.input_json) 

    # Ensure output filename ends with .json
    if not args.output_json.endswith('.json'):
        args.output_json += '.json'
    
    if args.input_json is not None:
        args.input_json = os.path.join('jsons', args.input_json)
    args.output_json = os.path.join('jsons', args.output_json)    
        
    main(args)
