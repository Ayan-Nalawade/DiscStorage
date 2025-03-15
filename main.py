import requests, json
import time, os

import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

CHANNEL_ID = 1350240209291317440
BOT_NAME = "MyDataBot"


class Encryption():
    def __init__(self):
        pass 

    def derive_key(self, key: str) -> bytes:
        """Derives a 32-byte AES key from the given string key."""
        return hashlib.sha256(key.encode()).digest()

    def encrypt(self, data: bytes, key: str) -> bytes:
        """Encrypts the given data using AES-256-GCM with the provided key."""
        key_bytes = self.derive_key(key)
        cipher = AES.new(key_bytes, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return base64.b85encode(cipher.nonce + tag + ciphertext)

    def decrypt(self, encrypted_data: bytes, key: str) -> bytes:
        """Decrypts the given encrypted data using AES-256-GCM with the provided key."""
        key_bytes = self.derive_key(key)
        encrypted_data = base64.b85decode(encrypted_data)
        nonce, tag, ciphertext = encrypted_data[:16], encrypted_data[16:32], encrypted_data[32:]
        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

class Upload_Logic():
    def __init__(self):
        self.CHARACTER_LIMIT = 2000 #2000
        self.WEBHOOK_URL = "https://discord.com/api/webhooks/1350242637055000657/hebJBBZakZJak3Ui9OOl7kxctz_RFKRXpm9pcz2d3eWqso5uEmSx5Gm0aEQBB_tAu1NM"
        self.WEBHOOK_URL_AWAIT = self.WEBHOOK_URL + "?wait=true"
        self.PROXIES = {
                "http": "http://localhost:8118",
                "https": "http://localhost:8118",
            }
        self.NULLCHAR = "⠀"

    
    def split_into_chunk(self, text):
        limit = self.CHARACTER_LIMIT
        chunks = []
        while len(text) > limit:
            # Find the best place to split (at the last space within the limit)
            split_index = text[:limit].rfind(' ')
            if split_index == -1:  # No space found, split at the limit
                split_index = limit
            chunks.append(text[:split_index])
            text = text[split_index:].lstrip()  # Remove leading spaces in the remaining text
        
        if text:  # Add any remaining text
            chunks.append(text)
        
        return chunks
    
    def send_file(self, text: str, password: str, filetype: str) -> list:
        """Sends a file to the Discord channel using a webhook and returns the message ID. THE TEXT HAS FILE TYPE ADDED"""
        
        chunk: list = self.split_into_chunk(text)
        countr: int = 0
        return_list:list = []
        call = Encryption()

        for each in chunk:
            each = f"{call.encrypt(f"{each}{self.NULLCHAR}{filetype}".encode('utf-8'), password).decode('utf-8')}"
            countr += 1
            print(f"\r Upload progress via route ({requests.get('https://api64.ipify.org', proxies=self.PROXIES, timeout=30).text.strip()}): ({(countr*100//len(chunk))}%)", end='           ')
            post = requests.post(self.WEBHOOK_URL_AWAIT, proxies=self.PROXIES, files={'file': ('message.txt', each.encode('utf-8') )})
            if post.status_code == 200:
                message = post.json()
                return_list.append(message["id"]) 
        
        print("\n")

        return return_list
    
    def retrieve_id(self, message_id: list, password: str) -> tuple: # Tuple with decrypted data AND filetype
        """Retrieves the file based on the message IDs and decrypts the data."""
        call = Encryption()
        for each in message_id:
            url = f"{self.WEBHOOK_URL}/messages/{each}"
            response = requests.get(url, proxies=self.PROXIES)
            if response.status_code == 200:
                msg = response.json()
                attachments = msg.get("attachments", [])
                if attachments:
                    attachment = attachments[0]
                    attachment_url = attachment["url"]
                    file_response = requests.get(attachment_url)
                    if file_response.status_code == 200:
                        return call.decrypt(file_response.content, password).decode('utf-8').split(self.NULLCHAR)
                    else:
                        print(f"Failed to download file from {attachment_url}. Status code: {file_response.status_code}")
                else:
                    print(f"No attachments found in message ID {each}.")


    def delete_id(self, message_id: list) -> None:
            """ Deletes the message based on the message IDs."""
            countr: int = 0
            total_ids = len(message_id)
            for each in message_id:
                countr += 1
                url = f"{self.WEBHOOK_URL}/messages/{each}"
                response = requests.delete(url, proxies=self.PROXIES)
                if response.status_code == 204:
                    print(f"\r Deleted {each} via route ({requests.get('https://api64.ipify.org', proxies=self.PROXIES, timeout=30).text.strip()}) : ({(countr//total_ids)*100:.2f}%)", end='           ')
                else:
                    print(f"\n Failed to delete message ID {each}. Status code: {response.status_code}")
            print("\n")







    
u = Upload_Logic()
id = u.send_file("Hello world", "WOW", "txt")
print(id)
rt = u.retrieve_id(id, "WOW")
print(rt)
u.delete_id(id)