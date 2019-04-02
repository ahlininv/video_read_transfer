/**
 * Created by ahlininv on 22.03.19.
 * Grabs video from source and sends to display.
 */

#include "opencv2/opencv.hpp"
#include <iostream>

using namespace std;
using namespace cv;

struct PackedFrameHeader {
    uint64_t packet_pts; // max len of video is 2^64 frames
    uint8_t rows;
    uint8_t cols;
    uint8_t channels;
};

PackedFrameHeader pack_header(const Mat& frame, uint64_t pts)
{
    PackedFrameHeader header;
    header.packet_pts = pts;
    header.rows = frame.rows;
    header.cols = frame.cols;
    header.channels = frame.channels();
    return header;
//    return PackedFrameHeader{pts, (uint8_t)frame.rows, (uint8_t)frame.cols, (uint8_t)frame.channels()};
}

Mat unpack_header(uchar* header_data, uint64_t& pts) {
    PackedFrameHeader* header;
    header = (PackedFrameHeader*)header_data;
    pts = header->packet_pts;
    std::cerr << "rows: " << header->rows << " cols: " << header->cols << " channels: " << header->channels << "\n";
    Mat fr(header->rows, header->cols, CV_MAKETYPE(CV_8U, header->channels));
    if (!fr.isContinuous())
        fr = fr.clone();
    return fr;
}


int main() {
    // Create a VideoCapture object and open the input file
    // If the input is the web camera, pass 0 instead of the video file name
    VideoCapture cap("/home/ahlininv/Desktop/tantum.avi");

    // Check if camera opened successfully
    if(!cap.isOpened()){
        cout << "Error opening video stream or file" << endl;
        return -1;
    }
    uint64_t pts = 0;
    uint64_t received_pts = -1;
    while(1){
        Mat frame;
        // Capture frame-by-frame
        cap >> frame;
        std::cout << "\nRead: " << frame.total() << " " << frame.dataend - frame.datastart << " " << frame.cols << "x" << frame.rows << " " << frame.channels() << " bits for pixel\n";
        // If the frame is empty, break immediately
        if (frame.empty())
            break;

        // Packing for send
        PackedFrameHeader header = pack_header(frame, pts);
        std::cout << "Packed: rows: " << header.rows << " cols: " << header.cols << " channels: " << header.channels << "\n";
        uchar* header_to_network = new uchar[sizeof(PackedFrameHeader)];
        memcpy(header_to_network, (uchar*)&header, sizeof(PackedFrameHeader));

        size_t data_size = header.rows * header.cols * header.channels;
        uchar* data_to_network = new uchar[data_size];
        memcpy(data_to_network, frame.data, data_size);

        // Network emulation
        uchar* header_from_network = header_to_network;
        uchar* data_from_network = data_to_network;

        // Receiving, unpacking
        Mat received_frame = unpack_header(header_to_network, received_pts);
        received_frame.data = data_from_network;
        std::cerr << "Received : " << received_frame.total()<< " " << received_frame.dataend - received_frame.datastart << " " << received_frame.cols << "x" << received_frame.rows << " " << received_frame.channels() << " bits for pixel\n";


        // Display the resulting frame
        imshow( "Frame", received_frame );
        ++pts;

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
