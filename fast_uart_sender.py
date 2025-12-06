#!/usr/bin/env python3
"""
Fast UART Image Sender for FPGA Image Processor
Optimized for maximum transmission speed
"""

import cv2
import serial
import numpy as np
import time
import argparse
import os
import threading
from queue import Queue

class FastUARTImageSender:
    def __init__(self, port, baud_rate=1250000):
        """
        Initialize the fast UART image sender

        Args:
            port (str): Serial port name (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baud_rate (int): UART baud rate
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.target_width = 640
        self.target_height = 480

    def connect(self):
        """Connect to the UART port with optimized settings"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,         # Reduced timeout for faster operation
                write_timeout=0.1,   # Write timeout to prevent blocking
                # Hardware flow control disabled for maximum speed
                rtscts=False,
                dsrdtr=False
            )

            # Optimize buffer sizes
            self.serial_conn.set_buffer_size(rx_size=4096, tx_size=8192)

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

    def preprocess_image(self, image_path):
        """
        Load and preprocess image for FPGA display (NO ENHANCEMENT)

        Args:
            image_path (str): Path to image file

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

        # Resize to target resolution using faster interpolation
        img_resized = cv2.resize(img_gray, (self.target_width, self.target_height), 
                               interpolation=cv2.INTER_LINEAR)  # Faster than LANCZOS4

        print(f"Processed image shape: {img_resized.shape}")
        return img_resized

    def send_image_chunked(self, image, chunk_size=1024):
        """
        Send image in chunks for maximum speed

        Args:
            image (numpy.ndarray): Grayscale image array
            chunk_size (int): Size of chunks to send at once

        Returns:
            bool: True if successful
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not established")
            return False

        # Flatten image for transmission
        image_data = image.flatten()
        total_pixels = len(image_data)

        print(f"Starting fast image transmission ({total_pixels} pixels)...")
        print("Progress: [", end="", flush=True)

        start_time = time.time()
        sent_pixels = 0

        try:
            # Send data in chunks
            for i in range(0, total_pixels, chunk_size):
                chunk = image_data[i:i+chunk_size]

                # Convert numpy array to bytes
                chunk_bytes = chunk.tobytes()

                # Send entire chunk at once
                bytes_written = self.serial_conn.write(chunk_bytes)
                sent_pixels += len(chunk)

                # Force immediate transmission
                self.serial_conn.flush()

                # Show progress
                if sent_pixels % (total_pixels // 50) == 0:
                    print("█", end="", flush=True)

            print("]")
            elapsed_time = time.time() - start_time
            print(f"Transmission completed in {elapsed_time:.2f} seconds")
            print(f"Transfer rate: {total_pixels/elapsed_time:.0f} pixels/second")
            print(f"Data rate: {(total_pixels/elapsed_time)/1000:.1f} KB/s")
            return True

        except serial.SerialException as e:
            print(f"Error during transmission: {e}")
            return False

    def send_image_burst(self, image, burst_size=4096):
        """
        Send image in large bursts for maximum throughput

        Args:
            image (numpy.ndarray): Grayscale image array  
            burst_size (int): Size of bursts to send

        Returns:
            bool: True if successful
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not established")
            return False

        # Flatten image for transmission
        image_data = image.flatten()
        total_pixels = len(image_data)

        print(f"Starting burst transmission ({total_pixels} pixels)...")
        print("Progress: [", end="", flush=True)

        start_time = time.time()
        sent_pixels = 0

        try:
            # Send in large bursts
            for i in range(0, total_pixels, burst_size):
                burst = image_data[i:i+burst_size]
                burst_bytes = burst.tobytes()

                # Send burst
                self.serial_conn.write(burst_bytes)
                sent_pixels += len(burst)

                # Show progress less frequently for speed
                if sent_pixels % (total_pixels // 20) == 0:
                    print("██", end="", flush=True)

            # Final flush
            self.serial_conn.flush()

            print("]")
            elapsed_time = time.time() - start_time
            print(f"Burst transmission completed in {elapsed_time:.2f} seconds")
            print(f"Transfer rate: {total_pixels/elapsed_time:.0f} pixels/second")
            print(f"Data rate: {(total_pixels/elapsed_time)/1000:.1f} KB/s")
            return True

        except serial.SerialException as e:
            print(f"Error during burst transmission: {e}")
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
    parser = argparse.ArgumentParser(description='Fast UART Image Sender for FPGA')
    parser.add_argument('port', help='Serial port (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--image', '-i', help='Image file to send')
    parser.add_argument('--pattern', '-p', 
                       choices=['gradient', 'checkerboard', 'circles', 'edges'],
                       help='Test pattern to send')
    parser.add_argument('--baud', '-b', type=int, default=1250000, 
                       help='Baud rate (default: 1250000)')
    parser.add_argument('--mode', '-m', choices=['chunked', 'burst'], default='burst',
                       help='Transmission mode (default: burst)')
    parser.add_argument('--chunk-size', type=int, default=1024,
                       help='Chunk size for chunked mode (default: 1024)')
    parser.add_argument('--burst-size', type=int, default=4096,
                       help='Burst size for burst mode (default: 4096)')
    parser.add_argument('--save-patterns', action='store_true',
                       help='Save test patterns as image files')

    args = parser.parse_args()

    # Create sender instance
    sender = FastUARTImageSender(args.port, args.baud)

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
            image = sender.preprocess_image(args.image)
            print(f"Sending image: {args.image}")

            if args.mode == 'chunked':
                sender.send_image_chunked(image, args.chunk_size)
            else:  # burst mode
                sender.send_image_burst(image, args.burst_size)

        elif args.pattern:
            # Send test pattern
            patterns = sender.create_test_patterns()
            if args.pattern in patterns:
                print(f"Sending test pattern: {args.pattern}")

                if args.mode == 'chunked':
                    sender.send_image_chunked(patterns[args.pattern], args.chunk_size)
                else:  # burst mode
                    sender.send_image_burst(patterns[args.pattern], args.burst_size)
            else:
                print(f"Unknown pattern: {args.pattern}")

        else:
            print("Please specify either --image or --pattern")
            print("\nAvailable commands:")
            print("1. Send image (burst mode): python fast_uart_sender.py COM3 --image photo.jpg")
            print("2. Send image (chunked):     python fast_uart_sender.py COM3 --image photo.jpg --mode chunked")
            print("3. Send test pattern:       python fast_uart_sender.py COM3 --pattern gradient")
            print("4. Custom burst size:       python fast_uart_sender.py COM3 --image photo.jpg --burst-size 8192")
            print("5. Save test patterns:      python fast_uart_sender.py COM3 --save-patterns")
            print("\nSpeed Tips:")
            print("- Use burst mode for maximum speed")
            print("- Increase burst-size for faster transfer (try 8192 or 16384)")
            print("- Ensure good USB connection for high baud rates")
            print("\nFPGA Controls:")
            print("- Switches SW[1:0]: Select processing mode")
            print("  00 = Black & White, 01 = Grayscale, 10 = Color, 11 = Sobel") 
            print("- Center Button: Clear display")
            print("- LEDs show transfer progress and system status")

    finally:
        sender.disconnect()

if __name__ == "__main__":
    main()
