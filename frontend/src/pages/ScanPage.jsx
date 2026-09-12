import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, ScanLine, Smartphone, AlertTriangle, CheckCircle, RefreshCw, ChevronRight, Video, XCircle, Sparkles, Image as ImageIcon } from 'lucide-react';
import { GridContainer, Card, CardBody } from '../components/Primitives';
import { useNavigate } from 'react-router-dom';
import { addInspection } from '../services/api';
import { analyzeScannedImage } from '../utils/ocrScanner';

export default function ScanPage() {
  const navigate = useNavigate();
  const [previewUrl, setPreviewUrl] = useState(null);
  const [currentFileName, setCurrentFileName] = useState('');
  const [scanTarget, setScanTarget] = useState(null); // null by default: auto-detect vision + OCR
  const [detectedPreview, setDetectedPreview] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const [qualityIssue, setQualityIssue] = useState(null); // null if good, string if issue
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLiveCamera, setIsLiveCamera] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);
  const uploadInputRef = useRef(null);

  const handleLoadSample = (productType) => {
    stopLiveCamera();
    setIsChecking(true);
    setScanTarget(productType);
    let url = '/products/nestle_kitkat.jpg';
    let name = 'nestle_kitkat.jpg';
    if (productType === 'kitkat') {
      url = '/products/nestle_kitkat.jpg';
      name = 'nestle_kitkat.jpg';
    } else if (productType === 'apple') {
      url = '/products/apple_iphone15.jpg';
      name = 'apple_iphone15.jpg';
    } else if (productType === 'aashirvaad') {
      url = '/products/aashirvaad_atta.jpg';
      name = 'aashirvaad_atta.jpg';
    } else if (productType === 'pillsbury') {
      url = '/products/pillsbury_atta.jpg';
      name = 'pillsbury_atta.jpg';
    }
    setPreviewUrl(url);
    setCurrentFileName(name);
    setQualityIssue(null);

    analyzeScannedImage(url, productType).then(analysis => {
      setDetectedPreview(analysis);
      setIsChecking(false);
    });
  };

  // Stop video stream helper
  const stopLiveCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsLiveCamera(false);
  };

  // Clean up object URLs and camera stream
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) URL.revokeObjectURL(previewUrl);
      stopLiveCamera();
    };
  }, [previewUrl]);

  const startLiveCamera = async (chosenTarget) => {
    setCameraError(null);
    if (chosenTarget !== undefined) {
      setScanTarget(chosenTarget);
    }
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera not supported on this browser or context.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      setIsLiveCamera(true);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(e => console.error(e));
        }
      }, 100);
    } catch (err) {
      console.warn('Webcam access error:', err);
      setCameraError(err.message || 'Could not access webcam. Using device file picker.');
      setIsLiveCamera(false);
      // Fallback directly to file picker
      fileInputRef.current?.click();
    }
  };

  const captureWebcamFrame = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to persistent base64 Data URL so the user's actual capture is preserved
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    setCurrentFileName(`webcam_scan_${Date.now()}.jpg`);
    stopLiveCamera();
    processDataUrl(dataUrl);
  };

  const checkImageQualityFromUrl = (dataUrl) => {
    return new Promise((resolve) => {
      const img = new Image();
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
        if (avgBrightness < 25) {
          issue = "Too dark — try better lighting.";
        } else if (avgBrightness > 240) {
          issue = "Overexposed — image is too bright.";
        } else if (variance < 40) {
          issue = "This image looks blurry — try holding steady.";
        }
        
        resolve({ issue });
      };
      
      img.onerror = () => {
        resolve({ issue: null });
      };
      
      img.src = dataUrl;
    });
  };

  const processDataUrl = async (dataUrl) => {
    setIsChecking(true);
    setPreviewUrl(dataUrl);
    setQualityIssue(null);

    const [qualityResult, analysisResult] = await Promise.all([
      checkImageQualityFromUrl(dataUrl),
      analyzeScannedImage(dataUrl, scanTarget)
    ]);

    setQualityIssue(qualityResult.issue);
    setDetectedPreview(analysisResult);
    setIsChecking(false);
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCurrentFileName(file.name || 'custom_upload.jpg');
    
    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target.result;
      processDataUrl(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  const handleRetake = () => {
    setPreviewUrl(null);
    setCurrentFileName('');
    setQualityIssue(null);
    setDetectedPreview(null);
    stopLiveCamera();
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (uploadInputRef.current) uploadInputRef.current.value = '';
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    const newId = `SCN-${Math.floor(Math.random() * 9000 + 1000)}`;

    // Use detected analysis or re-run
    const analysis = detectedPreview || await analyzeScannedImage(previewUrl, scanTarget);

    const newEntry = {
      id: newId,
      productName: analysis.productName,
      brand: analysis.brand,
      category: analysis.category,
      marketplace: scanTarget ? `Field Mobile Scan (${analysis.brand})` : 'Field Live Scan',
      timestamp: new Date().toISOString(),
      status: analysis.status,
      netQuantity: analysis.netQuantity,
      mrp: analysis.mrp,
      violationType: analysis.violationType,
      // CRITICAL: ALWAYS USE USER'S EXACT CAPTURED IMAGE
      image: previewUrl,
      evidenceImages: [
        { id: 'ev1', url: previewUrl, hash: `sha256_${Date.now().toString(16)}` }
      ],
      boundingBoxes: analysis.boundingBoxes,
      checklist: analysis.checklist
    };

    await addInspection(newEntry);
    navigate(`/inspection/${newId}`);
  };

  return (
    <div className="flex flex-col gap-5 max-w-3xl mx-auto h-full justify-center pb-20">
      
      <div className="text-center mb-1">
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Single Scan</h1>
        <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">Field Officer Mobile & Webcam Capture</p>
      </div>

      {/* Target Commodity Selector */}
      <div className="flex flex-col items-center gap-2 mb-1">
        <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest flex items-center gap-1.5">
          <span>Target Commodity Mode:</span>
        </span>
        <div className="flex flex-wrap items-center justify-center gap-2">
          <button 
            onClick={() => setScanTarget(null)}
            className={`px-3 py-1.5 border rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5 ${
              scanTarget === null 
                ? 'bg-primary text-white border-primary ring-2 ring-primary/30' 
                : 'bg-card border-border-subtle hover:border-primary text-text-primary'
            }`}
          >
            🔍 Auto-Detect (Vision + OCR)
          </button>
          <button 
            onClick={() => setScanTarget('kitkat')}
            className={`px-3.5 py-1.5 border rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5 ${
              scanTarget === 'kitkat' 
                ? 'bg-rose-500 text-white border-rose-500 ring-2 ring-rose-500/30' 
                : 'bg-card border-border-subtle hover:border-rose-500 text-text-primary'
            }`}
          >
            🍫 Nestlé KitKat ₹30
          </button>
          <button 
            onClick={() => setScanTarget('aashirvaad')}
            className={`px-3 py-1.5 border rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5 ${
              scanTarget === 'aashirvaad' 
                ? 'bg-emerald-600 text-white border-emerald-600 ring-2 ring-emerald-600/30' 
                : 'bg-card border-border-subtle hover:border-emerald-500 text-text-primary'
            }`}
          >
            🌾 Aashirvaad Atta
          </button>
          <button 
            onClick={() => setScanTarget('pillsbury')}
            className={`px-3 py-1.5 border rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5 ${
              scanTarget === 'pillsbury' 
                ? 'bg-amber-600 text-white border-amber-600 ring-2 ring-amber-600/30' 
                : 'bg-card border-border-subtle hover:border-amber-500 text-text-primary'
            }`}
          >
            🥣 Pillsbury Atta
          </button>
          <button 
            onClick={() => setScanTarget('apple')}
            className={`px-3 py-1.5 border rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer flex items-center gap-1.5 ${
              scanTarget === 'apple' 
                ? 'bg-blue-600 text-white border-blue-600 ring-2 ring-blue-600/30' 
                : 'bg-card border-border-subtle hover:border-primary text-text-primary'
            }`}
          >
            🍏 iPhone 15 Pro
          </button>
        </div>
      </div>

      <GridContainer>
        <Card className="col-span-1 md:col-span-2 lg:col-span-12 relative overflow-hidden shadow-lg border-border-subtle bg-canvas rounded-3xl mx-auto w-full max-w-md">
          
          {/* Main Content Area */}
          <CardBody noPadding className="flex flex-col relative min-h-[500px]">
            
            {/* Live Camera Viewfinder */}
            {isLiveCamera && !previewUrl && !isChecking && (
              <div className="relative flex-1 bg-black overflow-hidden flex items-center justify-center min-h-[440px] rounded-t-[1.3rem]">
                <video 
                  ref={videoRef} 
                  playsInline 
                  autoPlay 
                  muted 
                  className="w-full h-full object-cover"
                />
                
                {/* Framing Overlay on Live Camera */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                  <div className="w-3/4 h-3/4 border-2 border-primary-light/80 relative shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]">
                     <div className="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-primary-light"></div>
                     <div className="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-primary-light"></div>
                     <div className="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-primary-light"></div>
                     <div className="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-primary-light"></div>
                  </div>
                </div>

                {/* Top Control Bar on Camera */}
                <div className="absolute top-3 left-3 right-3 flex justify-between items-center z-20">
                  <div className="flex items-center gap-1.5">
                    <span className="bg-black/70 text-white text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full flex items-center gap-1.5 backdrop-blur-xs border border-white/10">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span> Live
                    </span>
                    <span className="bg-black/70 text-white border border-white/20 text-[10px] font-bold px-2.5 py-1 rounded-full backdrop-blur-xs">
                      {scanTarget === 'kitkat' ? '🍫 KitKat ₹30' :
                       scanTarget === 'apple' ? '🍏 iPhone 15' :
                       scanTarget === 'pillsbury' ? '🥣 Pillsbury' :
                       scanTarget === 'aashirvaad' ? '🌾 Atta' : '🔍 Auto-Detect'}
                    </span>
                  </div>
                  <button 
                    onClick={stopLiveCamera} 
                    className="p-1.5 bg-black/60 hover:bg-black/80 text-white rounded-full transition-colors cursor-pointer"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                {/* Quick Target Switcher on Viewfinder */}
                <div className="absolute top-12 inset-x-3 flex justify-center gap-1 z-20">
                  <button 
                    onClick={() => setScanTarget(null)}
                    className={`px-2 py-0.5 text-[9px] font-bold rounded-full backdrop-blur-xs cursor-pointer ${!scanTarget ? 'bg-primary text-white font-extrabold' : 'bg-black/50 text-white/80'}`}
                  >
                    Auto
                  </button>
                  <button 
                    onClick={() => setScanTarget('kitkat')}
                    className={`px-2 py-0.5 text-[9px] font-bold rounded-full backdrop-blur-xs cursor-pointer ${scanTarget === 'kitkat' ? 'bg-rose-500 text-white font-extrabold' : 'bg-black/50 text-white/80'}`}
                  >
                    🍫 KitKat
                  </button>
                  <button 
                    onClick={() => setScanTarget('aashirvaad')}
                    className={`px-2 py-0.5 text-[9px] font-bold rounded-full backdrop-blur-xs cursor-pointer ${scanTarget === 'aashirvaad' ? 'bg-emerald-600 text-white font-extrabold' : 'bg-black/50 text-white/80'}`}
                  >
                    🌾 Atta
                  </button>
                  <button 
                    onClick={() => setScanTarget('apple')}
                    className={`px-2 py-0.5 text-[9px] font-bold rounded-full backdrop-blur-xs cursor-pointer ${scanTarget === 'apple' ? 'bg-blue-600 text-white font-extrabold' : 'bg-black/50 text-white/80'}`}
                  >
                    🍏 iPhone
                  </button>
                </div>

                {/* Bottom Snap Button */}
                <div className="absolute bottom-6 inset-x-0 flex flex-col items-center justify-center gap-2 z-20">
                  <button
                    onClick={captureWebcamFrame}
                    className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-2xl ring-4 ring-primary hover:scale-105 transition-transform cursor-pointer"
                  >
                    <div className="w-12 h-12 rounded-full border-2 border-primary flex items-center justify-center">
                      <Camera className="w-6 h-6 text-primary" />
                    </div>
                  </button>
                  <span className="text-[11px] font-bold text-white uppercase tracking-wider drop-shadow">Click to Snap</span>
                </div>
              </div>
            )}

            {/* STATE 1: Waiting for input */}
            {!previewUrl && !isChecking && !isLiveCamera && (
              <div className="flex-1 flex flex-col items-center justify-center p-6 bg-sidebar rounded-t-[1.3rem] min-h-[440px]">
                <div className="absolute inset-0 pointer-events-none opacity-50 flex items-center justify-center">
                  <div className="w-3/4 h-3/4 border border-white/20 relative">
                     <div className="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-primary-light"></div>
                     <div className="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-primary-light"></div>
                     <div className="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-primary-light"></div>
                     <div className="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-primary-light"></div>
                  </div>
                </div>

                <ScanLine className="w-16 h-16 text-primary-light/50 mb-4 animate-pulse" />
                <div className="text-white font-bold tracking-widest uppercase text-sm mb-2 text-center">Align Product Packet in Frame</div>
                <div className="text-white/70 text-xs max-w-xs text-center mb-6">
                  {scanTarget === 'kitkat' ? 'Hold your Nestlé KitKat ₹30 pack in view' : 'Ensure Brand and MRP/Quantity are visible'}
                </div>
                
                {cameraError && (
                  <div className="text-xs text-rose-300 bg-rose-950/60 border border-rose-800 p-2.5 rounded-xl mb-4 text-center max-w-xs">
                    {cameraError}
                  </div>
                )}
              </div>
            )}

            {/* STATE 2: Checking Quality Loading */}
            {isChecking && (
              <div className="flex-1 flex flex-col items-center justify-center p-6 bg-sidebar rounded-t-[1.3rem] min-h-[440px]">
                <RefreshCw className="w-12 h-12 text-primary-light animate-spin mb-4" />
                <div className="text-white font-bold tracking-widest uppercase text-sm">Analyzing Product & Image Quality...</div>
                <div className="text-primary-light/80 text-xs mt-1">Vision boundary segmentation in progress</div>
              </div>
            )}

            {/* STATE 3: Submitting */}
            {isSubmitting && (
              <div className="absolute inset-0 bg-sidebar/95 z-50 flex flex-col items-center justify-center backdrop-blur-sm rounded-3xl">
                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-primary-light mb-4"></div>
                <div className="text-white font-bold tracking-widest uppercase text-sm">Generating Inspection Dossier...</div>
                <div className="text-primary-light/80 text-xs mt-2">Computing statutory checklist & evidence hash</div>
              </div>
            )}

            {/* STATE 4: Preview and Quality Result */}
            {previewUrl && !isChecking && !isSubmitting && (
              <div className="flex-1 flex flex-col">
                <div className="relative flex-1 bg-black overflow-hidden flex items-center justify-center min-h-[350px]">
                  <img src={previewUrl} alt="Preview" className="max-w-full max-h-[380px] object-contain" />
                  
                  {/* Framing Overlay on Preview */}
                  <div className="absolute inset-0 pointer-events-none opacity-40 flex items-center justify-center">
                    <div className="w-3/4 h-3/4 border border-white/40 relative shadow-[0_0_0_9999px_rgba(0,0,0,0.4)]">
                       <div className="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-primary-light"></div>
                       <div className="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-primary-light"></div>
                       <div className="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-primary-light"></div>
                       <div className="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-primary-light"></div>
                    </div>
                  </div>
                </div>

                {/* Instant Recognition Banner */}
                {detectedPreview && (
                  <div className={`p-3.5 border-y flex items-center justify-between ${
                    detectedPreview.brand === 'No Commercial Label'
                      ? 'bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400'
                      : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                  }`}>
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 shrink-0" />
                      <div>
                        <div className="text-xs font-extrabold">{detectedPreview.productName}</div>
                        <div className="text-[11px] opacity-80">{detectedPreview.brand} • Net Qty: {detectedPreview.netQuantity}</div>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs font-bold font-mono">₹ {detectedPreview.mrp}</div>
                      <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                        detectedPreview.status.includes('Compliant') ? 'bg-emerald-500/20 text-emerald-600' : 'bg-rose-500/20 text-rose-500'
                      }`}>
                        {detectedPreview.status}
                      </span>
                    </div>
                  </div>
                )}

                {/* Quality Banner */}
                {qualityIssue && (
                  <div className="bg-status-err-bg border-b border-status-err-border p-3 flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-status-err-text shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs font-bold text-status-err-text">Image Quality Note</div>
                      <div className="text-[11px] text-status-err-text/90">{qualityIssue}</div>
                    </div>
                  </div>
                )}
                
                {/* Preview Actions */}
                <div className="p-5 bg-card flex flex-col gap-2.5 shrink-0 rounded-b-3xl">
                   <button 
                     onClick={handleSubmit} 
                     className="w-full py-3.5 bg-primary text-white font-bold rounded-xl shadow-sm hover:bg-primary-dark transition-colors flex items-center justify-center gap-2 cursor-pointer"
                   >
                     Process & Analyze Inspection <ChevronRight className="w-5 h-5" />
                   </button>
                   <button 
                     onClick={handleRetake} 
                     className="w-full py-2.5 bg-canvas border border-border-subtle text-text-secondary font-bold text-xs rounded-xl hover:bg-border-strong transition-colors cursor-pointer"
                   >
                     Retake / Choose Another Photo
                   </button>
                </div>
              </div>
            )}

            {/* Input Controls (Only show when not previewing/checking/streaming) */}
            {!previewUrl && !isChecking && !isLiveCamera && (
              <div className="bg-card p-6 flex flex-col items-center justify-center gap-5 shrink-0 rounded-b-[1.3rem]">
                 
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

                 {/* Primary Capture Buttons: Live Camera Scan */}
                 <div className="flex items-center justify-center -mt-16 z-10">
                   <button 
                      onClick={() => startLiveCamera(scanTarget)}
                      title="Open Camera to Scan Product"
                      className="w-20 h-20 bg-primary text-white rounded-full flex items-center justify-center hover:scale-105 transition-transform shadow-2xl ring-4 ring-sidebar cursor-pointer group"
                   >
                      <div className="w-16 h-16 border-2 border-white/40 rounded-full flex items-center justify-center group-hover:border-white transition-colors">
                         <Camera className="w-8 h-8 text-white" />
                      </div>
                   </button>
                 </div>
                 
                 {/* Instructions and Secondary Upload Link */}
                 <div className="flex flex-col items-center gap-2">
                   <span className="text-[12px] font-bold text-text-primary tracking-wide">
                     Click Camera to Start Live Scanner
                   </span>
                   <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                     {scanTarget === 'kitkat' ? 'Target: Nestlé KitKat ₹30 active' : 'Real-time Legal Metrology Bounding Box Extraction'}
                   </span>
                   <div className="flex items-center gap-2 mt-2">
                     <button 
                       onClick={() => uploadInputRef.current?.click()}
                       className="flex items-center gap-1.5 text-xs font-bold text-secondary hover:text-secondary-dark transition-colors cursor-pointer bg-canvas px-3 py-1.5 rounded-lg border border-border-subtle"
                     >
                       <Upload className="w-3.5 h-3.5" /> Upload File
                     </button>
                     {scanTarget && (
                       <button
                         onClick={() => handleLoadSample(scanTarget)}
                         className="flex items-center gap-1.5 text-xs font-bold text-text-secondary hover:text-text-primary transition-colors cursor-pointer bg-canvas px-3 py-1.5 rounded-lg border border-border-subtle"
                       >
                         <ImageIcon className="w-3.5 h-3.5" /> Load Preset
                       </button>
                     )}
                   </div>
                 </div>

              </div>
            )}
            
          </CardBody>
        </Card>
      </GridContainer>
    </div>
  );
}
