import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useI18n } from '../context/i18n';
import { useFocusTrap } from '../hooks/useFocusTrap';
import { CloseIcon } from './icons';

interface CameraCaptureModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCapture: (dataUrl: string) => void;
}

const CameraCaptureModal: React.FC<CameraCaptureModalProps> = ({ isOpen, onClose, onCapture }) => {
    const { t } = useI18n();
    const modalRef = useFocusTrap<HTMLDivElement>();
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);

    const [error, setError] = useState('');
    const [capturedImage, setCapturedImage] = useState<string | null>(null);

    const cleanupCamera = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
    }, []);

    useEffect(() => {
        if (!isOpen) {
            cleanupCamera();
            setCapturedImage(null);
            setError('');
            return;
        }

        const startCamera = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    streamRef.current = stream;
                }
            } catch (err) {
                console.error("Camera error:", err);
                setError(t('modelingTool.cameraModal.error'));
            }
        };

        startCamera();

        return cleanupCamera;
    }, [isOpen, cleanupCamera, t]);
    
     useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);

    const handleCapture = () => {
        if (videoRef.current && canvasRef.current) {
            const context = canvasRef.current.getContext('2d');
            if (context) {
                canvasRef.current.width = videoRef.current.videoWidth;
                canvasRef.current.height = videoRef.current.videoHeight;
                context.drawImage(videoRef.current, 0, 0, videoRef.current.videoWidth, videoRef.current.videoHeight);
                const dataUrl = canvasRef.current.toDataURL('image/jpeg');
                setCapturedImage(dataUrl);
                cleanupCamera();
            }
        }
    };

    const handleRetake = () => {
        setCapturedImage(null);
    };

    const handleUsePhoto = () => {
        if (capturedImage) {
            onCapture(capturedImage);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/70 z-[101] flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
            <div
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="camera-capture-title"
                className="bg-gray-800 rounded-lg border-2 border-gray-700 shadow-lg w-full max-w-lg p-4 flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex justify-between items-center mb-4 flex-shrink-0">
                    <h2 id="camera-capture-title" className="text-xl font-bold text-indigo-400">{t('modelingTool.cameraModal.title')}</h2>
                    <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-700" aria-label={t('game.ariaLabels.closeModal')}>
                        <CloseIcon className="w-6 h-6" />
                    </button>
                </div>
                
                <div className="relative aspect-video w-full bg-black rounded-md overflow-hidden flex items-center justify-center">
                    {error ? (
                        <p className="text-red-400 p-4">{error}</p>
                    ) : (
                        <>
                            <video ref={videoRef} autoPlay playsInline className={`w-full h-full object-cover ${capturedImage ? 'hidden' : 'block'}`} />
                            <canvas ref={canvasRef} className="hidden" />
                            {capturedImage && <img src={capturedImage} alt="Captured" className="w-full h-full object-contain" />}
                        </>
                    )}
                </div>
                
                <div className="mt-4 flex gap-2 justify-center">
                    {capturedImage ? (
                        <>
                            <button onClick={handleRetake} className="flex-1 bg-gray-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors">
                                {t('modelingTool.cameraModal.retakeButton')}
                            </button>
                            <button onClick={handleUsePhoto} className="flex-1 bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors">
                                {t('modelingTool.cameraModal.useButton')}
                            </button>
                        </>
                    ) : (
                        <button onClick={handleCapture} disabled={!!error} className="bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-500">
                            {t('modelingTool.cameraModal.captureButton')}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CameraCaptureModal;