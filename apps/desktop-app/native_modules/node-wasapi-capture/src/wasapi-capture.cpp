#include <napi.h>
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <iostream>
#include <vector>
#include <mutex>
#include <atomic>
#include <memory>

#pragma comment(lib, "ole32")
#pragma comment(lib, "mmdevapi")

const CLSID CLSID_MMDeviceEnumerator = __uuidof(MMDeviceEnumerator);
const IID IID_IMMDeviceEnumerator = __uuidof(IMMDeviceEnumerator);
const IID IID_IAudioClient = __uuidof(IAudioClient);
const IID IID_IAudioCaptureClient = __uuidof(IAudioCaptureClient);

class WASAPICapture : public Napi::ObjectWrap<WASAPICapture> {
private:
    IMMDeviceEnumerator* pEnumerator;
    IMMDevice* pDevice;
    IAudioClient* pAudioClient;
    IAudioCaptureClient* pCaptureClient;
    WAVEFORMATEX* pwfx;
    HANDLE hEvent;
    bool isCapturing;
    std::atomic<bool> shouldStop;
    std::mutex captureMutex;
    Napi::ThreadSafeFunction tsfn;
    std::thread captureThread;

    void Cleanup() {
        shouldStop = true;
        
        if (hEvent != NULL) {
            SetEvent(hEvent);
        }
        
        if (captureThread.joinable()) {
            captureThread.join();
        }
        
        if (tsfn) {
            tsfn.Release();
        }
        
        if (hEvent != NULL) {
            CloseHandle(hEvent);
            hEvent = NULL;
        }
        
        if (pCaptureClient) {
            pCaptureClient->Release();
            pCaptureClient = NULL;
        }
        
        if (pAudioClient) {
            pAudioClient->Release();
            pAudioClient = NULL;
        }
        
        if (pDevice) {
            pDevice->Release();
            pDevice = NULL;
        }
        
        if (pEnumerator) {
            pEnumerator->Release();
            pEnumerator = NULL;
        }
        
        if (pwfx) {
            CoTaskMemFree(pwfx);
            pwfx = NULL;
        }
    }

    static void CaptureThreadStatic(Napi::Env env, Napi::Function jsCallback, WASAPICapture* capture) {
        capture->CaptureThread();
    }

