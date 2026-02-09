#!/usr/bin/env python3
"""
Secure Multi-User Messaging System with Mnemonic Authentication
Chat application with threaded conversations
"""

import hashlib
import secrets
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# Simple wordlist for mnemonic generation
WORDLIST = [
    "apple", "banana", "cherry", "dragon", "elephant", "forest", "guitar", "house",
    "island", "jungle", "kitchen", "lemon", "mountain", "notebook", "ocean", "piano",
    "queen", "river", "sunset", "tiger", "umbrella", "volcano", "window", "xylophone",
    "yellow", "zebra", "anchor", "bridge", "castle", "desert", "engine", "flower",
    "garden", "harbor", "indent", "jacket", "kitten", "ladder", "marble", "needle",
    "orange", "pocket", "quartz", "rocket", "socket", "temple", "upward", "vessel",
    "wallet", "xenon", "yogurt", "zephyr", "arrow", "bottle", "candle", "dollar",
    "eagle", "feather", "globe", "helmet", "infant", "jester", "kernel", "lantern",
    "mirror", "nugget", "orchid", "parrot", "quiver", "ribbon", "silver", "turret",
    "unicorn", "violet", "willow", "xylose", "yonder", "zodiac", "acorn", "basket",
    "copper", "dahlia", "emerald", "fossil", "garnet", "honey", "insect", "jasper",
    "kelp", "lotus", "magnet", "nectar", "opal", "petal", "quill", "ruby",
    "sapphire", "topaz", "urchin", "vapor", "wheat", "xenolith", "yarn", "zinc"
]

DATA_FILE = Path("messaging_data.json")

session = None  # Global active session
pending_user = None  # Pending user (created but not logged in)


class Session:
    """Represents an active user session"""
    def __init__(self, user_id, encryption_key, username):
        self.user_id = user_id
        self.encryption_key = encryption_key
        self.username = username


class PendingUser:
    """Represents a user who has sent messages but not logged in yet"""
    def __init__(self, user_id, encryption_key, mnemonic, username):
        self.user_id = user_id
        self.encryption_key = encryption_key
        self.mnemonic = mnemonic
        self.username = username


def generate_mnemonic():
    """Generate a 12-word mnemonic from random selection"""
    words = [secrets.choice(WORDLIST) for _ in range(12)]
    return " ".join(words)


def mnemonic_to_key(mnemonic):
    """Convert mnemonic phrase to encryption key via hashing"""
    key_material = hashlib.sha256(mnemonic.encode()).digest()
    return key_material


def derive_user_id(mnemonic):
    """Derive a user ID from the mnemonic"""
    user_hash = hashlib.sha256(("user:" + mnemonic).encode()).hexdigest()
    return user_hash[:16]


