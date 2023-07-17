import os
import openai
import json
import time
import argparse
import re
from atomicwrites import atomic_write
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import threading
import random

next_message_id = 1

def extract_info(prompt):
    match = re.search(r"\*\*Error Nature and Language:\*\* The error is (?:an|a) '(.+?)' in '(.+?)'.", prompt)
    if match:
        error = match.group(1)
        language = match.group(2)
        return language, error
    else:
        return None, None
    
def process_single_entry(i, rep, entry, args, languages_errors_used):
    global next_message_id
    print_lock = threading.Lock()
    thread_id = threading.get_ident()

    with print_lock:
        print(f"threaded_askgpt: [Thread-{thread_id}] messages_id {entry['messages_id']}_{rep} PROCESSING")

    new_entry = entry.copy()
    new_entry['messages_id'] = f"{str(next_message_id).zfill(5)}"
    next_message_id += 1 
    messages = list(new_entry['messages'])

    while new_entry.get('messages_complete') != True:
        try:
            sleep_time = random.uniform(1, 5)
            time.sleep(sleep_time)

            if messages[-1]['role'] == 'assistant' and messages[-1]['content'] == '':
                messages = messages[:-1]

            userPrompt = (messages[-1]['content'])
            if args.debugging_history:
                userPrompt += f'Also, do not repeat a combination of languages and error types that has already been generated. The goal is to create a diverse dataset of different languages and error types. Lastly, it is important you do not repeat a combo of languages and error types that has already been generated, here are the following existing language and error type combinations that you must not generate within your example, but you are at will to generate a different combination pair: [{", ".join(languages_errors_used)}].'
            #print("------------------------------------------------")
            #print("## USER PROMPT:\n" + userPrompt)

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

            if assistantResponse.strip() != '':   # Check if the assistant's content is not empty before adding
                messages.append({
                    "role": "assistant",
                    "content": assistantResponse
                })
            new_entry['messages'] = messages
            new_entry['messages_complete'] = True
            
            if args.debugging_history:
                language, error_type = extract_info(assistantResponse)
                if language and error_type:
                    languages_errors_used.append(f"{language} - {error_type}")
                    with open('languages_errors_used.txt', 'a') as file:
                        file.write("%s\n" % languages_errors_used[-1])

        except Exception as e:
            print(f"threaded_askgpt: [Thread-{thread_id}] messages_id {entry['messages_id']}_{rep} ERROR: {e} (Retrying in 5-15 seconds...)")
            error_sleep_time = random.uniform(5, 15)
            time.sleep(error_sleep_time)
    with print_lock:
        print(f"threaded_askgpt: [Thread-{thread_id}] messages_id {entry['messages_id']}_{rep} COMPLETE ")
    
    return new_entry

def main(args):
    openai.api_key = args.api_key
    openai.api_base = args.api_url

    if args.resume:
        if os.path.isfile(args.output_json):
            print(f"threaded_askgpt: Existing {args.output_json} file found, attempting to resume...")
            args.input_json = args.output_json

    with open(args.input_json, 'r') as input_file:
        input_data = json.load(input_file)

    output_data = input_data
    incomplete_entries = [i for i, entry in enumerate(output_data) if entry.get('messages_complete') != True]

    languages_errors_used = []
    if args.debugging_history:
        if os.path.exists('languages_errors_used.txt'):
            with open('languages_errors_used.txt', 'r') as file:
                languages_errors_used = [line.rstrip() for line in file]

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_threads) as executor:
        futures = []
        for i in incomplete_entries:
            for rep in range(args.num_responses):
                entry = output_data[i]
                futures.append(executor.submit(process_single_entry, i, rep, entry, args, languages_errors_used))

        for future in concurrent.futures.as_completed(futures):
            new_entry = future.result()
            output_data.append(new_entry)
            print(f"threaded_askgpt: [MAIN] writing to {args.output_json}")
            with atomic_write(args.output_json, overwrite=True) as f:
                json.dump(output_data, f, indent=4)
    print(f"threaded_askgpt: Successfully Completed {args.output_json} with " + str(len(output_data)) + " entries.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OpenAI chat bot')
    parser.add_argument("-input_json", help="Input JSON file", type=str, required=True)
    parser.add_argument("-output_json", help="Output JSON file", type=str)
    parser.add_argument("-include_chat_history", help="Include chat history in subsequent messages", action='store_true')
    parser.add_argument("-max_chat_history", help="Maximum number of elements to keep in chat_history", type=int, default=10)
    parser.add_argument("-resume", help="Resume processing using the output file as the input file", action='store_true')
    parser.add_argument("-max_threads", help="Maximum number of threads", type=int, default=1)
    parser.add_argument("-debugging_history", help="Keep history of the languages and errors used", action='store_true')
    parser.add_argument("-num_responses", help="Number of responses per prompt", type=int, default=1)
    
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
