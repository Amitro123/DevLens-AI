import { useState, useRef } from 'react'
import MeetingSelector from './MeetingSelector'
import UploadForm from './UploadForm'

export default function Dashboard() {
    const [selectedSession, setSelectedSession] = useState(null)
    const [isDevMode, setIsDevMode] = useState(false)
    const uploadRef = useRef(null)

    const handleSessionSelect = (session) => {
        setSelectedSession(session)
        // Smooth scroll to upload area
        setTimeout(() => {
            uploadRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }, 100)
    }

    return (
        <div className="space-y-8">
            {/* Header / Context Selection */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
                <div className="flex items-center gap-3 bg-white p-2 rounded-lg border border-gray-200 shadow-sm">
                    <span className="text-xs font-medium text-gray-600 uppercase tracking-wider">Developer Mode</span>
                    <button
                        onClick={() => setIsDevMode(!isDevMode)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${isDevMode ? 'bg-blue-600' : 'bg-gray-200'}`}
                    >
                        <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isDevMode ? 'translate-x-6' : 'translate-x-1'}`}
                        />
                    </button>
                </div>
            </div>

            <MeetingSelector
                onSessionSelect={handleSessionSelect}
                selectedSessionId={selectedSession?.id}
            />

            {/* Bottom Section: Upload Area */}
            <div ref={uploadRef} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                            {selectedSession ? `Upload Video for: ${selectedSession.title}` : 'Manual Processing'}
                        </h3>
                        <p className="text-sm text-gray-600">
                            {selectedSession
                                ? 'Context primed. Uploading will generate specific documentation.'
                                : 'Select a meeting above or upload manually using standard modes.'}
                        </p>
                    </div>

                    {selectedSession && (
                        <button
                            onClick={() => setSelectedSession(null)}
                            className="text-sm text-gray-500 hover:text-gray-700 underline"
                        >
                            Reset to Manual
                        </button>
                    )}
                </div>

                <UploadForm session={selectedSession} isDevMode={isDevMode} />
            </div>
        </div>
    )
}
