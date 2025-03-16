import requests
import base64, hashlib
import os
import json
from Crypto.Cipher import AES

CHANNEL_ID = <CHANGE ME>
BOT_NAME = "MyDataBot"
COMMON_ERROR = "NOO"

class Encryption:
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
        # Return base85-encoded ciphertext (including nonce and tag)
        return base64.b85encode(cipher.nonce + tag + ciphertext)

    def decrypt(self, encrypted_data: bytes, key: str) -> bytes:
        """Decrypts the given encrypted data using AES-256-GCM with the provided key."""
        key_bytes = self.derive_key(key)
        decoded = base64.b85decode(encrypted_data)
        nonce, tag, ciphertext = decoded[:16], decoded[16:32], decoded[32:]
        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

class Upload_Logic:
    def __init__(self):
        # CHARACTER_LIMIT is set to a multiple of 5 to ensure valid base85 blocks.
        self.CHARACTER_LIMIT = 7340032
        self.CHARACTER_LIMIT -= self.CHARACTER_LIMIT % 5
        self.WEBHOOK_URL = "<CHANGE ME>"
        self.WEBHOOK_URL_AWAIT = self.WEBHOOK_URL + "?wait=true"
        self.PROXIES = {
            "http": "http://localhost:8118",
            "https": "http://localhost:8118",
        }

    def split_into_chunks(self, text: str) -> list:
        """Splits the text into chunks of a given limit (ensuring each chunk is a multiple of 5)."""
        limit = self.CHARACTER_LIMIT
        return [text[i:i+limit] for i in range(0, len(text), limit)]

    def send_file(self, payload: str, password: str) -> list:
        """
        Sends the encrypted payload (a base85-encoded string) to the Discord channel using a webhook.
        Returns a list of message IDs.
        """
        chunks = self.split_into_chunks(payload)
        total_chunks = len(chunks)
        message_ids = []
        encryption_instance = Encryption()

        for idx, chunk in enumerate(chunks, start=1):
            chunk_bytes = chunk.encode('utf-8')
            try:
                ip = requests.get('https://api64.ipify.org', proxies=self.PROXIES, timeout=30).text.strip()
            except Exception as e:
                ip = "N/A"
            print(f"\r Upload progress via route ({ip}): ({(idx*100)//total_chunks}%)", end='           ')
            post = requests.post(self.WEBHOOK_URL_AWAIT, proxies=self.PROXIES,
                                 files={'file': ('message.txt', chunk_bytes)})
            if post.status_code == 200:
                message = post.json()
                message_ids.append(message["id"])
            else:
                print(f"\nFailed to send chunk {idx}. Status code: {post.status_code}")
        print("\n")
        return message_ids

    def retrieve_file(self, message_ids: list, password: str) -> str:
        """
        Retrieves all chunks using the message IDs, concatenates them,
        and returns the decrypted payload (JSON string) that contains file data.
        """
        encryption_instance = Encryption()
        all_chunks = ""
        countr = 0
        for mid in message_ids:
            url = f"{self.WEBHOOK_URL}/messages/{mid}"
            response = requests.get(url, proxies=self.PROXIES)
            if response.status_code == 200:
                msg = response.json()
                attachments = msg.get("attachments", [])
                if attachments:
                    attachment = attachments[0]
                    attachment_url = attachment["url"]
                    file_response = requests.get(attachment_url, proxies=self.PROXIES)
                    if file_response.status_code == 200:
                        chunk_data = file_response.content.decode('utf-8')
                        all_chunks += chunk_data
                    else:
                        print(f"Failed to download file from {attachment_url}. Status code: {file_response.status_code}")
                else:
                    print(f"No attachments found in message ID {mid}.")
            else:
                print(f"Failed to retrieve message ID {mid}. Status code: {response.status_code}")

        # Decrypt the concatenated payload
        try:
            decrypted_bytes = encryption_instance.decrypt(all_chunks.encode('utf-8'), password)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None

    def delete_ids(self, message_ids: list) -> None:
        """Deletes the messages corresponding to the given message IDs."""
        total_ids = len(message_ids)
        for count, mid in enumerate(message_ids, start=1):
            url = f"{self.WEBHOOK_URL}/messages/{mid}"
            response = requests.delete(url, proxies=self.PROXIES)
            try:
                ip = requests.get('https://api64.ipify.org', proxies=self.PROXIES, timeout=30).text.strip()
            except Exception as e:
                ip = "N/A"
            if response.status_code == 204:
                print(f"\r Deleted {mid} via route ({ip}) : ({(count/total_ids)*100:.2f}%)", end='           ')
            else:
                print(f"\nFailed to delete message ID {mid}. Status code: {response.status_code}")
        print("\n")

