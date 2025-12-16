import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { Upload, Users, Tag, Clock, FileVideo, Loader2, CheckCircle, XCircle } from 'lucide-react'

export default function SessionCard({ session, onUploadComplete }) {
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    const onDrop = useCallback(async (acceptedFiles) => {
        if (acceptedFiles.length === 0) return

        const file = acceptedFiles[0]
        setUploading(true)
        setProgress(0)
        setError(null)
        setResult(null)

        const formData = new FormData()
        formData.append('file', file)
        // Mode will be auto-selected based on session's suggested_mode

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress(prev => Math.min(prev + 10, 90))
            }, 500)

            const response = await axios.post(`/api/v1/upload/${session.session_id}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })

            clearInterval(progressInterval)
            setProgress(100)
            setResult(response.data)

            // Notify parent to refresh
            if (onUploadComplete) {
                setTimeout(() => onUploadComplete(), 2000)
            }

        } catch (err) {
            setError(err.response?.data?.detail || 'Upload failed. Please try again.')
        } finally {
            setUploading(false)
        }
    }, [session.session_id, onUploadComplete])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'video/*': ['.mp4', '.mov', '.avi', '.webm']
        },
        maxFiles: 1,
        multiple: false,
        disabled: uploading || result
    })

    // Format time
    const formatTime = (isoString) => {
        const date = new Date(isoString)
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }

    // Get mode badge color
    const getModeColor = (mode) => {
        switch (mode) {
            case 'bug_report':
                return 'bg-red-100 text-red-700'
            case 'feature_kickoff':
                return 'bg-purple-100 text-purple-700'
            default:
                return 'bg-blue-100 text-blue-700'
        }
    }

    return (
        <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
                <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900 flex-1">
                        {session.title}
                    </h3>
                    {session.metadata?.event_start && (
                        <div className="flex items-center gap-1 text-sm text-gray-600">
                            <Clock className="w-4 h-4" />
                            {formatTime(session.metadata.event_start)}
                        </div>
                    )}
                </div>

                {/* Metadata */}
                <div className="space-y-2">
                    {/* Attendees */}
                    {session.attendees && session.attendees.length > 0 && (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Users className="w-4 h-4 flex-shrink-0" />
                            <span className="truncate">{session.attendees.slice(0, 2).join(', ')}
                                {session.attendees.length > 2 && ` +${session.attendees.length - 2} more`}
                            </span>
                        </div>
                    )}

                    {/* Keywords */}
                    {session.context_keywords && session.context_keywords.length > 0 && (
                        <div className="flex items-start gap-2">
                            <Tag className="w-4 h-4 flex-shrink-0 mt-0.5 text-gray-600" />
                            <div className="flex flex-wrap gap-1">
                                {session.context_keywords.map((keyword, idx) => (
                                    <span
                                        key={idx}
                                        className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded"
                                    >
                                        {keyword}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Suggested Mode */}
                    {session.suggested_mode && (
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Suggested:</span>
                            <span className={`px-2 py-1 text-xs font-medium rounded ${getModeColor(session.suggested_mode)}`}>
                                {session.suggested_mode.replace('_', ' ').toUpperCase()}
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Upload Area */}
            <div className="p-6">
                {!result && !error && (
                    <div
                        {...getRootProps()}
                        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${isDragActive
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-300 hover:border-blue-400'
                            } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <input {...getInputProps()} disabled={uploading} />
                        {uploading ? (
                            <div className="space-y-2">
                                <Loader2 className="w-8 h-8 mx-auto text-blue-600 animate-spin" />
                                <p className="text-sm text-gray-600">Processing video...</p>
                                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                                <p className="text-xs text-gray-500">{progress}%</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <Upload className="w-8 h-8 mx-auto text-gray-400" />
                                <p className="text-sm text-gray-600">
                                    {isDragActive ? 'Drop video here' : 'Click or drag video to upload'}
                                </p>
                                <p className="text-xs text-gray-500">MP4, MOV, AVI, WEBM</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Success */}
                {result && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-green-700 mb-2">
                            <CheckCircle className="w-5 h-5" />
                            <span className="font-medium">Documentation Generated!</span>
                        </div>
                        <p className="text-sm text-green-600">
                            Session completed successfully
                        </p>
                    </div>
                )}

                {/* Error */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-red-700 mb-2">
                            <XCircle className="w-5 h-5" />
                            <span className="font-medium">Upload Failed</span>
                        </div>
                        <p className="text-sm text-red-600">{error}</p>
                        <button
                            onClick={() => setError(null)}
                            className="mt-2 text-sm text-red-700 hover:text-red-900 font-medium"
                        >
                            Try Again
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
