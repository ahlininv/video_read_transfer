import cv2

# cap = cv2.VideoCapture("rtsp:/admin:12345Admin@172.18.12.127/h264/ch01/main/av_stream")
cap = cv2.VideoCapture("/home/ahlininv/Desktop/tantum.avi")

if __name__ == "__main__":
    while(cap.isOpened()):
        ret, frame = cap.read()
        if frame is None:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow('frame', gray)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
