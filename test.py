from anthropic import Anthropic

client = Anthropic(
    api_key="sk-trollllm-f53d3e35702a7b7c95a2c54fb808750c368c5bfae7637396558bad04cfba5819",
    base_url="https://chat.trollllm.xyz" # Ghi đè đường dẫn gốc của Anthropic
)

message = client.messages.create(
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Chào Claude, bạn khỏe không?"}
    ],
    model="claude-opus-4.7",
)
print(message.content)