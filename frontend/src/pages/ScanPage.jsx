import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, ScanLine, Smartphone, AlertTriangle, CheckCircle, RefreshCw, ChevronRight } from 'lucide-react';
import { GridContainer, Card, CardBody } from '../components/Primitives';
import { useNavigate } from 'react-router-dom';

export default function ScanPage() {
  const navigate = useNavigate();
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const [qualityIssue, setQualityIssue] = useState(null); // null if good, string if issue
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef(null);
  const uploadInputRef = useRef(null);

  // Clean up object URLs
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const checkImageQuality = (file) => {
    return new Promise((resolve) => {
      const img = new Image();
      const objectUrl = URL.createObjectURL(file);
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Downsample for performance (max 300px)
        const MAX_SIZE = 300;
        let width = img.width;
        let height = img.height;
        if (width > height && width > MAX_SIZE) {
          height *= MAX_SIZE / width;
          width = MAX_SIZE;
        } else if (height > width && height > MAX_SIZE) {
          width *= MAX_SIZE / height;
          height = MAX_SIZE;
        }
        
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, 0, 0, width, height);
        
        const imageData = ctx.getImageData(0, 0, width, height);
        const data = imageData.data;
        
        let totalLuminance = 0;
        const gray = new Float32Array(width * height);
        
        // Convert to grayscale and compute luminance
        for (let i = 0; i < data.length; i += 4) {
          const luma = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
          totalLuminance += luma;
          gray[i / 4] = luma;
        }
        
        const avgBrightness = totalLuminance / (width * height);
        
        // Compute Laplacian variance (blur detection)
        const laplacian = new Float32Array(width * height);
        for (let y = 1; y < height - 1; y++) {
          for (let x = 1; x < width - 1; x++) {
            const i = y * width + x;
            laplacian[i] = 
              gray[i - width] * 1 +
              gray[i - 1] * 1 +
              gray[i] * -4 +
              gray[i + 1] * 1 +
              gray[i + width] * 1;
          }
        }
        
        let sum = 0;
        let sqSum = 0;
        const count = (width - 2) * (height - 2);
        for (let y = 1; y < height - 1; y++) {
          for (let x = 1; x < width - 1; x++) {
            const val = laplacian[y * width + x];
            sum += val;
            sqSum += val * val;
          }
        }
        
        const mean = sum / count;
        const variance = (sqSum / count) - (mean * mean);
        
        let issue = null;
        if (avgBrightness < 30) {
          issue = "Too dark — try better lighting.";
        } else if (avgBrightness > 230) {
          issue = "Overexposed — image is too bright.";
        } else if (variance < 60) {
          issue = "This image looks blurry — try holding the camera steady.";
        }
        
        resolve({ objectUrl, issue });
      };
      
      img.onerror = () => {
        resolve({ objectUrl: null, issue: "Could not read image." });
      };
      
      img.src = objectUrl;
    });
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsChecking(true);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setQualityIssue(null);

    const result = await checkImageQuality(file);
    
    setPreviewUrl(result.objectUrl);
    setQualityIssue(result.issue);
    setIsChecking(false);
  };

  const handleRetake = () => {
    setPreviewUrl(null);
    setQualityIssue(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (uploadInputRef.current) uploadInputRef.current.value = '';
  };

  const handleSubmit = () => {
    setIsSubmitting(true);
    setTimeout(() => {
      // If quality was flagged, route to a review-pending dossier mock (SKU-104)
      // If good, route to a compliant mock (SKU-101)
      if (qualityIssue) {
        navigate('/inspection/SKU-104'); 
      } else {
        navigate('/inspection/SKU-101');
      }
    }, 1500);
  };

  return (
    <div className="flex flex-col gap-6 max-w-3xl mx-auto h-full justify-center pb-20">
      
      <div className="text-center mb-2">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Single Scan</h1>
        <p className="text-[11px] text-text-muted mt-2 uppercase tracking-widest font-bold">Field Officer Mobile Capture</p>
      </div>

      <GridContainer>
        <Card className="col-span-1 md:col-span-2 lg:col-span-12 relative overflow-hidden shadow-lg border-border-subtle bg-canvas rounded-3xl mx-auto w-full max-w-md">
          
          {/* Main Content Area */}
          <CardBody noPadding className="flex flex-col relative min-h-[500px]">
            
            {/* STATE 1: Waiting for input */}
            {!previewUrl && !isChecking && (
              <div className="flex-1 flex flex-col items-center justify-center p-6 bg-sidebar rounded-t-[1.3rem]">
                <div className="absolute inset-0 pointer-events-none opacity-50 flex items-center justify-center">
                  <div className="w-3/4 h-3/4 border border-white/20 relative">
                     <div className="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-primary-light"></div>
                     <div className="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-primary-light"></div>
                     <div className="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-primary-light"></div>
                     <div className="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-primary-light"></div>
                  </div>
                </div>

                <ScanLine className="w-16 h-16 text-primary-light/50 mb-4 animate-pulse" />
                <div className="text-white font-bold tracking-widest uppercase text-sm mb-2 text-center">Align Label in Frame</div>
                <div className="text-white/70 text-xs max-w-xs text-center">Ensure MRP and Net Quantity are visible</div>
              </div>
            )}

            {/* STATE 2: Checking Quality Loading */}
            {isChecking && (
              <div className="flex-1 flex flex-col items-center justify-center p-6 bg-sidebar rounded-t-[1.3rem]">
                <RefreshCw className="w-12 h-12 text-primary-light animate-spin mb-4" />
                <div className="text-white font-bold tracking-widest uppercase text-sm">Checking Image Quality...</div>
              </div>
            )}

            {/* STATE 3: Submitting */}
            {isSubmitting && (
              <div className="absolute inset-0 bg-sidebar/95 z-50 flex flex-col items-center justify-center backdrop-blur-sm rounded-3xl">
                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-primary-light mb-4"></div>
                <div className="text-white font-bold tracking-widest uppercase text-sm">Extracting Metadata...</div>
                <div className="text-primary-light/80 text-xs mt-2">Running rule engine checks</div>
              </div>
            )}

            {/* STATE 4: Preview and Quality Result */}
            {previewUrl && !isChecking && !isSubmitting && (
              <div className="flex-1 flex flex-col">
                <div className="relative flex-1 bg-black overflow-hidden flex items-center justify-center">
                  <img src={previewUrl} alt="Preview" className="max-w-full max-h-[400px] object-contain" />
                  
                  {/* Framing Overlay on Preview */}
                  <div className="absolute inset-0 pointer-events-none opacity-50 flex items-center justify-center">
                    <div className="w-3/4 h-3/4 border border-white/40 relative shadow-[0_0_0_9999px_rgba(0,0,0,0.4)]">
                       <div className="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-primary-light"></div>
                       <div className="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-primary-light"></div>
                       <div className="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-primary-light"></div>
                       <div className="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-primary-light"></div>
                    </div>
                  </div>
                </div>

                {/* Quality Banner */}
                {qualityIssue ? (
                  <div className="bg-status-err-bg border-y border-status-err-border p-4 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-status-err-text shrink-0 mt-0.5" />
                    <div>
                      <div className="text-sm font-bold text-status-err-text">Quality Check Failed</div>
                      <div className="text-xs text-status-err-text/90 mt-0.5">{qualityIssue}</div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-status-ok-bg border-y border-status-ok-border p-4 flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-status-ok-text shrink-0" />
                    <div className="text-sm font-bold text-status-ok-text">Looks good. Ready for extraction.</div>
                  </div>
                )}
                
                {/* Preview Actions */}
                <div className="p-6 bg-card flex flex-col gap-3 shrink-0 rounded-b-3xl">
                   {qualityIssue ? (
                     <>
                       <button onClick={handleRetake} className="w-full py-3.5 bg-status-err-text text-white font-bold rounded-xl shadow-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2">
                         <Camera className="w-5 h-5" /> Retake Photo
                       </button>
                       <button onClick={handleSubmit} className="w-full py-3 bg-canvas border border-border-strong text-text-secondary font-bold rounded-xl hover:bg-border-subtle transition-colors flex items-center justify-center gap-2">
                         Use Anyway <ChevronRight className="w-4 h-4" />
                       </button>
                     </>
                   ) : (
                     <>
                       <button onClick={handleSubmit} className="w-full py-3.5 bg-primary text-white font-bold rounded-xl shadow-sm hover:bg-primary-dark transition-colors flex items-center justify-center gap-2">
                         Use This Photo <ChevronRight className="w-5 h-5" />
                       </button>
                       <button onClick={handleRetake} className="w-full py-3 bg-canvas border border-border-subtle text-text-secondary font-bold rounded-xl hover:bg-border-strong transition-colors">
                         Retake
                       </button>
                     </>
                   )}
                </div>
              </div>
            )}

            {/* Input Controls (Only show when not previewing/checking) */}
            {!previewUrl && !isChecking && (
              <div className="bg-card p-6 flex flex-col items-center justify-center gap-6 shrink-0 rounded-b-[1.3rem]">
                 
                 {/* Hidden inputs */}
                 <input 
                   type="file" 
                   accept="image/*" 
                   capture="environment" 
                   ref={fileInputRef}
                   onChange={handleFileChange}
                   className="hidden" 
                 />
                 <input 
                   type="file" 
                   accept="image/*" 
                   ref={uploadInputRef}
                   onChange={handleFileChange}
                   className="hidden" 
                 />

                 {/* Primary Capture Button */}
                 <button 
                    onClick={() => fileInputRef.current?.click()}
                    className="w-20 h-20 bg-card rounded-full flex items-center justify-center hover:scale-105 transition-transform shadow-2xl ring-4 ring-sidebar relative -mt-16 z-10"
                 >
                    <div className="w-16 h-16 border-2 border-border-subtle rounded-full flex items-center justify-center">
                       <Camera className="w-8 h-8 text-sidebar" />
                    </div>
                 </button>
                 
                 {/* Secondary Upload Link */}
                 <button 
                   onClick={() => uploadInputRef.current?.click()}
                   className="flex items-center gap-2 text-sm font-bold text-primary hover:text-primary-dark transition-colors"
                 >
                   <Upload className="w-4 h-4" /> Upload from device
                 </button>

              </div>
            )}
            
          </CardBody>
        </Card>
      </GridContainer>
    </div>
  );
}
