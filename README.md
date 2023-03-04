# py-eye-stabilizer
This is a Python script designed to reduce the shakiness of video footage by identifying and aligning the eyes in each frame with the center of the frame. While this technique can help stabilize video, it may not produce the same level of stabilization as a commercial video editing software. Nonetheless, this project can be a fun and interesting exercise in image processing and video stabilization techniques.


![](example.gif)

# Installation
To run the Eye Stabilizer, you will need to install the following packages:
* OpenCV
* dlib
* numpy

These can be installed using pip:
`pip install opencv-python dlib numpy`

Remember to install CMake to get dlib to work.

To get the facial landmark detector to work, you must install 'shape_predictor_68_face_landmarks.dat' from 'https://github.com/italojs/facial-landmarks-recognition/blob/master/shape_predictor_68_face_landmarks.dat', and put it inside a folder called "facial_landmarks" in the project.

# Usage
To use the Eye Stabilizer, simply run the eyestabilizer.py script and specify the path to your input video file and the output folder where the stabilized frames will be saved:

`python eye-stabilizer.py -i path/to/video.mp4 -o path/to/video.mp4` (You can also use .mkv for example)

There is also an option to skip the stabilization and go straight to the images -> video by doing:

`python eye-stabilizer.py -o path/to/video.mp4 -ss` (If you specify -i while doing -ss, it will use the audio from the -i video)

# Contributing
If you find any bugs or issues with the Eye Stabilizer, please open a GitHub issue or submit a pull request with your proposed changes.
