import stream_chat

"""
# GetStream.Io
STREAM_API_KEY=t3zrhpnqru9p
STREAM_API_SECRET=jbf54qyurd8kjfxdu9exa9vmxcwzhjpb3enwj84nkvxb46e63ze26tuvanaha38h

"""

if __name__ == "__main__":
    user_1 = "aa"
    user_2 = "cc"
    user_3 = "dd"

    stream = stream_chat.StreamChat(
        api_key="t3zrhpnqru9p",
        api_secret="jbf54qyurd8kjfxdu9exa9vmxcwzhjpb3enwj84nkvxb46e63ze26tuvanaha38h",
    )

    stream.upsert_user({"id": user_1, "role": "user"})
    stream.upsert_user({"id": user_2, "role": "user"})

    token1 = stream.create_token(user_id=str(user_1))
    print(token1)
    token2 = stream.create_token(user_id=str(user_2))
    print(token2)
    token3 = stream.create_token(user_id=str(user_3))
    print(token3)

    channel = stream.channel(
        "test-chat", None, data=dict(members=[user_1, user_2], created_by_id=user_1)
    )
    # Note: query method creates a channel
    ch = channel.query()
    print(ch)
