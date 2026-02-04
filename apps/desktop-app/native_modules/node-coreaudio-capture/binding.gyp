{
  "targets": [
    {
      "target_name": "coreaudio-capture",
      "c++!": {
        "std": "c++17"
      },
      "sources": [
        "src/coreaudio-capture.cpp"
      ],
      "include_dirs": [
        "<!@(node -p \"require('node-addon-api').include\")"
      ],
      "defines": [
        "NAPI_DISABLE_CPP_EXCEPTIONS"
      ],
      "dependencies": [
        "<!(node -p \"require('node-addon-api').gyp\")"
      ],
      "libraries": [
        "-framework CoreAudio",
        "-framework AudioToolbox",
        "-framework AudioUnit",
        "-framework CoreServices"
      ],
      "xcode_settings": {
        "MACOSX_DEPLOYMENT_TARGET": "10.13",
        "OTHER_CFLAGS": [
          "-x objective-c++"
        ]
      }
    }
  ]
}
