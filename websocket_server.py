import asyncio
import websockets
import uuid
import json

# I'm maintaining all active connections in this dictionary
clients = {}
# I'm maintaining all active users in this dictionary
users = {}
# The current editor content is maintained here.
editor_content = None
# User activity history.
user_activity = []

# Event types
types_def = {
    "USER_EVENT": "userevent",
    "CONTENT_CHANGE": "contentchange"
}

def broadcast_message(message):
    # We are sending the current data to all connected clients
    data = json.dumps(message)
    for client in clients.values():
        asyncio.create_task(client.send(data))

async def handle_message(message, user_id):
    data_from_client = json.loads(message)
    json_message = {"type": data_from_client["type"]}
    if data_from_client["type"] == types_def["USER_EVENT"]:
        users[user_id] = data_from_client
        user_activity.append(f"{data_from_client['username']} joined to edit the document")
        json_message["data"] = {"users": users, "userActivity": user_activity}
    elif data_from_client["type"] == types_def["CONTENT_CHANGE"]:
        global editor_content
        editor_content = data_from_client["content"]
        json_message["data"] = {"editorContent": editor_content, "userActivity": user_activity}
    broadcast_message(json_message)

async def handle_disconnect(user_id):
    print(f"{user_id} disconnected.")
    json_message = {"type": types_def["USER_EVENT"]}
    username = users.get(user_id, {}).get("username", user_id)
    user_activity.append(f"{username} left the document")
    json_message["data"] = {"users": users, "userActivity": user_activity}
    del clients[user_id]
    del users[user_id]
    broadcast_message(json_message)

async def handle_connection(websocket, path):
    # Generate a unique code for every user
    user_id = str(uuid.uuid4())
    print(f"Received a new connection from {user_id}")
    
    # Store the new connection and handle messages
    clients[user_id] = websocket
    print(f"{user_id} connected.")
    try:
        async for message in websocket:
            await handle_message(message, user_id)
    except websockets.exceptions.ConnectionClosedError:
        pass
    finally:
        await handle_disconnect(user_id)

async def main():
    # Spinning the WebSocket server.
    port = 8000
    async with websockets.serve(handle_connection, "localhost", port):
        print(f"WebSocket server is running on port {port}")
        await asyncio.Future()  # Keep the server running

if __name__ == "__main__":
    asyncio.run(main())