    void CaptureThread() {
        UINT32 packetLength = 0;
        UINT32 numFramesAvailable;
        BYTE* pData;
        DWORD flags;
        
        while (!shouldStop) {
            DWORD waitResult = WaitForSingleObject(hEvent, 2000);
            
            if (waitResult != WAIT_OBJECT_0) {
                if (shouldStop) break;
                continue;
            }
            
            std::lock_guard<std::mutex> lock(captureMutex);
            
            while (true) {
                HRESULT hr = pCaptureClient->GetNextPacketSize(&packetLength);
                if (FAILED(hr) || packetLength == 0) break;
                
                hr = pCaptureClient->GetBuffer(&pData, &numFramesAvailable, &flags, NULL, NULL);
                if (FAILED(hr)) break;
                
                if (flags & AUDCLNT_BUFFERFLAGS_SILENT) {
                    pData = NULL;
                }
                
                if (pData != NULL) {
                    std::vector<float> samples;
                    samples.reserve(numFramesAvailable * pwfx->nChannels);
                    
                    float* floatData = reinterpret_cast<float*>(pData);
                    for (UINT32 i = 0; i < numFramesAvailable * pwfx->nChannels; i++) {
                        samples.push_back(floatData[i]);
                    }
                    
                    auto callback = [samples](Napi::Env env, Napi::Function jsCallback) {
                        Napi::Array arr = Napi::Array::New(env, samples.size());
                        for (size_t i = 0; i < samples.size(); i++) {
                            arr.Set(i, samples[i]);
                        }
                        jsCallback.Call({arr});
                    };
                    
                    tsfn.NonBlockingCall(callback);
                }
                
                pCaptureClient->ReleaseBuffer(numFramesAvailable);
            }
        }
    }

public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports) {
        Napi::Function func = DefineClass(env, "WASAPICapture", {
            InstanceMethod("start", &WASAPICapture::Start),
            InstanceMethod("stop", &WASAPICapture::Stop),
            InstanceMethod("getFormat", &WASAPICapture::GetFormat),
            InstanceMethod("getDevices", &WASAPICapture::GetDevices).Static(),
            StaticMethod<&WASAPICapture::getDefaultDevice>("getDefaultDevice")
        });

        Napi::FunctionReference* constructor = new Napi::FunctionReference();
        *constructor = Napi::Persistent(func);
        env.SetInstanceData<Napi::FunctionReference>(constructor);

        exports.Set("WASAPICapture", func);
        return exports;
    }

    WASAPICapture(const Napi::CallbackInfo& info) : Napi::ObjectWrap<WASAPICapture>(info) {
        pEnumerator = NULL;
        pDevice = NULL;
        pAudioClient = NULL;
        pCaptureClient = NULL;
        pwfx = NULL;
        hEvent = NULL;
        isCapturing = false;
        shouldStop = false;
    }

    ~WASAPICapture() {
        Cleanup();
    }

    Napi::Value Start(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        if (isCapturing) {
            Napi::Error::New(env, "Already capturing").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        std::string deviceId;
        Napi::Function callback;
        
        if (info.Length() >= 1 && info[0].IsString()) {
            deviceId = info[0].As<Napi::String>().Utf8Value();
        }
        
        if (info.Length() >= 2 && info[1].IsFunction()) {
            callback = info[1].As<Napi::Function>();
        }
        
        HRESULT hr;
        
        hr = CoInitialize(NULL);
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to initialize COM").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        hr = CoCreateInstance(
            CLSID_MMDeviceEnumerator, NULL,
            CLSCTX_ALL, IID_IMMDeviceEnumerator,
            (void**)&pEnumerator
        );
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to create device enumerator").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        if (deviceId.empty()) {
            hr = pEnumerator->GetDefaultAudioEndpoint(eRender, eConsole, &pDevice);
        } else {
            hr = pEnumerator->GetDevice(std::wstring(deviceId.begin(), deviceId.end()).c_str(), &pDevice);
        }
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to get audio device").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        hr = pDevice->Activate(IID_IAudioClient, CLSCTX_ALL, NULL, (void**)&pAudioClient);
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to activate audio client").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        hr = pAudioClient->GetMixFormat(&pwfx);
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to get mix format").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        hEvent = CreateEvent(NULL, FALSE, FALSE, NULL);
        if (hEvent == NULL) {
            Napi::Error::New(env, "Failed to create event").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        REFERENCE_TIME hnsRequestedDuration = 10000000;
        
        hr = pAudioClient->Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_EVENTCALLBACK | AUDCLNT_STREAMFLAGS_LOOPBACK,
            hnsRequestedDuration, 0, pwfx, NULL
        );
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to initialize audio client").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        hr = pAudioClient->SetEventHandle(hEvent);
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to set event handle").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        hr = pAudioClient->GetService(IID_IAudioCaptureClient, (void**)&pCaptureClient);
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to get capture client").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        UINT32 bufferFrameCount;
        hr = pAudioClient->GetBufferSize(&bufferFrameCount);
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to get buffer size").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        hr = pAudioClient->Start();
        if (FAILED(hr)) {
            Napi::Error::New(env, "Failed to start audio client").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        isCapturing = true;
        shouldStop = false;
        
        if (!callback.IsEmpty()) {
            tsfn = Napi::ThreadSafeFunction::New(
                env, callback, "WASAPICaptureCallback", 0, 1
            );
            
            captureThread = std::thread(&WASAPICapture::CaptureThreadStatic, env, callback, this);
        }
        
        return Napi::Boolean::New(env, true);
    }

    Napi::Value Stop(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        if (!isCapturing) {
            return Napi::Boolean::New(env, true);
        }
        
        Cleanup();
        isCapturing = false;
        
        return Napi::Boolean::New(env, true);
    }

    Napi::Value GetFormat(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        if (pwfx == NULL) {
            return env.Null();
        }
        
        Napi::Object format = Napi::Object::New(env);
        format.Set("sampleRate", pwfx->nSamplesPerSec);
        format.Set("channels", pwfx->nChannels);
        format.Set("bitsPerSample", pwfx->wBitsPerSample);
        format.Set("formatTag", pwfx->wFormatTag);
        
        if (pwfx->wFormatTag == WAVE_FORMAT_IEEE_FLOAT) {
            format.Set("sampleFormat", "float32");
        } else if (pwfx->wFormatTag == WAVE_FORMAT_PCM) {
            format.Set("sampleFormat", "int16");
        }
        
        return format;
    }

    static Napi::Value GetDevices(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        Napi::Array devices = Napi::Array::New(env);
        
        HRESULT hr;
        IMMDeviceEnumerator* pEnumerator = NULL;
        IMMDeviceCollection* pCollection = NULL;
        
        hr = CoInitialize(NULL);
        if (FAILED(hr)) {
            return devices;
        }
        
        hr = CoCreateInstance(
            CLSID_MMDeviceEnumerator, NULL,
            CLSCTX_ALL, IID_IMMDeviceEnumerator,
            (void**)&pEnumerator
        );
        if (FAILED(hr)) {
            return devices;
        }
        
        hr = pEnumerator->EnumAudioEndpoints(eRender, DEVICE_STATE_ACTIVE, &pCollection);
        if (FAILED(hr)) {
            pEnumerator->Release();
            return devices;
        }
        
        UINT count;
        hr = pCollection->GetCount(&count);
        if (FAILED(hr)) {
            pCollection->Release();
            pEnumerator->Release();
            return devices;
        }
        
        for (UINT i = 0; i < count; i++) {
            IMMDevice* pDevice = NULL;
            IPropertyStore* pProps = NULL;
            
            hr = pCollection->Item(i, &pDevice);
            if (FAILED(hr)) continue;
            
            hr = pDevice->OpenPropertyStore(STGM_READ, &pProps);
            if (FAILED(hr)) {
                pDevice->Release();
                continue;
            }
            
            PROPVARIANT varName;
            PropVariantInit(&varName);
            
            hr = pProps->GetValue(PKEY_Device_FriendlyName, &varName);
            if (SUCCEEDED(hr)) {
                Napi::Object device = Napi::Object::New(env);
                
                LPWSTR deviceId = NULL;
                pDevice->GetId(&deviceId);
                
                int bufferSize = WideCharToMultiByte(CP_UTF8, 0, deviceId, -1, NULL, 0, NULL, NULL);
                std::string deviceIdStr(bufferSize - 1, 0);
                WideCharToMultiByte(CP_UTF8, 0, deviceId, -1, &deviceIdStr[0], bufferSize, NULL, NULL);
                
                device.Set("id", deviceIdStr);
                device.Set("name", std::wstring(varName.pwszVal).c_str());
                
                devices.Set(devices.Length(), device);
                
                CoTaskMemFree(deviceId);
            }
            
            PropVariantClear(&varName);
            pProps->Release();
            pDevice->Release();
        }
        
        pCollection->Release();
        pEnumerator->Release();
        
        return devices;
    }

    static Napi::Value GetDefaultDevice(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        HRESULT hr;
        IMMDeviceEnumerator* pEnumerator = NULL;
        IMMDevice* pDevice = NULL;
        IPropertyStore* pProps = NULL;
        
        hr = CoInitialize(NULL);
        if (FAILED(hr)) {
            return env.Null();
        }
        
        hr = CoCreateInstance(
            CLSID_MMDeviceEnumerator, NULL,
            CLSCTX_ALL, IID_IMMDeviceEnumerator,
            (void**)&pEnumerator
        );
        if (FAILED(hr)) {
            return env.Null();
        }
        
        hr = pEnumerator->GetDefaultAudioEndpoint(eRender, eConsole, &pDevice);
        if (FAILED(hr)) {
            pEnumerator->Release();
            return env.Null();
        }
        
        hr = pDevice->OpenPropertyStore(STGM_READ, &pProps);
        if (FAILED(hr)) {
            pDevice->Release();
            pEnumerator->Release();
            return env.Null();
        }
        
        PROPVARIANT varName;
        PropVariantInit(&varName);
        
        hr = pProps->GetValue(PKEY_Device_FriendlyName, &varName);
        
        Napi::Object device = Napi::Object::New(env);
        
        if (SUCCEEDED(hr)) {
            LPWSTR deviceId = NULL;
            pDevice->GetId(&deviceId);
            
            int bufferSize = WideCharToMultiByte(CP_UTF8, 0, deviceId, -1, NULL, 0, NULL, NULL);
            std::string deviceIdStr(bufferSize - 1, 0);
            WideCharToMultiByte(CP_UTF8, 0, deviceId, -1, &deviceIdStr[0], bufferSize, NULL, NULL);
            
            device.Set("id", deviceIdStr);
            device.Set("name", std::wstring(varName.pwszVal).c_str());
            
            CoTaskMemFree(deviceId);
        }
        
        PropVariantClear(&varName);
        pProps->Release();
        pDevice->Release();
        pEnumerator->Release();
        
        return device;
    }
};

Napi::Object Init(Napi::Env env, Napi::Object exports) {
    return WASAPICapture::Init(env, exports);
}

NODE_API_MODULE(wasapi-capture, Init)
