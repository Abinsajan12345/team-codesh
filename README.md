# Hand Gesture Text Editor

A simple hand gesture recognition system that allows you to type text using hand movements and displays it in a web interface.

## Features

- 🤚 **Hand Gesture Recognition**: Use hand movements to select letters
- 🌐 **Web Interface**: Real-time text display in a modern web browser
- 📡 **WebSocket Communication**: Real-time data transmission between Python and web
- 🎯 **Two Modes**: Letter selection and font switching
- 📊 **Connection Monitoring**: Live status and statistics

## How It Works

1. **Hand Tracking**: Python script uses MediaPipe to track hand movements
2. **Gesture Recognition**: Detects hand rotation and finger touches
3. **WebSocket Server**: Sends selected letters to web interface
4. **Web Display**: Shows text in real-time with connection status

## Setup Instructions

### Prerequisites

Make sure you have Python installed with the following packages:
```bash
pip install opencv-python mediapipe websockets
```

### Running the System

1. **Start the Python Server**:
   ```bash
   python websocket_server.py
   ```
   - This will start the hand tracking and WebSocket server
   - You should see a camera window showing hand tracking
   - The server runs on `ws://localhost:8765`

2. **Open the Web Interface**:
   - Open `simple-frontend.html` in your web browser
   - Click "Connect" to establish WebSocket connection
   - Start using hand gestures to type!

## How to Use Hand Gestures

### Letter Mode (Default)
- **Rotate your hand** to select different letters (A-Z)
- **Hold the position** for a moment to send the letter
- **Touch thumb to index finger** to switch to letter mode

### Font Mode
- **Touch thumb to middle finger** to switch to font mode
- **Rotate your hand** to select different fonts
- **Touch thumb to index finger** to return to letter mode

### Controls
- **Connect/Disconnect**: Manage WebSocket connection
- **Clear Text**: Clear the text area
- **Copy Text**: Copy text to clipboard

## File Structure

```
├── websocket_server.py    # Python hand tracking + WebSocket server
├── simple-frontend.html   # Web interface
└── README.md             # This file
```

## Troubleshooting

### Connection Issues
- Make sure the Python server is running before connecting
- Check that port 8765 is not blocked by firewall
- Ensure camera access is granted

### Hand Tracking Issues
- Ensure good lighting for hand detection
- Keep your hand clearly visible to the camera
- Try adjusting hand position if tracking is unstable

### Performance
- The system works best with a stable hand position
- Hold each letter for a moment before moving to the next
- Use smooth hand movements for better accuracy

## Technical Details

- **WebSocket Port**: 8765
- **Hand Hold Threshold**: 10 frames (adjustable in code)
- **Touch Threshold**: 0.07 (distance for finger touch detection)
- **Supported Letters**: A-Z
- **Supported Fonts**: 7 OpenCV font styles

## Customization

You can modify the following parameters in `websocket_server.py`:
- `HOLD_THRESHOLD`: How long to hold a letter before sending
- `TOUCH_THRESHOLD`: Sensitivity for finger touch detection
- `CROP_PADDING`: Padding around hand for display cropping

## Browser Compatibility

The web interface works with all modern browsers that support WebSocket:
- Chrome/Chromium
- Firefox
- Safari
- Edge 