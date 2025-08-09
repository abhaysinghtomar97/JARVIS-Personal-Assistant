from openai import OpenAI

client =OpenAI(
    api_key="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"
)

completion =client.chat.completions.create(
    model ="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content":"You are a virtual assistant named Jarvis assistant, skilled in genral Task like Alexa and google cloud."},
        {"role":"user", "content": command}
    ]
)
print(completion.choices[0].message)