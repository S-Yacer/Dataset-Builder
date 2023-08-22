import json
import argparse

'''The purpose of this script is to format our RLHF data into a chosen/ rejected dataset
by combining and pre-processing the chosen and rejected json files.
An example result can be found: /jsons/final_rlhf.json'''

def combine_jsons(file1, file2, output_file):
    with open(file1, 'r') as f1:
        data1 = json.load(f1)

    with open(file2, 'r') as f2:
        data2 = json.load(f2)

    # Combine the data
    combined_data = []
    for d1, d2 in zip(data1, data2):
        d = {}

        # Split the instruction into system and user parts
        full_instruction = d1.get('messages')[0].get('content', '')
        split_instruction = full_instruction.split('\n \n\n## USER INSTRUCTION:')
        system_instruction = split_instruction[0].strip().replace("## SYSTEM INSTRUCTION:\n", "") if len(split_instruction) > 1 else ''
        user_instruction = split_instruction[1].strip() if len(split_instruction) > 1 else ''

        # Create chosen feature
        assistant_response1 = d1.get('messages')[1].get('content', '') if len(d1.get('messages')) > 1 else ''
        d['chosen'] = system_instruction + ". " + "### Instruction: \n\n" + user_instruction + "### Response: " + assistant_response1

        # Create rejected feature
        assistant_response2 = d2.get('messages')[1].get('content', '') if len(d2.get('messages')) > 1 else ''
        d['rejected'] = system_instruction + ". " + "### Instruction: \n\n" + user_instruction + "### Response: " + assistant_response2

        combined_data.append(d)

    # Save combined data as a new JSON file
    with open(output_file, 'w') as outfile:
        json.dump(combined_data, outfile, indent=2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine two JSON files into a single one with specific formatting.')
    parser.add_argument('--file1', required=True, help='First input JSON file.')
    parser.add_argument('--file2', required=True, help='Second input JSON file.')
    parser.add_argument('--output', default='final_rlhf.json', help='Output JSON file.')
    
    args = parser.parse_args()

    combine_jsons(args.file1, args.file2, args.output)
