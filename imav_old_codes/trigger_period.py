'''
Code to obtain the period to take a picture during drone mapping
'''

def picture_period(velocity, overlap, drone_height, sensor_height, focal_length):
    # Be theta the angle of view of the camera over two
    tan_theta = sensor_height / (2 * focal_length)
    
    # Vertical size of the picture on the ground
    vertical_size = 2 * tan_theta * drone_height

    # Period to take a picture
    period = (1 - overlap) * vertical_size / velocity

    return period

if __name__ == "__main__":
    # Runcam 5 parameters
    velocity = 3.0  # meters per second
    overlap = 0.85   # 70% overlap
    drone_height = 15  # meters
    sensor_height = 3.6  # mm
    focal_length = 2.1   # mm

    period = picture_period(velocity, overlap, drone_height, sensor_height, focal_length)
    print(f"Picture taking period: {period:.2f} seconds")