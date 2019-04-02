/**
 * OpenCV video streaming over TCP/IP
 * Client: Receives and displays video from server
 * Created by Victor Akhlynin (ahlininv@gmail.com), 2019
 */

#include "opencv2/opencv.hpp"
#include <arpa/inet.h>

#include <sys/socket.h>
#include <unistd.h>

using namespace cv;

int main(int argc, char** argv)
{
    int sock;
    char* server_ip;
    int serverPort;

    if (argc < 3) {
           std::cerr << "Usage: cv_video_cli <serverIP> <serverPort> " << std::endl;
    }

    server_ip   = argv[1];
    serverPort = atoi(argv[2]);

    struct  sockaddr_in server_addr;
    socklen_t addrLen = sizeof(struct sockaddr_in);

    if ((sock = socket(PF_INET, SOCK_STREAM, 0)) < 0) {
        std::cerr << "socket() failed" << std::endl;
    }

    server_addr.sin_family = PF_INET;
    server_addr.sin_addr.s_addr = inet_addr(server_ip);
    server_addr.sin_port = htons(serverPort);

    if (connect(sock, (sockaddr*)&server_addr, addrLen) < 0) {
        std::cerr << "connect() failed!" << std::endl;
    }

    Mat frame = Mat::zeros(360 , 640, CV_8UC3);
    int frame_length = frame.total() * frame.elemSize();
    uchar *data_ptr = frame.data;

    //make img continuous
    if (!frame.isContinuous()) {
          frame = frame.clone();
    }

    std::cout << "Image Size:" << frame_length << std::endl;

    namedWindow("CV Video Client", 1);

    int bytes = 0;
    while (1) {
//        std::cerr << "w";

        if ((bytes = recv(sock, data_ptr, frame_length , MSG_WAITALL)) == -1) {
            std::cerr << "recv failed, received bytes = " << bytes << std::endl;
        }

        cv::imshow("CV Video Client", frame);

        if (char key = (char)cv::waitKey(25)) {
//            std::cerr << "waiting is over\n";
            if (key == 27 || key == 'q')
                break;
        }
    }

    close(sock);

    return 0;
}
