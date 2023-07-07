import os
import openai
import json
import time
import argparse
import re
from atomicwrites import atomic_write
import requests  

def main(args):
    openai.api_key = args.api_key
    openai.api_base = args.api_url

    if args.resume:
        if os.path.isfile(args.output_json):
            print(f"askgpt: Existing {args.output_json} file found, attempting to resume...")
            args.input_json = args.output_json

    with open(args.input_json, 'r') as input_file:
        input_data = json.load(input_file)

    messages = []
    output_data = input_data

    for i, entry in enumerate(output_data):
        if entry.get('messages_complete') == True:
            continue
        
        print("************************************************")
        print("askgpt: Processing messages_id "+ str(entry['messages_id']) + " (" + str(i+1) + "/" + str(len(output_data)) + ")")    
        
        if args.include_chat_history:
            messages += entry['messages']
        else:
            messages = entry['messages']

        while len(messages) > args.max_chat_history:
            messages.pop(0);messages.pop(0)

        while entry.get('messages_complete') != True:
            try:            
                userPrompt = (messages[-2]['content'])
                assistantPrompt = (messages[-1]['content'])
                print("------------------------------------------------")
                print("## USER PROMPT:\n" + userPrompt)
                if assistantPrompt != '':
                    print("\n## ASSISTANT PROMPT:\n" + assistantPrompt)
                
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

                first_5_words = ' '.join(userPrompt.split()[:5])
                if first_5_words in assistantResponse:
                    print("Failed attempt: assistantResponse contains the first 5 words of userPrompt.")
                    print("Retrying in 15 seconds...")
                    time.sleep(15)
                    continue 
                
                if assistantResponse.startswith(assistantPrompt):
                    assistantResponse = assistantResponse[len(assistantPrompt):]
                
                messages[-1]['content'] += assistantResponse
                print("\n## ASSISTANT RESPONSE:\n" + (messages[-1]['content']))                
                entry['messages_complete'] = True
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
    parser.add_argument("-include_chat_history", help="Include chat history in subsequent messages", action='store_true')
    parser.add_argument("-max_chat_history", help="Maximum number of elements to keep in chat_history", type=int, default=10)
    parser.add_argument("-resume", help="Resume processing using the output file as the input file", action='store_true')
    
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
