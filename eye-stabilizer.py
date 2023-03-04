import cv2
import dlib
import numpy as np
import os
import subprocess
import time
import argparse


class EyeStabilizer:
    def __init__(self, input_video_path, output_folder, skipstabilization):
        if not skipstabilization or input_video:
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor("facial_landmarks/shape_predictor_68_face_landmarks.dat")
            self.cap = cv2.VideoCapture(input_video_path)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.frame_num = 0
            self.avg_time_per_frame = 0
            self.frame_history = {}
        
        os.makedirs(output_folder, exist_ok=True)


    def seconds_to_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"


    def calculate_remaining_time(self, current_time):
        if self.frame_num > 1:
            time_diff = current_time - self.frame_history[self.frame_num - 1]
            self.avg_time_per_frame = ((self.frame_num - 2) * self.avg_time_per_frame + time_diff) / (self.frame_num - 1)

        # Print progress
        remaining_frames = self.total_frames - self.frame_num
        remaining_time_str = self.seconds_to_time(self.avg_time_per_frame * remaining_frames)
        
        return remaining_time_str


    def stabilize(self, output_folder):
        self.frame_num = 0
        self.avg_time_per_frame = 0
        
        while self.cap.isOpened():
            # Read frame from video
            ret, frame = self.cap.read()

            # Check if frame was read correctly
            if not ret:
                break
            
            # Grayscale frame for face detection to speed up the process
            gray = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2GRAY)

            # Detect faces in the frame
            faces = self.detector(gray)
            
            # Check if face was detected in the frame and if so, stabilize it
            if len(faces) > 0:
                # Use the first face returned by the detector
                face = faces[0]
                
                # Increment frame number
                self.frame_num += 1
                
                # Get facial landmarks
                landmarks = self.predictor(image=gray, box=face)

                # coordinates of eyes
                left_eye_coords = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)])
                right_eye_coords = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)])

                #  center of eyes calculation
                left_eye_center = left_eye_coords.mean(axis=0)
                right_eye_center = right_eye_coords.mean(axis=0)

                # and then we calculate angle between eyes
                eyes_centered = np.average([left_eye_center, right_eye_center], axis=0)

                # direction of eyes x, y
                shift_image = (frame.shape[1] // 2 - int(eyes_centered[0]), frame.shape[0] // 2 - int(eyes_centered[1]))

                # translation matrix for shifting the image to the center of eyes
                translation = np.float32([[1, 0, int(shift_image[0])], [0, 1, int(shift_image[1])]])
                
                # apply it to the og image
                original_frame = cv2.warpAffine(frame, translation, frame.shape[1::-1])

                # save the frame
                cv2.imwrite(f"{output_folder}/frame_{self.frame_num}.jpg", original_frame)

            else:
                self.frame_num += 1
                # No faces were detected - save original frame without modifications
                cv2.imwrite(f"{output_folder}/frame_{self.frame_num}.jpg", frame)

            # the exact current time
            current_time = time.perf_counter()
            
            # store it in frame histort dic
            self.frame_history[self.frame_num] = current_time

            # remaining time is calculated
            remaining_time = self.calculate_remaining_time(current_time)
            
            print(f"Stabilizing frame {self.frame_num} of {self.total_frames} to '{output_folder}' | Time remaining: {remaining_time}", end="\r", flush=True)



        # Release resources
        self.cap.release()
        
        print(f"Stabilization done!" + (' ' * 65), flush=True)
        
        
    def create_final_video(self, input_video_path, output_video_path, stabilized_images_path, fps):
        # create ffmpeg command
        if fps is None:
            fps = self.fps

        if input_video_path is None:
            command = ['ffmpeg', '-y', '-framerate', f"{fps}", '-start_number', '1', '-i', os.path.join(stabilized_images_path, 'frame_%d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', output_video_path]
        else:
            command = ['ffmpeg', '-y', '-framerate', f"{fps}", '-start_number', '1', '-i', os.path.join(stabilized_images_path, 'frame_%d.jpg'), '-i', input_video_path, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', output_video_path]

        # ffmpeg command
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )

        # used so it stays in one line and we can see the progress
        for line in iter(process.stdout.readline, ''):
            if "frame=" in line:
                print("Merging frames into video... " + line.strip()[:28], end='\r', flush=True)

        print(f"Merging done!" + (' ' * 65), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-ss', '--skipstabilization', action='store_true', help='turn stabilizer off')
    parser.add_argument('-i', '--input', help='input video path')
    parser.add_argument('-o', '--output', help='output video path')
    # parser.add_argument('-db', '--debug', help='output video path')

    # Parse the command-line arguments
    args = parser.parse_args()
    
    # get input and output video paths
    input_video = parser.parse_args().input
    output_video_path = parser.parse_args().output
    stabilized_images_path = "stabilized_images"
    
    # first checks if -ss is true because then it doesnt need an input path
    if not parser.parse_args().skipstabilization:
        if input_video is None or output_video_path is None:
            print('You need to specify an input and output path! (Use -i and -o)')
            exit(1)
    else: 
        if output_video_path is None:
            print('You need to specify an output path! (Use -o)')
            exit(1)    
        
    
    stabilizer = EyeStabilizer(input_video, stabilized_images_path, parser.parse_args().skipstabilization)

    fps = None
    if args.skipstabilization:
        print('Skipping stabilizing...')
        if not input_video:
            fps = str(input('What is the desired FPS for the output video? '))
    else:
        stabilizer.stabilize(stabilized_images_path)
        
    stabilizer.create_final_video(input_video, output_video_path, stabilized_images_path, fps)
