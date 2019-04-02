cmake_minimum_required (VERSION 2.6)
project (video_play)
set (CMAKE_CXX_STANDARD 11)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package( OpenCV REQUIRED )
find_package( Threads REQUIRED )

add_executable( video_play video_play.cpp )
target_link_libraries( video_play ${OpenCV_LIBS} )

add_executable( server server.cpp )
target_link_libraries( server ${OpenCV_LIBS} )
target_link_libraries( server Threads::Threads )

add_executable( client client.cpp )
target_link_libraries( client ${OpenCV_LIBS} )
