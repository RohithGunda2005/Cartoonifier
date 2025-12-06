# Enhanced FPGA Image Processor with Progress Indication

This is an enhanced version of the FPGA-based image processor with the following new features:

## 🆕 New Features

### 1. **Progression LEDs**
- **LEDs 4-7**: Show real-time transfer progress (25%, 50%, 70%, 90%+)
- **LED 8**: Transfer active indicator (fast blinking during transmission)
- **LED 12**: UART activity indicator (lights up on each received byte)
- **LED 14**: Frame completion indicator

### 2. **Clear Button Functionality**
- **Center Button (U18)**: Press to clear the current display
- **LED 9**: Clear operation indicator (fast blinking during clear)
- Clears entire framebuffer to black for sending new images

### 3. **Live Mode Change Indication**
- **LED 10**: Mode change indicator (slow blinking when mode switches)
- **LEDs 0-3**: Still show current mode (one-hot encoding)
- Immediate visual feedback when switching modes with SW[1:0]

### 4. **Enhanced Color Levels**
- **Grayscale Mode**: Increased from 4 to 8 gradient levels
- **Color Mode**: Enhanced from 8 to 16 color levels with smooth transitions
- **VGA Output**: Full 4-bit per channel RGB (4096 colors total)

### 5. **Additional Status LEDs**
- **LED 11**: System ready (PLL locked)
- **LED 13**: Frame data present indicator
- **LED 15**: VGA active indicator

## 🎛️ User Interface

### Switches
- **SW[1:0]**: Mode selection
  - `00`: Black & White mode
  - `01`: Enhanced Grayscale (8 levels)
  - `10`: Enhanced Color (16 levels)
  - `11`: Sobel Edge Detection

### Button
- **Center Button**: Clear display

### LED Indicators (16 LEDs total)
```
LEDs 0-3:   Mode indicators (one-hot)
LEDs 4-7:   Transfer progress (fills up during transmission)
LED 8:      Transfer active (fast blink)
LED 9:      Clear active (fast blink)
LED 10:     Mode changed (slow blink)
LED 11:     System ready
LED 12:     UART activity
LED 13:     Frame data present
LED 14:     Frame complete
LED 15:     VGA active
```

## 🚀 Usage Instructions

### 1. Hardware Setup
1. Program the FPGA with the enhanced design using `main_modified.v`
2. Use the updated pin constraints from `constraints_modified.xdc`
3. Connect VGA monitor and UART cable

### 2. Sending Images

#### Using the Enhanced Python Script
```bash
# Send an image file
python uart_image_sender_enhanced.py COM3 --image photo.jpg --enhance

# Generate and send test patterns
python uart_image_sender_enhanced.py COM3 --pattern gradient
python uart_image_sender_enhanced.py COM3 --pattern checkerboard
python uart_image_sender_enhanced.py COM3 --pattern circles
python uart_image_sender_enhanced.py COM3 --pattern edges

# Save test patterns to files
python uart_image_sender_enhanced.py COM3 --save-patterns
```

#### Available Test Patterns
- **gradient**: Horizontal intensity gradient (good for testing grayscale levels)
- **checkerboard**: Alternating black/white squares (good for B&W mode)
- **circles**: Concentric circles (good for edge detection)
- **edges**: Horizontal and vertical lines (excellent for Sobel mode)

### 3. Observing the Enhancements

1. **Transfer Progress**: Watch LEDs 4-7 fill up during image transmission
2. **Mode Changes**: Switch SW[1:0] and see LED 10 blink, plus immediate mode change on LEDs 0-3
3. **Clear Function**: Press center button and watch LED 9 blink while display clears
4. **Enhanced Colors**: 
   - Try grayscale mode with gradient pattern to see 8 levels
   - Use color mode to see 16-level false color mapping

## 📁 File Structure

### Modified Files
- `main_modified.v` - Enhanced main module with all new features
- `constraints_modified.xdc` - Updated pin constraints for 16 LEDs and clear button
- `uart_image_sender_enhanced.py` - Enhanced Python sender with progress and test patterns

### Original Files (unchanged)
- `uart_rx.v` - UART receiver module
- `vga_640x480.v` - VGA timing controller
- `clock_gen_basys3.v` - Clock generation
- `sobel3x3_stream.v` - Sobel edge detection
- `debounce_onepulse.v` - Button debouncing
- Other support modules (FIFOs, BRAM, etc.)

## 🎨 Color Mode Details

### Enhanced Grayscale (Mode 01)
- 8 distinct intensity levels
- Smooth gradations from black to white
- Values: 32, 64, 96, 128, 160, 192, 224, 255

### Enhanced False Color (Mode 10)
16-level mapping with spectrum-like progression:
```
Level 0:  Black
Level 1:  Dark Blue
Level 2:  Blue
Level 3:  Cyan-Blue
Level 4:  Cyan
Level 5:  Green-Cyan
Level 6:  Green
Level 7:  Yellow-Green
Level 8:  Yellow
Level 9:  Orange-Yellow
Level 10: Orange
Level 11: Red-Orange
Level 12: Red
Level 13: Magenta-Red
Level 14: Magenta
Level 15: White
```

## 🔧 Technical Improvements

- **Better Progress Tracking**: Pixel counter tracks exact transfer progress
- **Mode Change Detection**: Compares current and previous mode states
- **Enhanced Debouncing**: Proper button debouncing for clear function
- **Optimized Memory Management**: Efficient clear operation using address counter
- **Real-time Status**: Multiple status indicators for system debugging
- **Clock Domain Management**: Proper handling of different clock domains

## 🎯 Testing Recommendations

1. **Start with test patterns** to verify all modes work correctly
2. **Try the gradient pattern** in grayscale mode to see enhanced levels
3. **Use the edges pattern** in Sobel mode for best edge detection demo
4. **Test mode switching** while pattern is displayed to see live changes
5. **Use clear button** between different images for clean transitions

This enhanced system provides much better user feedback and improved visual quality compared to the original design!
