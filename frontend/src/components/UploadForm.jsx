import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { api } from '../api'
import { Upload, FileVideo, Loader2, CheckCircle, XCircle } from 'lucide-react'
import DocViewer from './DocViewer'

const PROCESSING_STEPS = [
    "Uploading video...",
    "Analyzing audio tracks...",
    "Filtering relevant segments...",
    "Extracting key frames...",
    "Generating documentation..."
]

export default function UploadForm({ session = null, isDevMode = false }) {
    const [modes, setModes] = useState([])
    const [selectedMode, setSelectedMode] = useState('general_doc')
    const [projectName, setProjectName] = useState('')
    const [language, setLanguage] = useState('en')
    // CR_FINDINGS 4.3: Use separate state for file and Drive URL instead of overloading 'file'
    const [videoFile, setVideoFile] = useState(null)     // For file uploads (File object)
    const [driveUrl, setDriveUrl] = useState('')          // For Drive imports (string URL)
    const [uploadMode, setUploadMode] = useState('file')  // 'file' | 'drive'
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [statusMessage, setStatusMessage] = useState("")

    // Update form when session changes
    useEffect(() => {
        if (session) {
            setProjectName(session.title)
            if (session.suggested_mode) {
                setSelectedMode(session.suggested_mode)
            }
        }
    }, [session])

    // Fetch available modes on mount
    useEffect(() => {
        fetchModes()
    }, [])

    const fetchModes = async () => {
        try {
            const data = await api.getModes()
            setModes(data.modes || [])
        } catch (err) {
            console.error('Failed to fetch modes:', err)
            // Fallback modes
            setModes([
                { mode: 'general_doc', name: 'Technical Documentation', description: 'General documentation' },
                { mode: 'bug_report', name: 'Bug Report', description: 'Bug analysis' },
                { mode: 'feature_spec', name: 'Feature Spec', description: 'Feature requirements' }
            ])
        }
    }

    const onDrop = useCallback((acceptedFiles) => {
        if (acceptedFiles.length > 0) {
            setVideoFile(acceptedFiles[0])
            setError(null)
            setResult(null)
        }
    }, [])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'video/*': ['.mp4', '.mov', '.avi', '.webm']
        },
        maxFiles: 1,
        multiple: false
    })

    const handleSubmit = async (e) => {
        e.preventDefault()

        // Check if we have input based on current mode
        const hasInput = uploadMode === 'drive' ? driveUrl.trim() : videoFile
        if (!hasInput) {
            setError(uploadMode === 'drive' ? 'Please enter a Drive URL' : 'Please select a video file')
            return
        }

        setUploading(true)
        setProgress(0)
        setError(null)
        setResult(null)
        setStatusMessage(PROCESSING_STEPS[0])

        try {
            // Simulate progress
            let stepIndex = 0
            const progressInterval = setInterval(() => {
                setProgress(prev => {
                    const next = Math.min(prev + 5, 90)
                    if (next > 20 && stepIndex === 0) { stepIndex = 1; setStatusMessage(PROCESSING_STEPS[1]) }
                    else if (next > 40 && stepIndex === 1) { stepIndex = 2; setStatusMessage(PROCESSING_STEPS[2]) }
                    else if (next > 60 && stepIndex === 2) { stepIndex = 3; setStatusMessage(PROCESSING_STEPS[3]) }
                    else if (next > 80 && stepIndex === 3) { stepIndex = 4; setStatusMessage(PROCESSING_STEPS[4]) }
                    return next
                })
            }, 600)

            let data;

            // Handle Drive Upload (URL)
            if (uploadMode === 'drive') {
                if (!session) {
                    throw new Error("Drive import currently requires an active session context.")
                }
                data = await api.uploadFromDrive({
                    url: driveUrl,
                    session_id: session.id
                    // access_token: ... // Implement auth flow later
                })
            }
            // Handle File Upload
            else {
                const formData = new FormData()
                formData.append('file', videoFile)

                if (session) {
                    // Session context upload
                    formData.append('mode', selectedMode)
                    data = await api.uploadToSession(session.id, formData)
                } else {
                    // Manual upload
                    formData.append('project_name', projectName || 'Untitled Project')
                    formData.append('language', language)
                    formData.append('mode', selectedMode)
                    data = await api.manualUpload(formData)
                }
            }

            clearInterval(progressInterval)
            setProgress(100)
            setResult(data)

        } catch (err) {
            console.error(err)
            setError(err.response?.data?.detail || err.message || 'Upload failed. Please try again.')
        } finally {
            setUploading(false)
        }
    }

    const resetForm = () => {
        setVideoFile(null)
        setDriveUrl('')
        setUploadMode('file')
        setProjectName('')
        setResult(null)
        setError(null)
        setProgress(0)
    }

    return (
        <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="flex border-b border-gray-200 mb-6">
                <button
                    type="button"
                    onClick={() => {
                        setUploadMode('file')
                        setError(null)
                    }}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${uploadMode === 'file'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                >
                    Upload Video
                </button>
                <button
                    type="button"
                    onClick={() => {
                        setUploadMode('drive')
                        setError(null)
                    }}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${uploadMode === 'drive'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                >
                    Import from Drive
                </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">

                {/* Mode Selector (Shared) */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Documentation Mode
                    </label>
                    <select
                        value={selectedMode}
                        onChange={(e) => setSelectedMode(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={uploading}
                    >
                        {/* Group modes by department */}
                        {['R&D', 'HR', 'Finance'].map(dept => {
                            const deptModes = modes.filter(m => m.department === dept)
                            if (deptModes.length === 0) return null

                            return (
                                <optgroup key={dept} label={`${dept} Department`}>
                                    {deptModes.map((mode) => (
                                        <option key={mode.mode} value={mode.mode}>
                                            {mode.name}
                                        </option>
                                    ))}
                                </optgroup>
                            )
                        })}
                    </select>
                    {modes.find(m => m.mode === selectedMode) && (
                        <div className="mt-2 flex items-start gap-2">
                            {/* Department Badge */}
                            <span className={`text-xs px-2 py-0.5 rounded font-medium ${modes.find(m => m.mode === selectedMode).department === 'R&D' ? 'bg-blue-100 text-blue-700' :
                                modes.find(m => m.mode === selectedMode).department === 'HR' ? 'bg-purple-100 text-purple-700' :
                                    'bg-green-100 text-green-700'
                                }`}>
                                {modes.find(m => m.mode === selectedMode).department}
                            </span>
                            <p className="text-sm text-gray-600 flex-1">
                                {modes.find(m => m.mode === selectedMode).description}
                            </p>
                        </div>
                    )}
                </div>

                {/* Project Name (Shared) */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Project Name (Optional)
                    </label>
                    <input
                        type="text"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                        placeholder="My Awesome Project"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={uploading}
                    />
                </div>

                {/* Language Selector (Shared) */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Language
                    </label>
                    <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={uploading}
                    >
                        <option value="en">English</option>
                        <option value="he">Hebrew</option>
                    </select>
                </div>

                {/* Content Area based on Tab */}
                {uploadMode === 'drive' ? (
                    // Drive Input
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Google Drive Link
                        </label>
                        <input
                            type="text"
                            value={driveUrl}
                            placeholder="https://drive.google.com/file/d/..."
                            onChange={(e) => setDriveUrl(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            disabled={uploading}
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            Paste a public link or ensure the file is shared.
                        </p>
                    </div>
                ) : (
                    // File Dropzone
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Video File
                        </label>
                        <div
                            {...getRootProps()}
                            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-300 hover:border-blue-400'
                                } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <input {...getInputProps()} disabled={uploading} />
                            {videoFile ? (
                                <div className="flex items-center justify-center gap-2 text-green-600">
                                    <FileVideo className="w-6 h-6" />
                                    <span className="font-medium">{videoFile.name}</span>
                                    <span className="text-sm text-gray-500">
                                        ({(videoFile.size / 1024 / 1024).toFixed(2)} MB)
                                    </span>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <Upload className="w-12 h-12 mx-auto text-gray-400" />
                                    <p className="text-gray-600">
                                        {isDragActive
                                            ? 'Drop your video here'
                                            : 'Drag & drop a video, or click to select'}
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        Supports MP4, MOV, AVI, WEBM (max 15 minutes)
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={!(uploadMode === 'drive' ? driveUrl.trim() : videoFile) || uploading}
                    className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                    {uploading ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            {statusMessage || "Processing..."}
                        </>
                    ) : (
                        <>
                            {uploadMode === 'drive' ? (
                                <>
                                    <Upload className="w-5 h-5" />
                                    Import & Analyze
                                </>
                            ) : (
                                <>
                                    <Upload className="w-5 h-5" />
                                    Generate Documentation
                                </>
                            )}
                        </>
                    )}
                </button>
            </form>

            {/* Progress Bar */}
            {
                uploading && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm text-gray-600">
                            <span>{statusMessage}</span>
                            <span>{progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>
                )
            }

            {/* Error Message */}
            {
                error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                        <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <h4 className="font-medium text-red-900">Error</h4>
                            <p className="text-sm text-red-700 mt-1">{error}</p>
                        </div>
                    </div>
                )
            }

            {/* Success Result */}
            {
                result && (
                    <div className="space-y-4">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                                <h4 className="font-medium text-green-900">Documentation Generated!</h4>
                                <p className="text-sm text-green-700 mt-1">
                                    Task ID: {result.task_id}
                                </p>
                            </div>
                            <button
                                onClick={resetForm}
                                className="text-sm text-green-700 hover:text-green-900 font-medium"
                            >
                                Upload Another
                            </button>
                        </div>

                        {/* Documentation Preview */}
                        {/* Documentation Preview with Feedback Loop */}
                        <div className="bg-white rounded-lg shadow-sm">
                            <div className="p-4 border-b border-gray-100 flex justify-between items-center">
                                <h3 className="font-semibold text-gray-900">
                                    Generated Documentation
                                </h3>
                                {isDevMode && (
                                    <span className="text-xs bg-slate-800 text-slate-200 px-2 py-1 rounded font-mono">
                                        DEV MODE ACTIVE
                                    </span>
                                )}
                            </div>
                            <div className="p-6">
                                <DocViewer
                                    content={result.result}
                                    taskId={result.task_id}
                                    isDevMode={isDevMode}
                                />
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    )
}
