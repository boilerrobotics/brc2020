# Live Video

Use [image_transport](https://wiki.ros.org/image_transport) package for this package.
[Tutorial](https://wiki.ros.org/image_transport/Tutorials) is available.

One issue is `image_transport` might only support `Theora` codec which is out of date. It might not as effective as modern codec as H.264 with hardware acceleration. The codec details can be found [here](https://github.com/ros-perception/image_transport_plugins).

There are other options but also limitations

1. [ffmpeg-image-transport](https://github.com/ros-misc-utilities/ffmpeg_image_transport) requires Ubuntu 20.04 and ROS Galactic or newer.
2. [Isaac ROS Compression](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_compression) opens possibility for hardware encoder. But it requires Ubuntu 20.04 and ROS Galactic or newer.
3. [FogROS2](https://berkeleyautomation.github.io/FogROS2/video_compression).
4. Stream a video directly (without using ROS). [Potential solution](https://developer.ridgerun.com/wiki/index.php/GStreamer_pipelines_for_Jetson_TX2#H264_encoding%5B/url%5D).
