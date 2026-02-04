{
  "targets": [
    {
      "target_name": "pulseaudio-capture",
      "c++!": {
        "std": "c++17"
      },
      "sources": [
        "src/pulseaudio-capture.cpp"
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
        "-lpulse",
        "-lpulse-simple"
      ]
    }
  ]
}
