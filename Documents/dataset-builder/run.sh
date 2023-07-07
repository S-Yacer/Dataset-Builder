#!/bin/bash

## Phase I: Generate coding questions
py prompting.py -output_json coding_questions_prompted -list_size 1000 \
    -first_prompt "Please generate {list_size} unique and interesting coding questions that span a variety of topics." \
    -assistant_prompt "1. " 
py askgpt.py -input_json coding_questions_prompted -resume -model gpt-4
py trim_response.py -input_json coding_questions_asked -trim_blanks
py split_response.py -input_json coding_questions_trimmed -new_key "question"

## Phase II: Generate GPT-4 answers for the coding questions
py prompting.py -input_json coding_questions_split -output_json coding_answers_prompted -list_size 1000 \
    -first_prompt "Here is a coding question: '{question}'. How would you solve it?" \
    -assistant_prompt "Solution: " 
py askgpt.py -input_json coding_answers_prompted -temperature 0.1 -top_p 0.9 -presence_penalty 0.4 -frequency_penalty 0.4 -model gpt-4 -resume 
py trim_response.py -input_json coding_answers_asked -trim_blanks -trim_assistant_prompt
py split_response.py -input_json coding_answers_trimmed -new_key "answer"

## Phase III: Create the final dataset
py prompting.py -input_json coding_answers_split -output_json Coding_Conversations_v1_raw \
    -first_prompt "You are an AI assistant. User will you give you a task. Your goal is to complete the task as faithfully as you can. While performing the task think step-by-step and justify your steps\n\nQuestion: '{question}'" \
    -assistant_prompt "{answer}"
py formatting.py -input_json Coding_Conversations_v1_raw -format Alpaca

