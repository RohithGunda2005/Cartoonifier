#!/usr/bin/env python3
"""
Enhanced UART Image Sender for FPGA Image Processor
Compatible with the original UART settings
"""

import cv2
import serial
import numpy as np
import time
import argparse
import os
from pathlib import Path

class EnhancedUARTImageSender:
    def __init__(self, port, baud_rate=1250000):  # Use original baud rate
        """
        Initialize the UART image sender

        Args:
            port (str): Serial port name (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baud_rate (int): UART baud rate (1,250,000 for compatibility)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.target_width = 640
        self.target_height = 480

    def connect(self):
        """Connect to the UART port"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            print(f"Connected to {self.port} at {self.baud_rate} baud")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        """Disconnect from the UART port"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Disconnected from serial port")

    def preprocess_image(self, image_path, enhance_contrast=True):
        """
        Load and preprocess image for FPGA display

        Args:
            image_path (str): Path to image file
            enhance_contrast (bool): Whether to enhance contrast for better processing

        Returns:
            numpy.ndarray: Preprocessed grayscale image
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")

        print(f"Original image shape: {img.shape}")

        # Convert to grayscale
        if len(img.shape) == 3:
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            img_gray = img

        # Resize to target resolution
        img_resized = cv2.resize(img_gray, (self.target_width, self.target_height), 
                               interpolation=cv2.INTER_LANCZOS4)

        if enhance_contrast:
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img_resized = clahe.apply(img_resized)

        print(f"Processed image shape: {img_resized.shape}")
        return img_resized

    def send_image_with_progress(self, image, delay_ms=0):
        """
        Send image to FPGA with progress indication

        Args:
            image (numpy.ndarray): Grayscale image array
            delay_ms (int): Delay between pixels in milliseconds

        Returns:
            bool: True if successful
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not established")
            return False

        total_pixels = image.size
        sent_pixels = 0

        print(f"Starting image transmission ({total_pixels} pixels)...")
        print("Progress: [", end="", flush=True)

        start_time = time.time()

        try:
            # Send pixels row by row
            for y in range(image.shape[0]):
                for x in range(image.shape[1]):
                    pixel_value = image[y, x]

                    # Send pixel as single byte
                    self.serial_conn.write(bytes([pixel_value]))
                    sent_pixels += 1

                    # Show progress
                    if sent_pixels % (total_pixels // 50) == 0:
                        print("█", end="", flush=True)

                    # Optional delay for slower transmission
                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000.0)

            print("]")
            elapsed_time = time.time() - start_time
            print(f"Transmission completed in {elapsed_time:.2f} seconds")
            print(f"Transfer rate: {total_pixels/elapsed_time:.0f} pixels/second")
            return True

        except serial.SerialException as e:
            print(f"Error during transmission: {e}")
            return False

    def create_test_patterns(self):
        """Create test patterns for demonstrating different processing modes"""
        patterns = {}

        # Gradient test pattern
        gradient = np.zeros((self.target_height, self.target_width), dtype=np.uint8)
        for x in range(self.target_width):
            gradient[:, x] = int(255 * x / self.target_width)
        patterns['gradient'] = gradient

        # Checkerboard pattern
        checkerboard = np.zeros((self.target_height, self.target_width), dtype=np.uint8)
        square_size = 40
        for y in range(0, self.target_height, square_size):
            for x in range(0, self.target_width, square_size):
                if ((x // square_size) + (y // square_size)) % 2 == 0:
                    checkerboard[y:y+square_size, x:x+square_size] = 255
        patterns['checkerboard'] = checkerboard

        # Circular pattern
        center_y, center_x = self.target_height // 2, self.target_width // 2
        y, x = np.ogrid[:self.target_height, :self.target_width]
        dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        circles = ((dist % 50) < 25).astype(np.uint8) * 255
        patterns['circles'] = circles

        # Edge detection test pattern
        edges = np.zeros((self.target_height, self.target_width), dtype=np.uint8)
        # Horizontal edges
        edges[100:110, :] = 255
        edges[200:210, :] = 255
        edges[300:310, :] = 255
        # Vertical edges
        edges[:, 100:110] = 255
        edges[:, 300:310] = 255
        edges[:, 500:510] = 255
        patterns['edges'] = edges

        return patterns

    def save_test_patterns(self, output_dir="test_patterns"):
        """Save test patterns as image files"""
        patterns = self.create_test_patterns()

        os.makedirs(output_dir, exist_ok=True)

        for name, pattern in patterns.items():
            filename = os.path.join(output_dir, f"{name}.png")
            cv2.imwrite(filename, pattern)
            print(f"Saved {filename}")

        return patterns

def main():
    parser = argparse.ArgumentParser(description='Enhanced UART Image Sender for FPGA')
    parser.add_argument('port', help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--image', '-i', help='Image file to send')
    parser.add_argument('--pattern', '-p', 
                       choices=['gradient', 'checkerboard', 'circles', 'edges'],
                       help='Test pattern to send')
    parser.add_argument('--baud', '-b', type=int, default=1250000, 
                       help='Baud rate (default: 1250000)')
    parser.add_argument('--delay', '-d', type=int, default=0,
                       help='Delay between pixels in milliseconds')
    parser.add_argument('--enhance', action='store_true',
                       help='Enhance image contrast')
    parser.add_argument('--save-patterns', action='store_true',
                       help='Save test patterns as image files')

    args = parser.parse_args()

    # Create sender instance
    sender = EnhancedUARTImageSender(args.port, args.baud)

    # Save test patterns if requested
    if args.save_patterns:
        sender.save_test_patterns()
        print("Test patterns saved. You can now send them with --image option.")
        return

    # Connect to UART
    if not sender.connect():
        return

    try:
        if args.image:
            # Send image file
            image = sender.preprocess_image(args.image, args.enhance)
            print(f"Sending image: {args.image}")
            sender.send_image_with_progress(image, args.delay)

        elif args.pattern:
            # Send test pattern
            patterns = sender.create_test_patterns()
            if args.pattern in patterns:
                print(f"Sending test pattern: {args.pattern}")
                sender.send_image_with_progress(patterns[args.pattern], args.delay)
            else:
                print(f"Unknown pattern: {args.pattern}")

        else:
            print("Please specify either --image or --pattern")
            print("\nAvailable commands:")
            print("1. Send image file: python uart_image_sender_enhanced.py COM3 --image photo.jpg")
            print("2. Send test pattern: python uart_image_sender_enhanced.py COM3 --pattern gradient")
            print("3. Save test patterns: python uart_image_sender_enhanced.py COM3 --save-patterns")
            print("\nFPGA Controls:")
            print("- Switches SW[1:0]: Select processing mode")
            print("  00 = Black & White, 01 = Grayscale, 10 = Color, 11 = Sobel")
            print("- Center Button: Clear display")
            print("- LEDs show transfer progress and system status")

    finally:
        sender.disconnect()

if __name__ == "__main__":
    main()
