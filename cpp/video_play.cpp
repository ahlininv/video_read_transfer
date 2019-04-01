//
// Created by ahlininv on 22.03.19.
//

#include "opencv2/opencv.hpp"
#include <iostream>

using namespace std;
using namespace cv;

struct PackedFrame {
    uint64_t size; // size in bytes
    uint64_t packet_pts; // todo max len of video check later
    uint8_t shape[3];
    std::vector<uint8_t> data;
};

const PackedFrame packet_pack(const Mat& frame, uint64_t pts)
{
    PackedFrame packet;
    uint64_t packet_size = frame.dataend - frame.datastart;
    packet.size = sizeof(packet.size) + sizeof(packet.packet_pts) + sizeof(packet.shape) + packet_size;
    packet.packet_pts = pts;
    packet.shape[0] = frame.rows;
    packet.shape[1] = frame.cols;
    packet.shape[2] = frame.total();
    packet.data.resize(packet_size);
    memcpy(&(packet.data[0]), frame.data, packet_size);
}

int main(){

    // Create a VideoCapture object and open the input file
    // If the input is the web camera, pass 0 instead of the video file name
    VideoCapture cap("/home/ahlininv/Desktop/tantum.avi");

    // Check if camera opened successfully
    if(!cap.isOpened()){
        cout << "Error opening video stream or file" << endl;
        return -1;
    }

    while(1){

        Mat frame;
        // Capture frame-by-frame
        cap >> frame;
        std::cout << "Total: " << frame.total() << ", " << frame.dataend - frame.datastart << " between them, shape:" << frame.rows << "x" << frame.cols << "x" << frame.depth() << "\n";

        // If the frame is empty, break immediately
        if (frame.empty())
            break;

        // Display the resulting frame
        imshow( "Frame", frame );

        // Press  ESC on keyboard to exit
        char c=(char)waitKey(25);
        if(c==27)
            break;
    }

    // When everything done, release the video capture object
    cap.release();

    // Closes all the frames
    destroyAllWindows();

    return 0;
}
