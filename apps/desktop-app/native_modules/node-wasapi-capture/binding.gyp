{
  "targets": [
    {
      "target_name": "wasapi-capture",
      "c++!": {
        "std": "c++17"
      },
      "sources": [
        "src/wasapi-capture.cpp"
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
        "ole32",
        "ksuser",
        "mmdevapi"
      ]
    }
  ]
}
