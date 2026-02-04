#include <napi.h>
#include <CoreAudio/CoreAudio.h>
#include <AudioToolbox/AudioToolbox.h>
#include <AudioUnit/AudioUnit.h>
#include <iostream>
#include <vector>
#include <mutex>
#include <atomic>
#include <memory>

class CoreAudioCapture : public Napi::ObjectWrap<CoreAudioCapture> {
private:
    AudioUnit audioUnit;
    AudioDeviceID deviceID;
    AudioStreamBasicDescription format;
    bool isCapturing;
    std::atomic<bool> shouldStop;
    std::mutex captureMutex;
    Napi::ThreadSafeFunction tsfn;
    
    void Cleanup() {
        shouldStop = true;
        
        if (tsfn) {
            tsfn.Release();
        }
        
        if (audioUnit) {
            AudioOutputUnitStop(audioUnit);
            AudioUnitUninitialize(audioUnit);
            AudioComponentInstanceDispose(audioUnit);
            audioUnit = nullptr;
        }
    }

    static OSStatus AudioInputCallback(
        void* inRefCon,
        AudioUnitRenderActionFlags* ioActionFlags,
        const AudioTimeStamp* inTimeStamp,
        UInt32 inBusNumber,
        UInt32 inNumberFrames,
        AudioBufferList* ioData
    ) {
        CoreAudioCapture* capture = static_cast<CoreAudioCapture*>(inRefCon);
        
        if (capture->shouldStop) {
            return noErr;
        }
        
        AudioBufferList bufferList;
        bufferList.mNumberBuffers = 1;
        bufferList.mBuffers[0].mNumberChannels = capture->format.mChannelsPerFrame;
        bufferList.mBuffers[0].mDataByteSize = inNumberFrames * capture->format.mBytesPerFrame;
        
        std::vector<float> samples(inNumberFrames * capture->format.mChannelsPerFrame);
        bufferList.mBuffers[0].mData = samples.data();
        
        OSStatus status = AudioUnitRender(
            capture->audioUnit,
            ioActionFlags,
            inTimeStamp,
            inBusNumber,
            inNumberFrames,
            &bufferList
        );
        
        if (status != noErr) {
            return status;
        }
        
        if (capture->tsfn) {
            auto callback = [samples](Napi::Env env, Napi::Function jsCallback) {
                Napi::Array arr = Napi::Array::New(env, samples.size());
                for (size_t i = 0; i < samples.size(); i++) {
                    arr.Set(i, samples[i]);
                }
                jsCallback.Call({arr});
            };
            
            capture->tsfn.NonBlockingCall(callback);
        }
        
        return noErr;
    }

public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports) {
        Napi::Function func = DefineClass(env, "CoreAudioCapture", {
            InstanceMethod("start", &CoreAudioCapture::Start),
            InstanceMethod("stop", &CoreAudioCapture::Stop),
            InstanceMethod("getFormat", &CoreAudioCapture::GetFormat),
            InstanceMethod("getDevices", &CoreAudioCapture::GetDevices).Static(),
            StaticMethod<&CoreAudioCapture::getDefaultDevice>("getDefaultDevice")
        });

        Napi::FunctionReference* constructor = new Napi::FunctionReference();
        *constructor = Napi::Persistent(func);
        env.SetInstanceData<Napi::FunctionReference>(constructor);

        exports.Set("CoreAudioCapture", func);
        return exports;
    }

    CoreAudioCapture(const Napi::CallbackInfo& info) : Napi::ObjectWrap<CoreAudioCapture>(info) {
        audioUnit = nullptr;
        deviceID = kAudioObjectUnknown;
        isCapturing = false;
        shouldStop = false;
        
        format.mSampleRate = 48000.0;
        format.mFormatID = kAudioFormatLinearPCM;
        format.mFormatFlags = kAudioFormatFlagIsFloat | kAudioFormatFlagIsPacked;
        format.mBytesPerPacket = 4;
        format.mFramesPerPacket = 1;
        format.mBytesPerFrame = 4;
        format.mChannelsPerFrame = 2;
        format.mBitsPerChannel = 32;
    }

    ~CoreAudioCapture() {
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
        
        OSStatus status;
        
        AudioComponentDescription desc;
        desc.componentType = kAudioUnitType_Output;
        desc.componentSubType = kAudioUnitSubType_HALOutput;
        desc.componentManufacturer = kAudioUnitManufacturer_Apple;
        desc.componentFlags = 0;
        desc.componentFlagsMask = 0;
        
        AudioComponent comp = AudioComponentFindNext(nullptr, &desc);
        if (!comp) {
            Napi::Error::New(env, "Failed to find audio component").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        status = AudioComponentInstanceNew(comp, &audioUnit);
        if (status != noErr) {
            Napi::Error::New(env, "Failed to create audio unit").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        if (!deviceId.empty()) {
            deviceID = std::stoull(deviceId);
        } else {
            UInt32 size = sizeof(deviceID);
            AudioObjectPropertyAddress propertyAddress = {
                kAudioHardwarePropertyDefaultOutputDevice,
                kAudioObjectPropertyScopeOutput,
                kAudioObjectPropertyElementMain
            };
            status = AudioObjectGetPropertyData(
                kAudioObjectSystemObject,
                &propertyAddress,
                0,
                nullptr,
                &size,
                &deviceID
            );
            if (status != noErr) {
                Napi::Error::New(env, "Failed to get default device").ThrowAsJavaScriptException();
                return env.Null();
            }
        }
        
        status = AudioUnitSetProperty(
            audioUnit,
            kAudioOutputUnitProperty_CurrentDevice,
            kAudioUnitScope_Global,
            0,
            &deviceID,
            sizeof(deviceID)
        );
        if (status != noErr) {
            Napi::Error::New(env, "Failed to set audio device").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        UInt32 enableInput = 1;
        status = AudioUnitSetProperty(
            audioUnit,
            kAudioOutputUnitProperty_EnableIO,
            kAudioUnitScope_Input,
            1,
            &enableInput,
            sizeof(enableInput)
        );
        if (status != noErr) {
            Napi::Error::New(env, "Failed to enable input").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        UInt32 enableOutput = 0;
        status = AudioUnitSetProperty(
            audioUnit,
            kAudioOutputUnitProperty_EnableIO,
            kAudioUnitScope_Output,
            0,
            &enableOutput,
            sizeof(enableOutput)
        );
        if (status != noErr) {
            Napi::Error::New(env, "Failed to disable output").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        status = AudioUnitSetProperty(
            audioUnit,
            kAudioUnitProperty_StreamFormat,
            kAudioUnitScope_Output,
            1,
            &format,
            sizeof(format)
        );
        if (status != noErr) {
            Napi::Error::New(env, "Failed to set stream format").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        AURenderCallbackStruct callbackStruct;
        callbackStruct.inputProc = AudioInputCallback;
        callbackStruct.inputProcRefCon = this;
        
        status = AudioUnitSetProperty(
            audioUnit,
            kAudioOutputUnitProperty_SetInputCallback,
            kAudioUnitScope_Global,
            0,
            &callbackStruct,
            sizeof(callbackStruct)
        );
        if (status != noErr) {
            Napi::Error::New(env, "Failed to set callback").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        status = AudioUnitInitialize(audioUnit);
        if (status != noErr) {
            Napi::Error::New(env, "Failed to initialize audio unit").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        status = AudioOutputUnitStart(audioUnit);
        if (status != noErr) {
            Napi::Error::New(env, "Failed to start audio unit").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        isCapturing = true;
        shouldStop = false;
        
        if (!callback.IsEmpty()) {
            tsfn = Napi::ThreadSafeFunction::New(
                env, callback, "CoreAudioCaptureCallback", 0, 1
            );
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
        
        Napi::Object formatObj = Napi::Object::New(env);
        formatObj.Set("sampleRate", format.mSampleRate);
        formatObj.Set("channels", format.mChannelsPerFrame);
        formatObj.Set("bitsPerSample", format.mBitsPerChannel);
        formatObj.Set("formatID", format.mFormatID);
        formatObj.Set("formatFlags", format.mFormatFlags);
        formatObj.Set("sampleFormat", "float32");
        
        return formatObj;
    }

    static Napi::Value GetDevices(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        Napi::Array devices = Napi::Array::New(env);
        
        AudioObjectPropertyAddress propertyAddress = {
            kAudioHardwarePropertyDevices,
            kAudioObjectPropertyScopeOutput,
            kAudioObjectPropertyElementMain
        };
        
        UInt32 dataSize = 0;
        OSStatus status = AudioObjectGetPropertyDataSize(
            kAudioObjectSystemObject,
            &propertyAddress,
            0,
            nullptr,
            &dataSize
        );
        
        if (status != noErr) {
            return devices;
        }
        
        UInt32 deviceCount = dataSize / sizeof(AudioDeviceID);
        std::vector<AudioDeviceID> deviceIDs(deviceCount);
        
        status = AudioObjectGetPropertyData(
            kAudioObjectSystemObject,
            &propertyAddress,
            0,
            nullptr,
            &dataSize,
            deviceIDs.data()
        );
        
        if (status != noErr) {
            return devices;
        }
        
        uint32_t index = 0;
        for (AudioDeviceID deviceID : deviceIDs) {
            CFStringRef deviceName = nullptr;
            dataSize = sizeof(deviceName);
            
            AudioObjectPropertyAddress nameAddress = {
                kAudioDevicePropertyDeviceNameCFString,
                kAudioObjectPropertyScopeOutput,
                kAudioObjectPropertyElementMain
            };
            
            status = AudioObjectGetPropertyData(
                deviceID,
                &nameAddress,
                0,
                nullptr,
                &dataSize,
                &deviceName
            );
            
            if (status == noErr && deviceName) {
                Napi::Object device = Napi::Object::New(env);
                device.Set("id", std::to_string(deviceID));
                
                char buffer[256];
                CFStringGetCString(deviceName, buffer, sizeof(buffer), kCFStringEncodingUTF8);
                device.Set("name", buffer);
                
                devices.Set(index++, device);
                
                CFRelease(deviceName);
            }
        }
        
        return devices;
    }

    static Napi::Value GetDefaultDevice(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        AudioDeviceID deviceID;
        UInt32 size = sizeof(deviceID);
        
        AudioObjectPropertyAddress propertyAddress = {
            kAudioHardwarePropertyDefaultOutputDevice,
            kAudioObjectPropertyScopeOutput,
            kAudioObjectPropertyElementMain
        };
        
        OSStatus status = AudioObjectGetPropertyData(
            kAudioObjectSystemObject,
            &propertyAddress,
            0,
            nullptr,
            &size,
            &deviceID
        );
        
        if (status != noErr) {
            return env.Null();
        }
        
        CFStringRef deviceName = nullptr;
        size = sizeof(deviceName);
        
        AudioObjectPropertyAddress nameAddress = {
            kAudioDevicePropertyDeviceNameCFString,
            kAudioObjectPropertyScopeOutput,
            kAudioObjectPropertyElementMain
        };
        
        status = AudioObjectGetPropertyData(
            deviceID,
            &nameAddress,
            0,
            nullptr,
            &size,
            &deviceName
        );
        
        if (status != noErr || !deviceName) {
            return env.Null();
        }
        
        Napi::Object device = Napi::Object::New(env);
        device.Set("id", std::to_string(deviceID));
        
        char buffer[256];
        CFStringGetCString(deviceName, buffer, sizeof(buffer), kCFStringEncodingUTF8);
        device.Set("name", buffer);
        
        CFRelease(deviceName);
        
        return device;
    }
};

Napi::Object Init(Napi::Env env, Napi::Object exports) {
    return CoreAudioCapture::Init(env, exports);
}

NODE_API_MODULE(coreaudio-capture, Init)
