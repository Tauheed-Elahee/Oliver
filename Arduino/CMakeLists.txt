set(CMAKE_TOOLCHAIN_FILE cmake/ArduinoToolchain.cmake)

# set(${FIRMWARE_NAME}_PORT /dev/ttyACM0)

cmake_minimum_required(VERSION 2.8)

project(Arduino_code C CXX)

# print_board_list()
# print_programmer_list()

# add_subdirectory(src)


set(ARDUINO_SDK_PATH Arduino_SDK/arduino)
set(ARDUINO_DEFAULT_BOARD uno)
set(ARDUINO_DEFAULT_PORT /dev/ttyACM0)

link_directories(${ARDUINO_SDK_PATH}/libraries)

generate_arduino_firmware(arduino_code
    SRCS main.cpp
    PORT /dev/ttyACM0
    BOARD uno
)
