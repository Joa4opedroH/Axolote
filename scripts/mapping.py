from PIL import Image as img
from PIL.ExifTags import TAGS, GPSTAGS
import sys
import os
import time
import argparse
import math
import numpy as np
import cv2
import piexif
from fractions import Fraction
from decimal import Decimal, getcontext
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("mapping.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Fix for Python 3.10+ compatibility with DroneKit
import collections
import collections.abc
if not hasattr(collections, 'MutableMapping'):
    collections.MutableMapping = collections.abc.MutableMapping
if not hasattr(collections, 'Mapping'):
    collections.Mapping = collections.abc.Mapping
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable

from dronekit import connect, VehicleMode, LocationGlobalRelative, mavutil

TIMER_INTERVAL = 0.5  # seconds

class Mapping():
    """Gets video capture and saves images with gps metadata for map creation using DroneKit
    
    Attributes
    ----------
    vehicle : dronekit.Vehicle
        the connected drone vehicle

    quantidade_fotos : int
        the quantity of saved photos

    global_pose : LocationGlobalRelative
        vehicle global position
        
    timer_interval : float
        desired capture interval in seconds between photos
        
    cap : cv2.VideoCapture
        main images source
    
    capture1 : cv2.VideoCapture
        secondary images source
    
    current_capture : cv2.VideoCapture
        the current images source
    
    script_dir : str
        the script directory name 

    image_dir : str
        the directory name where images will be saved
    
    last_save_time : float
        the time when last image was saved

    Methods
    -------
    save_pictures() : None
        Saves pictures taken by a video capture
    
    float_to_rational(f) : int, int
        transforms a number into a fraction, returning both numerator and denominator

    add_gps_metadata(image_path, latitude, longitude, altitude) : None
        add gps metadata to its correspondent image
    
    check_camera() : bool
        check if the video capture is working well
 
    run() : None
        runs the mapping  
    """

    def __init__(self, connection_string='/dev/ttyACM1'):
        # Connect to the physical drone
        logger.info(f"Connecting to drone on: {connection_string}")
        self.vehicle = None

        try:
            # Connect without wait_ready to avoid blocking on GPS
            logger.info("Establishing connection...")
            self.vehicle = connect(connection_string, wait_ready=False, timeout=30)
            logger.info("✓ Drone connected successfully!")
            
            # Wait for GPS fix with proper interrupt handling
            logger.info("Waiting for GPS fix...")
            while True:
                if self.vehicle.gps_0.fix_type >= 2:
                    logger.info("GPS fix acquired!")
                    break
                logger.info(f" GPS: {self.vehicle.gps_0.fix_type} (waiting for fix)")
                time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Setup interrupted by user")
            if self.vehicle:
                self.vehicle.close()
                logger.info("Resources cleaned up")
            raise
        except Exception as e:
            logger.info(f"ERROR: Failed to connect to drone: {e}")
            logger.info(f"Connection used: {connection_string}")
            logger.info("\nTroubleshooting:")
            logger.info("  1. Check if drone/autopilot is connected and powered")
            logger.info("  2. Check USB cable connection")
            logger.info("  3. Verify device path: ls -la /dev/tty*")
            logger.info("  4. Check permissions: sudo chmod 666 /dev/ttyACM0")
            logger.info("  5. Make sure no other software is using the connection")
            raise
        
        self.quantidade_fotos = 0
        self.global_pose = None
        
        # Mapping configuration parameters
        self.timer_interval = TIMER_INTERVAL  # Desired interval in seconds between photo
        
        # Initialize both cameras
        self.cap0 = cv2.VideoCapture(0)  # First camera (video0)
        self.cap1 = cv2.VideoCapture(-1) # Last camera (video -1)
        self.current_capture = self.cap0  # Set the current capture source
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.image_dir = os.path.join(self.script_dir, "images_30-10")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        
        self.last_save_time = time.time()  # Initialize the time of the last save

    @staticmethod
    def float_to_rational(f) -> tuple[int, int]:
        """transforms a number into a fraction, returning both numerator and denominator

        Parameters
        ----------
        f : Any
            a number
        
        Returns
        -------
        tuple
            a tuple of int containing both fraction numerator and denominator
        """
        f = Fraction(f).limit_denominator()
        return f.numerator, f.denominator

    def save_pictures(self) -> None:
        """Saves pictures taken by video capture with correspondent gps metadata"""
        # Get current GPS position and altitude from DroneKit
        if self.vehicle.location.global_frame is not None:
            longitude = self.vehicle.location.global_frame.lon
            latitude = self.vehicle.location.global_frame.lat
            altitude = self.vehicle.location.global_relative_frame.alt if self.vehicle.location.global_relative_frame else None
            name = os.path.join(self.image_dir, "oficial%d.jpg" % self.quantidade_fotos)

            cv2.imwrite(name, self.cam_frame)
            self.add_gps_metadata(name, latitude, longitude, altitude)
            logger.info("Image " + str(self.quantidade_fotos) + " at lat: " + str(latitude) + ", long: " + str(longitude) + 
                  (f", alt: {altitude:.1f}m" if altitude is not None else ""))
            self.quantidade_fotos += 1
        else:
            logger.info("Warning: GPS location not available, skipping image save")

    def add_gps_metadata(self, image_path: str, latitude: float, longitude: float, altitude: float = None) -> None:
        """add gps metadata to its correspondent image
        
        Parameters
        ----------
        image_path : str
            path to the folder where the images will be saved

        latitude, longitude : float
            latitude and longitude coordinates
            
        altitude : float, optional
            altitude in meters
        """
        exif_dict = piexif.load(image_path)

        lat_deg = abs(latitude)
        lat_min, lat_sec = divmod(lat_deg * 3600, 60)
        lat_deg, lat_min = divmod(lat_min, 60)
        lat_ref = 'N' if latitude >= 0 else 'S'

        lon_deg = abs(longitude)
        lon_min, lon_sec = divmod(lon_deg * 3600, 60)
        lon_deg, lon_min = divmod(lon_min, 60)
        lon_ref = 'E' if longitude >= 0 else 'W'

        lat_deg_num, lat_deg_den = self.float_to_rational(lat_deg)
        lat_min_num, lat_min_den = self.float_to_rational(lat_min)
        lat_sec_num, lat_sec_den = self.float_to_rational(lat_sec)

        lon_deg_num, lon_deg_den = self.float_to_rational(lon_deg)
        lon_min_num, lon_min_den = self.float_to_rational(lon_min)
        lon_sec_num, lon_sec_den = self.float_to_rational(lon_sec)

        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSLatitudeRef: lat_ref,
            piexif.GPSIFD.GPSLatitude: ((lat_deg_num, lat_deg_den), (lat_min_num, lat_min_den), (lat_sec_num, lat_sec_den)),
            piexif.GPSIFD.GPSLongitudeRef: lon_ref,
            piexif.GPSIFD.GPSLongitude: ((lon_deg_num, lon_deg_den), (lon_min_num, lon_min_den), (lon_sec_num, lon_sec_den)),
        }

        # Add altitude if available
        if altitude is not None:
            alt_num, alt_den = self.float_to_rational(abs(altitude))
            gps_ifd[piexif.GPSIFD.GPSAltitude] = (alt_num, alt_den)
            gps_ifd[piexif.GPSIFD.GPSAltitudeRef] = 0  # 0 = above sea level, 1 = below sea level

        exif_dict['GPS'] = gps_ifd

        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y:%m:%d %H:%M:%S")

        exif_dict['0th'][piexif.ImageIFD.DateTime] = timestamp_str
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = timestamp_str
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = timestamp_str

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, image_path)

        logger.info("GPS metadata added to the image.")

    def check_camera(self) -> bool:
        """check if the video capture is working well

        Returns
        -------
        bool
            True if video capture is ok, False otherwise
        """
        success, self.cam_frame = self.current_capture.read()
        
        return success

    def run(self) -> None:
        """runs the mapping"""
        CAMERA_COUNT = 0
        try:
            
            logger.info(f"Starting mapping with configuration:")
            logger.info(f"  - Photo interval: {self.timer_interval}s")
  
            while True:
                # Take photos at intervals while mapping is active
                current_time = time.time()
                elapsed_time = current_time - self.last_save_time

                if elapsed_time >= self.timer_interval:
                    if self.check_camera():
                        logger.info("Timer triggered - taking photo")
                        self.save_pictures()
                        CAMERA_COUNT = 0
                    else:
                        logger.warning("Camera not found...")
                        CAMERA_COUNT += 1

                        if CAMERA_COUNT > 50:
                            logger.warning("Cameras not working at all")
                            break

                        if self.current_capture == self.cap0:
                            logger.info("Changing to video capture 1")
                            self.current_capture = self.cap1
                        elif self.current_capture == self.cap1:
                            logger.info("Changing to video capture 0")
                            self.current_capture = self.cap0

                        # If you're having this problem, check:
                        # 1. If the camera is connected with data cable
                        # 2. Run lsusb to see if the camera is listed (see: ICatchTek)
                        # 3. If everything is ok, then I hope the camera is with a SD card, or you're doomed...

                    self.last_save_time = time.time()  # Update the last save time
                else:
                    time.sleep(self.timer_interval - elapsed_time)
                    
        except KeyboardInterrupt:
            logger.info("Mapping interrupted by user")
        finally:
            # Clean up
            self.cap0.release()
            self.cap1.release()
            self.vehicle.close()
            logger.info("Resources cleaned up")

if __name__ == '__main__':
    try:
        mapping = Mapping()
        mapping.run()
    except KeyboardInterrupt:
        # Exit gracefully on Ctrl+C without showing traceback
        sys.exit(0)
