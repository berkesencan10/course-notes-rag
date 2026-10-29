import anthropic

client = anthropic.Anthropic()
msg = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=100,
    messages=[{"role": "user", "content": "Tek cümleyle merhaba de."}],
)
print(msg.content[0].text)
