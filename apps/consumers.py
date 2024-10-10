import os
import json
import io
import base64  # To encode audio for easier debugging
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
from pydub import AudioSegment

class AudioStreamConsumer(AsyncWebsocketConsumer):
    audio_data = []  # List to store audio data for all users
    audio_dir = 'templates/voice/'
    active_connections = 0  # Class variable to track active connections

    async def connect(self):
        self.room_name = 'audio_stream'
        self.room_group_name = f'audio_{self.room_name}'
        
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Increment active connection count
        AudioStreamConsumer.active_connections += 1
        print("Connect---->",AudioStreamConsumer.active_connections)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Decrement active connection count
        AudioStreamConsumer.active_connections -= 1

        print("Disconnect---->",AudioStreamConsumer.active_connections)
        
        # Check if there are no other connections
        if AudioStreamConsumer.active_connections == 0:  
            await self.save_audio()  # Save audio if no users are connected

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            self.audio_data.append(bytes_data) 

            base=base64.b64encode(bytes_data).decode('utf-8')

            bytes_data = base64.b64decode(base)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'audio_message',
                    'audio': bytes_data
                }
            )
            print(['audio'])
        else: 
            print('No Bytes Data Recieved')

    async def audio_message(self, event):
        print("Audio message handler called ---->>", event['audio']) 
        audio = event['audio']
        audio_bytes = base64.b64decode(audio)  # Decode base64 back to bytes
        await self.send(bytes_data=audio_bytes)  # Send audio bytes to WebSocket

    async def save_audio(self):
        if self.audio_data:
            combined = AudioSegment.empty()
            for audio_chunk in self.audio_data:
                try:
                    # Ensure that the chunk is in the correct format before decoding
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_chunk), format="webm")  # Use "webm" for input format
                    combined += audio_segment
                except Exception as e:
                    print(f"Error decoding audio chunk: {e}")
                    continue  # Skip this chunk if it fails

            output_file = os.path.join(self.audio_dir, f'{datetime.now().strftime("%Y%m%d%H%M%S")}_conversation.mp3')
            combined.export(output_file, format='mp3')  # Exporting as MP3
            print(f"Audio saved as {output_file}")