/**
 * Upload Page — Part of Person 1 (Frontend Lead)'s workspace
 *
 * Supports two modes:
 *   1. Single image upload (drag & drop or file picker)
 *   2. Bulk upload (multiple images or CSV of URLs)
 *
 * Currently renders a mock result from mock_data.json after "upload".
 *
 * TODO(Person 1): Wire to POST /upload/single and /upload/bulk,
 *   then navigate to /results/{id} with the real response.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import mockData from '../data/mock_data.json'

export default function UploadPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('single') // 'single' | 'bulk'
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    setSelectedFiles(files)
  }

  const handleFileChange = (e) => {
    setSelectedFiles(Array.from(e.target.files))
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return
    setUploading(true)

    // TODO(Person 1): Replace with real API call:
    //   const formData = new FormData()
    //   if (mode === 'single') {
    //     formData.append('file', selectedFiles[0])
    //     const res = await fetch('/api/upload/single', { method: 'POST', body: formData })
    //     const data = await res.json()
    //     navigate(`/results/${data.id}`)
    //   } else {
    //     selectedFiles.forEach(f => formData.append('files', f))
    //     const res = await fetch('/api/upload/bulk', { method: 'POST', body: formData })
    //     const data = await res.json()
    //     navigate('/repository')
    //   }

    // Mock: simulate upload delay then show results
    setTimeout(() => {
      setUploading(false)
      navigate('/results')
    }, 1200)
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-2">Upload Inspection</h1>
      <p className="text-slate-400 mb-8">
        Upload product label images for compliance analysis
      </p>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-8">
        {['single', 'bulk'].map((m) => (
          <button
            key={m}
            onClick={() => { setMode(m); setSelectedFiles([]) }}
            className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer ${
              mode === m
                ? 'bg-primary/20 text-primary-light border border-primary/30'
                : 'bg-surface-light text-slate-400 border border-white/5 hover:border-white/15'
            }`}
          >
            {m === 'single' ? '📷 Single Label' : '📦 Bulk Upload'}
          </button>
        ))}
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`glass rounded-2xl p-12 text-center transition-all duration-300 ${
          dragOver ? 'border-primary/50 bg-primary/5 scale-[1.01]' : ''
        }`}
      >
        <div className="text-5xl mb-4">{mode === 'single' ? '📷' : '📦'}</div>
        <p className="text-lg font-medium text-slate-200 mb-2">
          {mode === 'single'
            ? 'Drop a product label image here'
            : 'Drop multiple images or a CSV file'}
        </p>
        <p className="text-sm text-slate-500 mb-6">
          Supports JPG, PNG, WebP {mode === 'bulk' && '• or CSV with image URLs'}
        </p>

        <label className="inline-block px-6 py-3 rounded-xl bg-surface-lighter text-slate-300 hover:text-white hover:bg-surface-lighter/80 transition-all cursor-pointer text-sm font-medium">
          Browse Files
          <input
            type="file"
            className="hidden"
            accept={mode === 'single' ? 'image/*' : 'image/*,.csv'}
            multiple={mode === 'bulk'}
            onChange={handleFileChange}
          />
        </label>

        {/* Selected files list */}
        {selectedFiles.length > 0 && (
          <div className="mt-6 space-y-2">
            {selectedFiles.map((f, i) => (
              <div key={i} className="flex items-center justify-center gap-2 text-sm text-slate-300">
                <span className="w-2 h-2 rounded-full bg-accent" />
                {f.name}
                <span className="text-slate-500">({(f.size / 1024).toFixed(1)} KB)</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload button */}
      {selectedFiles.length > 0 && (
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="px-8 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-semibold hover:shadow-lg hover:shadow-primary/25 transition-all duration-200 disabled:opacity-60 cursor-pointer"
          >
            {uploading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing…
              </span>
            ) : (
              `Analyze ${selectedFiles.length} ${selectedFiles.length === 1 ? 'image' : 'images'}`
            )}
          </button>
        </div>
      )}

      {/* Quick preview of what the system checks */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-12">
        {[
          { icon: '💰', label: 'MRP', desc: 'Maximum Retail Price' },
          { icon: '⚖️', label: 'Net Qty', desc: 'Net Quantity' },
          { icon: '🏭', label: 'Manufacturer', desc: 'Name & Address' },
          { icon: '📅', label: 'Date', desc: 'Mfg / Expiry date' },
        ].map(({ icon, label, desc }) => (
          <div key={label} className="glass rounded-xl p-4 text-center">
            <div className="text-2xl mb-2">{icon}</div>
            <div className="text-sm font-semibold text-slate-200">{label}</div>
            <div className="text-xs text-slate-500">{desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