def xor_encrypt_decrypt(data, key):
    """Simple XOR encryption/decryption (symmetric)"""
    key_bytes = key * (len(data) // len(key) + 1)
    result = bytes([d ^ k for d, k in zip(data, key_bytes[:len(data)])])
    return result


def encrypt_data(plaintext, key):
    """Encrypt plaintext using the key"""
    data_bytes = plaintext.encode()
    encrypted = xor_encrypt_decrypt(data_bytes, key)
    return encrypted.hex()


def decrypt_data(ciphertext_hex, key):
    """Decrypt ciphertext using the key"""
    try:
        ciphertext = bytes.fromhex(ciphertext_hex)
        decrypted = xor_encrypt_decrypt(ciphertext, key)
        return decrypted.decode()
    except:
        return None


def load_storage():
    """Load encrypted data from file"""
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_storage(data):
    """Save encrypted data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def login():
    """Handle user login with mnemonic"""
    global session, pending_user
    
    print("\n" + "="*60)
    print("LOGIN WITH 12-WORD SECRET PHRASE")
    print("="*60)
    print("\nEnter your 12-word secret phrase (space-separated):")
    mnemonic = input("> ").strip().lower()
    
    # Validate format
    words = mnemonic.split()
    if len(words) != 12:
        print(f"❌ Invalid: expected 12 words, got {len(words)}")
        return
    
    # Derive credentials from mnemonic
    user_id = derive_user_id(mnemonic)
    encryption_key = mnemonic_to_key(mnemonic)
    
    # Check if user has any data
    storage = load_storage()
    if user_id in storage:
        # Verify mnemonic is correct by attempting to decrypt
        encrypted_check = storage[user_id].get("check")
        if encrypted_check:
            decrypted = decrypt_data(encrypted_check, encryption_key)
            if decrypted == "valid":
                username = decrypt_data(storage[user_id]["username"], encryption_key)
                print(f"\n✓ Login successful!")
                print(f"✓ Welcome back, {username}!")
                print(f"✓ User ID: {user_id}")
                session = Session(user_id, encryption_key, username)
                pending_user = None  # Clear any pending user
            else:
                print("❌ Invalid secret phrase - decryption failed")
        else:
            print("❌ Data corruption detected")
    else:
        print("❌ No account found for this secret phrase.")
        print("   Use 'Create new account' to register first.")


def create_account():
    """Create a new user account"""
    global pending_user
    
    print("\n" + "="*60)
    print("CREATE NEW ACCOUNT")
    print("="*60)
    
    print("\nEnter a username:")
    username = input("> ").strip()
    
    if not username:
        print("❌ Username cannot be empty")
        return
    
    # Generate new account
    mnemonic = generate_mnemonic()
    user_id = derive_user_id(mnemonic)
    encryption_key = mnemonic_to_key(mnemonic)
    
    pending_user = PendingUser(user_id, encryption_key, mnemonic, username)
    
    # Save account data to storage
    encrypted_check = encrypt_data("valid", encryption_key)
    encrypted_username = encrypt_data(username, encryption_key)
    
    storage = load_storage()
    storage[user_id] = {
        "check": encrypted_check,
        "username": encrypted_username,
        "inbox": [],
        "sent": []  # Added sent messages storage
    }
    save_storage(storage)
    
    print(f"\n✓ Account created successfully!")
    print(f"✓ User ID: {user_id}")
    print(f"✓ Username: {username}")
    print("\n" + "="*60)
    print("⚠️  CRITICAL: Save these 12 secret words:")
    print("="*60)
    print(f"\n{mnemonic}\n")
    print("="*60)
    print("⚠️  Write them down! This is the ONLY way to access your account.")
    print("="*60)


def get_all_users():
    """Get list of all users"""
    storage = load_storage()
    users = []
    for user_id in storage:
        users.append(user_id)
    return users


def send_message():
    """Send a message to another user"""
    global session, pending_user
    
    current_user = session if session else pending_user
    if not current_user:
        print("❌ Error: No active session or account")
        print("   Create an account first or log in")
        return
    
    storage = load_storage()
    
    # Show available users
    print("\n" + "="*60)
    print("SEND MESSAGE")
    print("="*60)
    
    all_users = get_all_users()
    if len(all_users) <= 1:
        print("❌ No other users found in the system")
        print("   Share your User ID with others so they can create accounts")
        print(f"   Your User ID: {current_user.user_id}")
        return
    
    print("\nAvailable users:")
    user_list = []
    for i, uid in enumerate(all_users, 1):
        if uid == current_user.user_id:
            continue
        # Try to get username
        user_data = storage[uid]
        try:
            username = decrypt_data(user_data["username"], current_user.encryption_key) if session else "Unknown"
            print(f"{i}. {username} (ID: {uid})")
        except:
            print(f"{i}. User ID: {uid}")
        user_list.append(uid)
    
    if not user_list:
        print("❌ No other users available")
        print(f"   Share your User ID with others: {current_user.user_id}")
        return
    
    print(f"\n{len(user_list)+1}. Enter User ID manually")
    print(f"{len(user_list)+2}. Cancel")
    
    choice = input("\nSelect recipient: ").strip()
    
    try:
        choice_num = int(choice)
        if choice_num == len(user_list) + 2:
            return
        elif choice_num == len(user_list) + 1:
            recipient_id = input("Enter recipient User ID: ").strip()
        elif 1 <= choice_num <= len(user_list):
            recipient_id = user_list[choice_num - 1]
        else:
            print("❌ Invalid selection")
            return
    except ValueError:
        print("❌ Invalid input")
        return
    
    if recipient_id not in storage:
        print("❌ Recipient not found")
        return
    
    if recipient_id == current_user.user_id:
        print("❌ Cannot send message to yourself")
        return
    
    # Get message
    print("\nEnter your message:")
    message = input("> ").strip()
    
    if not message:
        print("❌ Message cannot be empty")
        return
    
    # Create message data
    message_id = secrets.token_hex(8)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_data = {
        "id": message_id,
        "from": current_user.user_id,
        "from_name": current_user.username,
        "to": recipient_id,
        "message": message,
        "timestamp": timestamp,
        "read": False
    }
    
    message_json = json.dumps(message_data)
    
    # Add to recipient's inbox
    if "inbox" not in storage[recipient_id]:
        storage[recipient_id]["inbox"] = []
    
    storage[recipient_id]["inbox"].append(message_json)
    
    # Also store in sender's sent messages
    if "sent" not in storage[current_user.user_id]:
        storage[current_user.user_id]["sent"] = []
    
    storage[current_user.user_id]["sent"].append(message_json)
    save_storage(storage)
    
    print(f"\n✓ Message sent!")
    print(f"✓ Sent at {timestamp}")


def get_conversation_partners(user_id: str) -> List[Tuple[str, str, datetime]]:
    """Get all users that the current user has conversations with"""
    storage = load_storage()
    conversations = {}
    
    if user_id not in storage:
        return []
    
    user_data = storage[user_id]
    
    # Check inbox messages
    for msg_json in user_data.get("inbox", []):
        try:
            msg = json.loads(msg_json)
            sender_id = msg["from"]
            sender_name = msg["from_name"]
            timestamp = datetime.strptime(msg["timestamp"], "%Y-%m-%d %H:%M:%S")
            
            if sender_id not in conversations or timestamp > conversations[sender_id][2]:
                conversations[sender_id] = (sender_id, sender_name, timestamp)
        except:
            continue
    
    # Check sent messages
    for msg_json in user_data.get("sent", []):
        try:
            msg = json.loads(msg_json)
            recipient_id = msg["to"]
            # Try to get recipient name
            if recipient_id in storage:
                recipient_data = storage[recipient_id]
                if session:
                    recipient_name = decrypt_data(recipient_data["username"], session.encryption_key)
                else:
                    recipient_name = "Unknown"
            else:
                recipient_name = "Unknown"
            
            timestamp = datetime.strptime(msg["timestamp"], "%Y-%m-%d %H:%M:%S")
            
            if recipient_id not in conversations or timestamp > conversations[recipient_id][2]:
                conversations[recipient_id] = (recipient_id, recipient_name, timestamp)
        except:
            continue
    
    # Sort by most recent message
    sorted_conversations = sorted(
        conversations.values(),
        key=lambda x: x[2],
        reverse=True
    )
    
    return sorted_conversations


def view_conversation_with(user_id: str, other_user_id: str):
    """View conversation thread between two users"""
    global session, pending_user
    
    current_user = session if session else pending_user
    if not current_user:
        return
    
    storage = load_storage()
    all_messages = []
    
    # Get messages from inbox (received)
    if current_user.user_id in storage:
        user_data = storage[current_user.user_id]
        for msg_json in user_data.get("inbox", []):
            try:
                msg = json.loads(msg_json)
                if msg["from"] == other_user_id:
                    msg["direction"] = "received"
                    all_messages.append(msg)
            except:
                continue
    
    # Get messages from sent
    if current_user.user_id in storage:
        user_data = storage[current_user.user_id]
        for msg_json in user_data.get("sent", []):
            try:
                msg = json.loads(msg_json)
                if msg["to"] == other_user_id:
                    msg["direction"] = "sent"
                    all_messages.append(msg)
            except:
                continue
    
    # Sort messages by timestamp
    all_messages.sort(key=lambda x: x["timestamp"])
    
    if not all_messages:
        print(f"\nNo messages with this user yet.")
        return
    
    # Get other user's name
    other_user_name = "Unknown"
    if other_user_id in storage:
        other_user_data = storage[other_user_id]
        if session:
            other_user_name = decrypt_data(other_user_data["username"], session.encryption_key)
        else:
            # Try to find name from any message
            for msg in all_messages:
                if "from_name" in msg and msg["from"] == other_user_id:
                    other_user_name = msg["from_name"]
                    break
    
    print(f"\n{'='*60}")
    print(f"💬 CHAT WITH {other_user_name} ({other_user_id})")
    print(f"{'='*60}")
    
    # Display messages in chat format
    for msg in all_messages:
        timestamp = msg["timestamp"]
        message = msg["message"]
        
        if msg["direction"] == "received":
            print(f"\n[{timestamp}] {other_user_name}:")
            print(f"  {message}")
        else:
            print(f"\n[{timestamp}] You:")
            print(f"  {message}")
    
    print(f"\n{'='*60}")
    
    # Mark messages as read if logged in
    if session:
        # Update inbox messages as read
        user_data = storage[session.user_id]
        new_inbox = []
        for msg_json in user_data.get("inbox", []):
            msg = json.loads(msg_json)
            if msg["from"] == other_user_id:
                msg["read"] = True
            new_inbox.append(json.dumps(msg))
        
        if new_inbox != user_data.get("inbox", []):
            storage[session.user_id]["inbox"] = new_inbox
            save_storage(storage)


def view_conversations():
    """View all conversations (like a chat app inbox)"""
    global session, pending_user
    
    current_user = session if session else pending_user
    if not current_user:
        print("❌ No active account found")
        return
    
    conversations = get_conversation_partners(current_user.user_id)
    
    if not conversations:
        print("\n📭 No conversations yet")
        print("\nStart a conversation by sending a message to someone!")
        return
    
    print("\n" + "="*60)
    print("💬 CONVERSATIONS")
    print("="*60)
    
    storage = load_storage()
    
    for i, (user_id, username, last_timestamp) in enumerate(conversations, 1):
        # Count unread messages
        unread_count = 0
        if current_user.user_id in storage:
            user_data = storage[current_user.user_id]
            for msg_json in user_data.get("inbox", []):
                try:
                    msg = json.loads(msg_json)
                    if msg["from"] == user_id and not msg.get("read", False):
                        unread_count += 1
                except:
                    continue
        
        # Format last message time
        time_diff = datetime.now() - last_timestamp
        if time_diff.days == 0:
            last_seen = "Today"
        elif time_diff.days == 1:
            last_seen = "Yesterday"
        elif time_diff.days < 7:
            last_seen = f"{time_diff.days}d ago"
        else:
            last_seen = last_timestamp.strftime("%b %d")
        
        unread_indicator = f" ✉️{unread_count}" if unread_count > 0 else ""
        print(f"\n{i}. {username} {unread_indicator}")
        print(f"   ID: {user_id}")
        print(f"   Last: {last_seen}")
    
    print(f"\n{len(conversations)+1}. Back to menu")
    
    choice = input("\nSelect conversation to view: ").strip()
    
    try:
        choice_num = int(choice)
        if choice_num == len(conversations) + 1:
            return
        elif 1 <= choice_num <= len(conversations):
            selected_user_id = conversations[choice_num - 1][0]
            view_conversation_with(current_user.user_id, selected_user_id)
            
            # After viewing conversation, show options
            print("\nOptions:")
            print("1) Send reply")
            print("2) Back to conversations")
            print("3) Back to main menu")
            
            sub_choice = input("\nChoose an option: ").strip()
            
            if sub_choice == "1":
                # Quick reply
                if session or pending_user:
                    # Store the recipient for quick sending
                    temp_recipient = selected_user_id
                    print(f"\nReply to {conversations[choice_num - 1][1]}:")
                    message = input("> ").strip()
                    
                    if message:
                        storage = load_storage()
                        current_user = session if session else pending_user
                        
                        message_id = secrets.token_hex(8)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message_data = {
                            "id": message_id,
                            "from": current_user.user_id,
                            "from_name": current_user.username,
                            "to": temp_recipient,
                            "message": message,
                            "timestamp": timestamp,
                            "read": False
                        }
                        
                        message_json = json.dumps(message_data)
                        
                        # Add to recipient's inbox
                        if "inbox" not in storage[temp_recipient]:
                            storage[temp_recipient]["inbox"] = []
                        storage[temp_recipient]["inbox"].append(message_json)
                        
                        # Add to sender's sent messages
                        if "sent" not in storage[current_user.user_id]:
                            storage[current_user.user_id]["sent"] = []
                        storage[current_user.user_id]["sent"].append(message_json)
                        
                        save_storage(storage)
                        print("✓ Reply sent!")
            elif sub_choice == "2":
                view_conversations()
            elif sub_choice == "3":
                return
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Invalid input")


def show_my_info():
    """Show user's own information"""
    global session, pending_user
    
    current_user = session if session else pending_user
    
    if not current_user:
        print("❌ No account found")
        return
    
    print("\n" + "="*60)
    print("YOUR ACCOUNT INFORMATION")
    print("="*60)
    print(f"\nUsername: {current_user.username}")
    print(f"User ID: {current_user.user_id}")
    
    storage = load_storage()
    if current_user.user_id in storage:
        user_data = storage[current_user.user_id]
        
        # Count statistics
        inbox_count = len(user_data.get("inbox", []))
        sent_count = len(user_data.get("sent", []))
        unread_count = 0
        
        for msg_json in user_data.get("inbox", []):
            try:
                msg = json.loads(msg_json)
                if not msg.get("read", False):
                    unread_count += 1
            except:
                pass
        
        # Get conversation partners
        conversations = get_conversation_partners(current_user.user_id)
        
        print(f"\nStatistics:")
        print(f"  - Conversations: {len(conversations)}")
        print(f"  - Received messages: {inbox_count}")
        print(f"  - Sent messages: {sent_count}")
        print(f"  - Unread messages: {unread_count}")
    
    print("\n" + "="*60)
    print("📝 To receive messages from others:")
    print("   Share your User ID with them")
    print("="*60)


def use_application():
    """Main application menu"""
    global session, pending_user
    
    print("\n" + "="*60)
    print("💬 CHAT APPLICATION")
    print("="*60)
    
    if session:
        print(f"Logged in as: {session.username}")
        
        # Show conversation stats
        conversations = get_conversation_partners(session.user_id)
        unread_total = 0
        storage = load_storage()
        
        if session.user_id in storage:
            user_data = storage[session.user_id]
            for msg_json in user_data.get("inbox", []):
                try:
                    msg = json.loads(msg_json)
                    if not msg.get("read", False):
                        unread_total += 1
                except:
                    pass
        
        if conversations:
            if unread_total > 0:
                print(f"✉️  {unread_total} unread message(s) in {len(conversations)} conversation(s)")
            else:
                print(f"💬 {len(conversations)} conversation(s)")
        
        print("\n1) View conversations")
        print("2) Start new conversation")
        print("3) My account info")
        print("4) Back to main menu")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == "1":
            view_conversations()
        elif choice == "2":
            send_message()
        elif choice == "3":
            show_my_info()
        elif choice == "4":
            return
        else:
            print("❌ Invalid option")
    
    elif pending_user:
        print(f"Active account: {pending_user.username}")
        
        # Show conversation stats
        conversations = get_conversation_partners(pending_user.user_id)
        unread_total = 0
        storage = load_storage()
        
        if pending_user.user_id in storage:
            user_data = storage[pending_user.user_id]
            for msg_json in user_data.get("inbox", []):
                try:
                    msg = json.loads(msg_json)
                    if not msg.get("read", False):
                        unread_total += 1
                except:
                    pass
        
        if conversations:
            if unread_total > 0:
                print(f"✉️  {unread_total} unread message(s) in {len(conversations)} conversation(s)")
            else:
                print(f"💬 {len(conversations)} conversation(s)")
        
        print("\n1) View conversations")
        print("2) Start new conversation")
        print("3) My account info")
        print("4) Back to main menu")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == "1":
            view_conversations()
        elif choice == "2":
            send_message()
        elif choice == "3":
            show_my_info()
        elif choice == "4":
            return
        else:
            print("❌ Invalid option")
    
    else:
        print("No active account")
        print("\n1) Create new account")
        print("2) Back to main menu")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == "1":
            create_account()
        elif choice == "2":
            return
        else:
            print("❌ Invalid option")


def show_secret():
    """Show the pending user's secret phrase"""
    global pending_user
    
    if not pending_user:
        print("❌ No pending account found")
        return
    
    print("\n" + "="*60)
    print("YOUR 12-WORD SECRET PHRASE")
    print("="*60)
    print(f"\n{pending_user.mnemonic}\n")
    print("="*60)
    print("⚠️  Keep this secret safe! It's the ONLY way to access your account.")
    print("="*60)


def main():
    """Main program loop"""
    global session, pending_user
    
    print("="*60)
    print("💬 SECURE CHAT APPLICATION")
    print("="*60)
    print("\nWelcome! This is a secure chat system with 12-word secret phrases.")
    
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        
        if session:
            print(f"Status: ✓ Logged in as {session.username}")
            # Show conversation summary
            conversations = get_conversation_partners(session.user_id)
            unread_total = 0
            storage = load_storage()
            
            if session.user_id in storage:
                user_data = storage[session.user_id]
                for msg_json in user_data.get("inbox", []):
                    try:
                        msg = json.loads(msg_json)
                        if not msg.get("read", False):
                            unread_total += 1
                    except:
                        pass
            
            if conversations:
                if unread_total > 0:
                    print(f"✉️  {unread_total} unread in {len(conversations)} chats")
                else:
                    print(f"💬 {len(conversations)} active chats")
        elif pending_user:
            print(f"Status: Active as {pending_user.username}")
            # Show conversation summary
            conversations = get_conversation_partners(pending_user.user_id)
            unread_total = 0
            storage = load_storage()
            
            if pending_user.user_id in storage:
                user_data = storage[pending_user.user_id]
                for msg_json in user_data.get("inbox", []):
                    try:
                        msg = json.loads(msg_json)
                        if not msg.get("read", False):
                            unread_total += 1
                    except:
                        pass
            
            if conversations:
                if unread_total > 0:
                    print(f"✉️  {unread_total} unread in {len(conversations)} chats")
                else:
                    print(f"💬 {len(conversations)} active chats")
        else:
            print("Status: No active account")
        
        print("\n1) Log in with 12-word secret phrase")
        print("2) Open chat application")
        print("3) Create new account")
        print("4) Logout")
        
        if pending_user and not session:
            print("5) Show my 12-word secret phrase")
            print("6) Exit")
        else:
            print("5) Exit")
        
        choice = input("\nChoose an option: ").strip()
        
        if choice == "1":
            login()
        elif choice == "2":
            use_application()
        elif choice == "3":
            create_account()
        elif choice == "4":
            if session:
                print(f"\n✓ Logged out from {session.username}")
                session = None
            elif pending_user:
                print(f"\n✓ Cleared pending account {pending_user.username}")
                pending_user = None
            else:
                print("❌ Not logged in")
        elif choice == "5":
            if pending_user and not session:
                show_secret()
            else:
                print("\nGoodbye! Keep your secret phrase safe.")
                break
        elif choice == "6":
            if pending_user and not session:
                print("\nGoodbye! Keep your secret phrase safe.")
                break
            else:
                print("❌ Invalid option")
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()