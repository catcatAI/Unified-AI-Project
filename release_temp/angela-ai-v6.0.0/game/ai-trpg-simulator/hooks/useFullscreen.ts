import { useState, useLayoutEffect, useCallback, RefObject } from 'react';

interface DocumentWithFullscreen extends Document {
  mozFullScreenElement?: Element;
  msFullscreenElement?: Element;
  webkitFullscreenElement?: Element;
  mozCancelFullScreen?: () => Promise<void>;
  msExitFullscreen?: () => Promise<void>;
  webkitExitFullscreen?: () => Promise<void>;
}

interface HTMLElementWithFullscreen extends HTMLElement {
  mozRequestFullScreen?: () => Promise<void>;
  msRequestFullscreen?: () => Promise<void>;
  webkitRequestFullscreen?: () => Promise<void>;
}

export const useFullscreen = (elementRef: RefObject<HTMLElement>) => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = useCallback(() => {
    if (!elementRef.current) return;

    const doc = document as DocumentWithFullscreen;
    const element = elementRef.current as HTMLElementWithFullscreen;

    const isCurrentlyFullscreen = 
      doc.fullscreenElement ||
      doc.mozFullScreenElement ||
      doc.webkitFullscreenElement ||
      doc.msFullscreenElement;

    if (!isCurrentlyFullscreen) {
      const promise = (element.requestFullscreen ? element.requestFullscreen()
        : element.mozRequestFullScreen ? element.mozRequestFullScreen()
        : element.webkitRequestFullscreen ? element.webkitRequestFullscreen()
        : element.msRequestFullscreen ? element.msRequestFullscreen()
        : Promise.reject(new Error("Fullscreen API is not supported.")))
        
        promise.catch(err => {
            console.warn(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });

    } else {
      const promise = (doc.exitFullscreen ? doc.exitFullscreen()
        : doc.mozCancelFullScreen ? doc.mozCancelFullScreen()
        : doc.webkitExitFullscreen ? doc.webkitExitFullscreen()
        : doc.msExitFullscreen ? doc.msExitFullscreen()
        : Promise.reject(new Error("Fullscreen API is not supported.")))

        promise.catch(err => {
            console.warn(`Error attempting to exit full-screen mode: ${err.message} (${err.name})`);
        });
    }
  }, [elementRef]);
  
  useLayoutEffect(() => {
    const onFullscreenChange = () => {
        const doc = document as DocumentWithFullscreen;
        const isCurrentlyFullscreen = !!(
            doc.fullscreenElement ||
            doc.mozFullScreenElement ||
            doc.webkitFullscreenElement ||
            doc.msFullscreenElement
        );
        setIsFullscreen(isCurrentlyFullscreen);
    };

    document.addEventListener('fullscreenchange', onFullscreenChange);
    document.addEventListener('mozfullscreenchange', onFullscreenChange);
    document.addEventListener('webkitfullscreenchange', onFullscreenChange);
    document.addEventListener('MSFullscreenChange', onFullscreenChange);

    return () => {
        document.removeEventListener('fullscreenchange', onFullscreenChange);
        document.removeEventListener('mozfullscreenchange', onFullscreenChange);
        document.removeEventListener('webkitfullscreenchange', onFullscreenChange);
        document.removeEventListener('MSFullscreenChange', onFullscreenChange);
    };
  }, []);

  return { isFullscreen, toggleFullscreen };
};