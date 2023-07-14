import os
import openai
import json
import time
import argparse
import re
from atomicwrites import atomic_write
import requests  

def extract_info(prompt):
    match = re.search(r"\*\*Error Nature and Language:\*\* The error is a '(.+?)' in '(.+?)'.", prompt)
    if match:
        error = match.group(1)
        language = match.group(2)
        return language, error
    else:
        return None, None

def main(args):
    openai.api_key = args.api_key
    openai.api_base = args.api_url
    #languages_used = []
    #errors_encountered = []
    languages_errors_used = []

    if args.resume:
        if os.path.isfile(args.output_json):
            print(f"askgpt: Existing {args.output_json} file found, attempting to resume...")
            args.input_json = args.output_json

    with open(args.input_json, 'r') as input_file:
        input_data = json.load(input_file)

    output_data = []

    for i, entry in enumerate(input_data):
        messages = entry['messages'].copy()

        for rep in range(args.repeat_prompt):  # Repeat the prompt n times
            print("************************************************")
            new_messages_id = str(int(entry['messages_id']) + rep).zfill(4)
            print("askgpt: Processing messages_id "+ new_messages_id + " (" + str(i*args.repeat_prompt+rep+1) + "/" + str(len(input_data)*args.repeat_prompt) + ")")    
            
            if args.keep_history:
                messages += entry['messages']
            else:
                messages = entry['messages']
            
            if messages[-1]['role'] == 'assistant' and messages[-1]['content'] == '':
                messages = messages[:-1]  # Remove the last message if it's from the assistant and it's empty
            
            userPrompt = (messages[-1]['content'])
            if args.debugging_history:
                userPrompt += f' [{", ".join(languages_errors_used)}].'
            print("------------------------------------------------")
            print("## USER PROMPT:\n" + userPrompt)
            
            try:
                if args.debugging_history:
                    #print(f"\nLanguages used so far: {languages_used}")
                    #print(f"Errors encountered so far: {errors_encountered}")
                    print(f"\nLanguage-Error combinations used so far: {languages_errors_used}")
                    
                response = openai.ChatCompletion.create(
                    model=args.model,
                    messages=messages,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    presence_penalty=args.presence_penalty,
                    frequency_penalty=args.frequency_penalty,
                    max_tokens=args.max_tokens
                )

                assistantResponse = response.choices[0].message["content"]
                print("\n## ASSISTANT RESPONSE:\n" + assistantResponse)

                # Extract language and error from assistant's response
                if args.debugging_history:
                    language, error_type = extract_info(assistantResponse)
                    if language and error_type:
                        #languages_used.append(language)
                        #errors_encountered.append(error_type)
                        languages_errors_used.append(f"{language} - {error_type}")
                        with open('languages_errors_used.txt', 'w') as file:
                            for item in languages_errors_used:
                                file.write("%s\n" % item)

                first_5_words = ' '.join(userPrompt.split()[:5])
                if first_5_words in assistantResponse:
                    print("Failed attempt: assistantResponse contains the first 5 words of userPrompt.")
                    print("Retrying in 15 seconds...")
                    time.sleep(15)
                    continue
                
                messages.append({
                    'role': 'assistant',
                    'content': assistantResponse
                })
                
                new_entry = entry.copy()
                new_entry['messages_id'] = new_messages_id
                new_entry['messages'] = [messages[-2], messages[-1]]
                new_entry['messages_complete'] = True
                
                output_data.append(new_entry)
                
                with atomic_write(args.output_json, overwrite=True) as f:
                    json.dump(output_data, f, indent=4)
                
                time.sleep(1)
            except requests.exceptions.Timeout:   # Catch timeout errors
                print("Timeout occurred. Retrying in 15 seconds...")
                time.sleep(15)
            except Exception as e:  # All other errors
                print(f"\nAn error occurred: {e}")
                print("Retrying in 15 seconds...")
                time.sleep(15)

    print("------------------------------------------------")
    print(f"askgpt: Successfully Completed {args.output_json} with " + str(len(output_data)) + " entries.")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OpenAI chat bot')
    parser.add_argument("-input_json", help="Input JSON file", type=str, required=True)
    parser.add_argument("-output_json", help="Output JSON file", type=str)
    parser.add_argument("-repeat_prompt", help="Number of times to repeat each user prompt", type=int, default=1)
    parser.add_argument("-resume", help="Resume processing using the output file as the input file", action='store_true')
    parser.add_argument("-keep_history", help="Keep history of the n-1 reply", action='store_true')
    parser.add_argument("-debugging_history", help="Keep history of the languages and errors used", action='store_true')

    parser.add_argument("-api_key", help="OpenAI API key", type=str, default=os.getenv('OPENAI_API_KEY')) 
    parser.add_argument("-api_url", help="OpenAI API URL", type=str, default=os.getenv('OPENAI_API_URL')) 
    parser.add_argument("-model", help="OpenAI model to use", type=str, default="gpt-3.5-turbo")
    parser.add_argument("-temperature", type=float, default=None)
    parser.add_argument("-top_p", type=float, default=None)
    parser.add_argument("-presence_penalty", type=float, default=0)
    parser.add_argument("-frequency_penalty", type=float, default=0)
    parser.add_argument("-max_tokens", type=int, default=1024)
    args = parser.parse_args()

    for arg in vars(args):
        value = getattr(args, arg)
        if isinstance(value, str):
            setattr(args, arg, value.replace('\\n', '\n'))

    if args.input_json and not args.input_json.endswith('.json'):
        args.input_json += '.json'

    if args.input_json and not args.output_json:
        args.output_json = re.sub(r'_([^_]*)$', '_asked', args.input_json) 

    if not args.output_json.endswith('.json'):
        args.output_json += '.json'

    args.input_json = os.path.join('jsons', args.input_json)
    args.output_json = os.path.join('jsons', args.output_json)    
    
    main(args)
