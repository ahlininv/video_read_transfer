/**
 * OpenCV video streaming over TCP/IP
 * Server: Captures video from a webcam and send it to a client
 * by Isaac Maia
 */

#include "opencv2/opencv.hpp"
#include <iostream>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <string.h>
#include <thread>

using namespace cv;

//VideoCapture cap("/home/ahlininv/Desktop/tantum.avi"); // open the default camera
VideoCapture cap("./../../python/tests/test_video.avi"); // open the default camera


void play_to_network(int socket, int thread_id/*, VideoCapture cap*/) {
    Mat frame = Mat::zeros(360 , 640, CV_8UC3);
    Mat frame_gray;

    // make it continuous
    if (!frame.isContinuous()) {
        frame = frame.clone();
        frame_gray = frame.clone();
    }

    int frame_length = frame.total() * frame.elemSize();
    std::cout << "Image Size:" << frame.total() * frame.elemSize() << " " << frame.channels() << std::endl;

    // Check if camera opened successfully
    if(!cap.isOpened()) {
        std::cout << "Error opening video stream or file" << std::endl;
        exit(-1);
    }

    int bytes = 0;
    while (1) {
        cap >> frame;
        if (frame.empty()) {
            std::cerr << "Video is over\n";
            exit(0);
        }

//        std::cout << "Image Size:" << frame.total() * frame.elemSize() << " " << frame.channels() << std::endl;

        // process image if needed
        cvtColor(frame, frame_gray, CV_BGR2GRAY);

        //send processed image
        const Mat& frame_to_send = frame;
        frame_length = frame_to_send.total() * frame_to_send.elemSize();
        if ((bytes = send(socket, frame_to_send.data, frame_length, 0)) < 0) {
             std::cerr << "bytes = " << bytes << std::endl;
             break;
        }
    }
}


int main(int argc, char** argv)
{

    //networking stuff
    int local_socket;
    int remote_socket;
    int port = 8886;

    struct  sockaddr_in local_addr, remote_addr;

    int addr_len = sizeof(struct sockaddr_in);

    if ( (argc > 1) && (strcmp(argv[1],"-h") == 0) ) {
          std::cerr << "usage: ./cv_video_srv <port> <file or stream>\n" <<
                       "port           : socket port (4097 default)\n" <<
                       "file or stream : (0 default)\n" << std::endl;

          exit(1);
    }

    if (argc == 2) port = atoi(argv[1]);

    local_socket = socket(AF_INET , SOCK_STREAM , 0);
    if (local_socket == -1){
         perror("socket() call failed!!");
    }

    local_addr.sin_family = AF_INET;
    local_addr.sin_addr.s_addr = INADDR_ANY;
    local_addr.sin_port = htons( port );

    if( bind(local_socket,(struct sockaddr *)&local_addr , sizeof(local_addr)) < 0) {
         perror("Can't bind() socket");
         exit(1);
    }

    //Listening
    listen(local_socket , 3);

    std::cout <<  "Waiting for connections...\n"
              <<  "Server Port:" << port << std::endl;

    //accept connection from an incoming client
    while(1){
        remote_socket = accept(local_socket, (struct sockaddr *)&remote_addr, (socklen_t*)&addr_len);

        if (remote_socket < 0) {
            perror("accept failed!");
            exit(1);
        }
        std::cout << "Connection accepted" << std::endl;
        assert(cap.isOpened());
        std::thread t0(play_to_network, remote_socket, 0/*, cap*/);
//        std::thread t1(1, play_to_network, remote_socket/*, cap*/);
        t0.join();
//        t1.join();

    }
    close(remote_socket);

    return 0;
}