class LocalHandler:
    def __init__(self):
        pass

    def load_file(self, filepath: str) -> bytes:
        """Reads the file and returns its raw bytes."""
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            return data
        except FileNotFoundError:
            print("Invalid File")
            return None

    def save_file(self, filepath: str, data: bytes) -> int:
        """Saves the raw bytes data to the file."""
        with open(filepath, "wb") as f:
            return f.write(data)

if __name__ == "__main__":
    ul = Upload_Logic()
    lh = LocalHandler()
    encryption_instance = Encryption()

    while True:
        command = input(">>> ").strip().lower()
        if command == "exit":
            print("Good bye")
            break
        elif command == "help":
            print("Commands: \n 1. upload \n 2. retrieve \n 3. delete \n 4. exit")
        elif command == "upload":
            filename = input("Enter filename: ").strip()
            file_data = lh.load_file(filename)
            if file_data is None:
                continue
            # Extract file extension (default to "dat" if none found)
            if "." in filename:
                _, file_ext = filename.rsplit(".", 1)
            else:
                file_ext = "dat"
            print("MAKE SURE TO ENTER A PASSWORD YOU WILL REMEMBER...If you forget it, you will not be able to retrieve the data")
            password = input("Enter password: ").strip()
            # Prepare payload: a JSON object with the file extension and base85-encoded file data
            payload_dict = {
                "ext": file_ext,
                "data": base64.b85encode(file_data).decode('utf-8')
            }
            payload_json = json.dumps(payload_dict)
            payload_bytes = payload_json.encode('utf-8')
            # Encrypt the payload
            encrypted_payload = encryption_instance.encrypt(payload_bytes, password).decode('utf-8')
            # Send the encrypted payload (split into safe chunks)
            message_ids = ul.send_file(encrypted_payload, password)
            # Save all message IDs into the runtime file (rt)
            with open("out.rt", "w") as f:
                for mid in message_ids:
                    f.write(f"{mid}\n")
            print("Upload complete. Message IDs saved to out.rt")
        elif command == "retrieve":
            rt_file = input("Enter rt file: ").strip()
            try:
                with open(rt_file, "r") as f:
                    message_ids = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                print("Invalid RT file")
                continue
            print("MAKE SURE TO ENTER THE SAME PASSWORD YOU USED TO UPLOAD THE FILE")
            password = input("Enter password: ").strip()
            decrypted_payload = ul.retrieve_file(message_ids, password)
            if decrypted_payload is None:
                print("Failed to retrieve data.")
                continue
            try:
                payload_dict = json.loads(decrypted_payload)
                file_ext = payload_dict.get("ext", "dat")
                file_b85_data = payload_dict.get("data", "")
                original_file_bytes = base64.b85decode(file_b85_data.encode('utf-8'))
            except Exception as e:
                print(f"Failed to parse decrypted data: {e}")
                continue
            output_filename = f"retrieved.{file_ext}"
            lh.save_file(output_filename, original_file_bytes)
            print(f"File retrieved and saved as {output_filename}")
        elif command == "delete":
            rt_file = input("Enter rt file: ").strip()
            try:
                with open(rt_file, "r") as f:
                    message_ids = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                print("Invalid RT file")
                continue
            ul.delete_ids(message_ids)
            os.remove(rt_file)
            print("RT file deleted.")
        else:
            print("Unknown command. Type 'help' for commands.")
