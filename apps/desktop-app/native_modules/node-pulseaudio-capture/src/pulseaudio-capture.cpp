#include <napi.h>
#include <pulse/pulseaudio.h>
#include <pulse/simple.h>
#include <iostream>
#include <vector>
#include <mutex>
#include <atomic>
#include <memory>

class PulseAudioCapture : public Napi::ObjectWrap<PulseAudioCapture> {
private:
    pa_threaded_mainloop* mainloop;
    pa_context* context;
    pa_stream* stream;
    pa_sample_spec sampleSpec;
    pa_channel_map channelMap;
    bool isCapturing;
    std::atomic<bool> shouldStop;
    std::mutex captureMutex;
    Napi::ThreadSafeFunction tsfn;
    std::thread captureThread;
    
    void Cleanup() {
        shouldStop = true;
        
        if (mainloop) {
            pa_threaded_mainloop_signal(mainloop, 0);
        }
        
        if (captureThread.joinable()) {
            captureThread.join();
        }
        
        if (tsfn) {
            tsfn.Release();
        }
        
        if (stream) {
            pa_stream_disconnect(stream);
            pa_stream_unref(stream);
            stream = nullptr;
        }
        
        if (context) {
            pa_context_disconnect(context);
            pa_context_unref(context);
            context = nullptr;
        }
        
        if (mainloop) {
            pa_threaded_mainloop_stop(mainloop);
            pa_threaded_mainloop_free(mainloop);
            mainloop = nullptr;
        }
    }

    static void StreamReadCallback(pa_stream* p, size_t nbytes, void* userdata) {
        PulseAudioCapture* capture = static_cast<PulseAudioCapture*>(userdata);
        
        if (capture->shouldStop) {
            return;
        }
        
        const void* data;
        size_t length;
        
        if (pa_stream_peek(p, &data, &length) < 0) {
            return;
        }
        
        if (data && length > 0) {
            std::vector<float> samples;
            size_t sampleCount = length / sizeof(float);
            samples.reserve(sampleCount);
            
            const float* floatData = static_cast<const float*>(data);
            for (size_t i = 0; i < sampleCount; i++) {
                samples.push_back(floatData[i]);
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
        }
        
        pa_stream_drop(p);
    }

    static void StreamStateCallback(pa_stream* p, void* userdata) {
        PulseAudioCapture* capture = static_cast<PulseAudioCapture*>(userdata);
        pa_stream_state_t state = pa_stream_get_state(p);
        
        switch (state) {
            case PA_STREAM_READY:
                pa_threaded_mainloop_signal(capture->mainloop, 0);
                break;
            case PA_STREAM_FAILED:
            case PA_STREAM_TERMINATED:
                pa_threaded_mainloop_signal(capture->mainloop, 0);
                break;
            default:
                break;
        }
    }

    static void ContextStateCallback(pa_context* c, void* userdata) {
        PulseAudioCapture* capture = static_cast<PulseAudioCapture*>(userdata);
        pa_context_state_t state = pa_context_get_state(c);
        
        switch (state) {
            case PA_CONTEXT_READY:
                pa_threaded_mainloop_signal(capture->mainloop, 0);
                break;
            case PA_CONTEXT_FAILED:
            case PA_CONTEXT_TERMINATED:
                pa_threaded_mainloop_signal(capture->mainloop, 0);
                break;
            default:
                break;
        }
    }

public:
    static Napi::Object Init(Napi::Env env, Napi::Object exports) {
        Napi::Function func = DefineClass(env, "PulseAudioCapture", {
            InstanceMethod("start", &PulseAudioCapture::Start),
            InstanceMethod("stop", &PulseAudioCapture::Stop),
            InstanceMethod("getFormat", &PulseAudioCapture::GetFormat),
            InstanceMethod("getDevices", &PulseAudioCapture::GetDevices).Static(),
            StaticMethod<&PulseAudioCapture::getDefaultDevice>("getDefaultDevice")
        });

        Napi::FunctionReference* constructor = new Napi::FunctionReference();
        *constructor = Napi::Persistent(func);
        env.SetInstanceData<Napi::FunctionReference>(constructor);

        exports.Set("PulseAudioCapture", func);
        return exports;
    }

    PulseAudioCapture(const Napi::CallbackInfo& info) : Napi::ObjectWrap<PulseAudioCapture>(info) {
        mainloop = nullptr;
        context = nullptr;
        stream = nullptr;
        isCapturing = false;
        shouldStop = false;
        
        sampleSpec.format = PA_SAMPLE_FLOAT32LE;
        sampleSpec.rate = 48000;
        sampleSpec.channels = 2;
        
        pa_channel_map_init_stereo(&channelMap);
    }

    ~PulseAudioCapture() {
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
        
        mainloop = pa_threaded_mainloop_new();
        if (!mainloop) {
            Napi::Error::New(env, "Failed to create mainloop").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        if (pa_threaded_mainloop_start(mainloop) < 0) {
            pa_threaded_mainloop_free(mainloop);
            mainloop = nullptr;
            Napi::Error::New(env, "Failed to start mainloop").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        pa_threaded_mainloop_lock(mainloop);
        
        context = pa_context_new(pa_threaded_mainloop_get_api(mainloop), "Angela AI Audio Capture");
        if (!context) {
            pa_threaded_mainloop_unlock(mainloop);
            Cleanup();
            Napi::Error::New(env, "Failed to create context").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        pa_context_set_state_callback(context, ContextStateCallback, this);
        
        if (pa_context_connect(context, NULL, PA_CONTEXT_NOAUTOSPAWN, NULL) < 0) {
            pa_threaded_mainloop_unlock(mainloop);
            Cleanup();
            Napi::Error::New(env, "Failed to connect context").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        while (true) {
            pa_context_state_t state = pa_context_get_state(context);
            if (state == PA_CONTEXT_READY) {
                break;
            }
            if (!PA_CONTEXT_IS_GOOD(state)) {
                pa_threaded_mainloop_unlock(mainloop);
                Cleanup();
                Napi::Error::New(env, "Context connection failed").ThrowAsJavaScriptException();
                return env.Null();
            }
            pa_threaded_mainloop_wait(mainloop);
        }
        
        stream = pa_stream_new(context, "Angela Audio Capture", &sampleSpec, &channelMap);
        if (!stream) {
            pa_threaded_mainloop_unlock(mainloop);
            Cleanup();
            Napi::Error::New(env, "Failed to create stream").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        pa_stream_set_state_callback(stream, StreamStateCallback, this);
        pa_stream_set_read_callback(stream, StreamReadCallback, this);
        
        pa_buffer_attr bufferAttr;
        bufferAttr.maxlength = (uint32_t)-1;
        bufferAttr.tlength = (uint32_t)-1;
        bufferAttr.prebuf = (uint32_t)-1;
        bufferAttr.minreq = (uint32_t)-1;
        bufferAttr.fragsize = pa_usec_to_bytes(20000, &sampleSpec);
        
        const char* monitorName = deviceId.empty() ? NULL : deviceId.c_str();
        
        if (pa_stream_connect_record(stream, monitorName, &bufferAttr, PA_STREAM_ADJUST_LATENCY) < 0) {
            pa_threaded_mainloop_unlock(mainloop);
            Cleanup();
            Napi::Error::New(env, "Failed to connect stream").ThrowAsJavaScriptException();
            return env.Null();
        }
        
        while (true) {
            pa_stream_state_t state = pa_stream_get_state(stream);
            if (state == PA_STREAM_READY) {
                break;
            }
            if (!PA_STREAM_IS_GOOD(state)) {
                pa_threaded_mainloop_unlock(mainloop);
                Cleanup();
                Napi::Error::New(env, "Stream connection failed").ThrowAsJavaScriptException();
                return env.Null();
            }
            pa_threaded_mainloop_wait(mainloop);
        }
        
        pa_threaded_mainloop_unlock(mainloop);
        
        isCapturing = true;
        shouldStop = false;
        
        if (!callback.IsEmpty()) {
            tsfn = Napi::ThreadSafeFunction::New(
                env, callback, "PulseAudioCaptureCallback", 0, 1
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
        formatObj.Set("sampleRate", sampleSpec.rate);
        formatObj.Set("channels", sampleSpec.channels);
        formatObj.Set("format", static_cast<int>(sampleSpec.format));
        formatObj.Set("sampleFormat", "float32");
        
        return formatObj;
    }

    static Napi::Value GetDevices(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        Napi::Array devices = Napi::Array::New(env);
        
        pa_threaded_mainloop* mainloop = pa_threaded_mainloop_new();
        if (!mainloop) {
            return devices;
        }
        
        if (pa_threaded_mainloop_start(mainloop) < 0) {
            pa_threaded_mainloop_free(mainloop);
            return devices;
        }
        
        pa_threaded_mainloop_lock(mainloop);
        
        pa_context* context = pa_context_new(pa_threaded_mainloop_get_api(mainloop), "Angela Device List");
        if (!context) {
            pa_threaded_mainloop_unlock(mainloop);
            pa_threaded_mainloop_free(mainloop);
            return devices;
        }
        
        if (pa_context_connect(context, NULL, PA_CONTEXT_NOAUTOSPAWN, NULL) < 0) {
            pa_context_unref(context);
            pa_threaded_mainloop_unlock(mainloop);
            pa_threaded_mainloop_free(mainloop);
            return devices;
        }
        
        while (true) {
            pa_context_state_t state = pa_context_get_state(context);
            if (state == PA_CONTEXT_READY) break;
            if (!PA_CONTEXT_IS_GOOD(state)) {
                pa_context_disconnect(context);
                pa_context_unref(context);
                pa_threaded_mainloop_unlock(mainloop);
                pa_threaded_mainloop_free(mainloop);
                return devices;
            }
            pa_threaded_mainloop_wait(mainloop);
        }
        
        pa_operation* op = pa_context_get_sink_info_list(context, 
            [](pa_context* c, const pa_sink_info* i, int eol, void* userdata) {
                if (eol > 0) {
                    pa_threaded_mainloop_signal(static_cast<pa_threaded_mainloop*>(userdata), 0);
                    return;
                }
                
                if (i && i->monitor_source_name) {
                    Napi::Array* devices = static_cast<Napi::Array*>(pa_threaded_mainloop_get_api(
                        static_cast<pa_threaded_mainloop*>(userdata))->userdata);
                    
                    Napi::Env env = devices->Env();
                    Napi::Object device = Napi::Object::New(env);
                    
                    device.Set("id", i->monitor_source_name);
                    device.Set("name", i->name ? i->name : "Unknown");
                    device.Set("description", i->description ? i->description : "Unknown");
                    
                    devices->Set(devices->Length(), device);
                }
            }, 
            mainloop
        );
        
        if (op) {
            pa_operation_unref(op);
        }
        
        pa_threaded_mainloop_wait(mainloop);
        
        pa_context_disconnect(context);
        pa_context_unref(context);
        
        pa_threaded_mainloop_unlock(mainloop);
        pa_threaded_mainloop_free(mainloop);
        
        return devices;
    }

    static Napi::Value GetDefaultDevice(const Napi::CallbackInfo& info) {
        Napi::Env env = info.Env();
        
        pa_threaded_mainloop* mainloop = pa_threaded_mainloop_new();
        if (!mainloop) {
            return env.Null();
        }
        
        if (pa_threaded_mainloop_start(mainloop) < 0) {
            pa_threaded_mainloop_free(mainloop);
            return env.Null();
        }
        
        pa_threaded_mainloop_lock(mainloop);
        
        pa_context* context = pa_context_new(pa_threaded_mainloop_get_api(mainloop), "Angela Default Device");
        if (!context) {
            pa_threaded_mainloop_unlock(mainloop);
            pa_threaded_mainloop_free(mainloop);
            return env.Null();
        }
        
        if (pa_context_connect(context, NULL, PA_CONTEXT_NOAUTOSPAWN, NULL) < 0) {
            pa_context_unref(context);
            pa_threaded_mainloop_unlock(mainloop);
            pa_threaded_mainloop_free(mainloop);
            return env.Null();
        }
        
        while (true) {
            pa_context_state_t state = pa_context_get_state(context);
            if (state == PA_CONTEXT_READY) break;
            if (!PA_CONTEXT_IS_GOOD(state)) {
                pa_context_disconnect(context);
                pa_context_unref(context);
                pa_threaded_mainloop_unlock(mainloop);
                pa_threaded_mainloop_free(mainloop);
                return env.Null();
            }
            pa_threaded_mainloop_wait(mainloop);
        }
        
        Napi::Object device = Napi::Object::New(env);
        bool found = false;
        
        pa_operation* op = pa_context_get_server_info(context,
            [](pa_context* c, const pa_server_info* i, void* userdata) {
                if (i && i->default_sink_name) {
                    struct DeviceData {
                        Napi::Object device;
                        bool* found;
                    };
                    DeviceData* data = static_cast<DeviceData*>(userdata);
                    
                    data->device.Set("id", i->default_sink_name);
                    data->device.Set("name", i->default_sink_name);
                    *data->found = true;
                }
                pa_threaded_mainloop_signal(static_cast<pa_threaded_mainloop*>(
                    static_cast<DeviceData*>(userdata)->device.Data()), 0);
            },
            &device
        );
        
        if (op) {
            pa_operation_unref(op);
        }
        
        pa_threaded_mainloop_wait(mainloop);
        
        pa_context_disconnect(context);
        pa_context_unref(context);
        
        pa_threaded_mainloop_unlock(mainloop);
        pa_threaded_mainloop_free(mainloop);
        
        return found ? device : env.Null();
    }
};

Napi::Object Init(Napi::Env env, Napi::Object exports) {
    return PulseAudioCapture::Init(env, exports);
}

NODE_API_MODULE(pulseaudio-capture, Init)
