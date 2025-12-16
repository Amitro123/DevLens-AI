import { useState, useEffect } from 'react'
import { api } from '../api'
import { Calendar, Zap, CheckCircle2, Loader2, ArrowRight } from 'lucide-react'

export default function MeetingSelector({ onSessionSelect, selectedSessionId }) {
    const [meetings, setMeetings] = useState([])
    const [loading, setLoading] = useState(true)
    const [processingId, setProcessingId] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchDrafts()
    }, [])

    const fetchDrafts = async () => {
        try {
            const data = await api.getDraftMeetings()
            setMeetings(data) // Expecting array directly
            setLoading(false)
        } catch (err) {
            console.error('Failed to fetch drafts:', err)
            setError('Failed to load meetings')
            setLoading(false)
        }
    }

    const handlePrep = async (e, meeting) => {
        e.stopPropagation()
        setProcessingId(meeting.id)

        try {
            await api.prepSession(meeting.id)

            // Update local state
            setMeetings(prev => prev.map(m =>
                m.id === meeting.id
                    ? { ...m, status: 'ready_for_upload' }
                    : m
            ))
        } catch (err) {
            console.error('Failed to prep session:', err)
            // Revert on error? Or just show toast?
        } finally {
            setProcessingId(null)
        }
    }

    const handleSelect = (meeting) => {
        if (meeting.status === 'ready_for_upload' || meeting.status === 'processing') {
            onSessionSelect(meeting)
        }
    }

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            </div>
        )
    }

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Select Meeting Context
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {meetings.map((meeting) => {
                    const isReady = meeting.status === 'ready_for_upload'
                    const isProcessing = meeting.status === 'processing'
                    const isSelected = selectedSessionId === meeting.id
                    const isPrepping = processingId === meeting.id

                    return (
                        <div
                            key={meeting.id}
                            onClick={() => handleSelect(meeting)}
                            className={`
                                relative p-4 rounded-xl border-2 transition-all cursor-pointer
                                ${isReady
                                    ? 'border-green-500/50 bg-green-50/10 hover:border-green-500 shadow-[0_0_15px_rgba(34,197,94,0.1)]'
                                    : 'border-gray-200 hover:border-gray-300 bg-white'
                                }
                                ${isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
                            `}
                        >
                            {/* Status Badge */}
                            <div className="flex justify-between items-start mb-3">
                                <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                                    {meeting.time ? new Date(meeting.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Scheduled'}
                                </span>
                                {isReady && (
                                    <span className="flex items-center gap-1 text-xs font-bold text-green-600 bg-green-100 px-2 py-1 rounded-full">
                                        <CheckCircle2 className="w-3 h-3" />
                                        Ready
                                    </span>
                                )}
                            </div>

                            {/* Content */}
                            <h4 className="font-semibold text-gray-900 mb-1">{meeting.title}</h4>
                            <div className="flex flex-wrap gap-1 mb-4">
                                {meeting.context_keywords.slice(0, 3).map((kw, i) => (
                                    <span key={i} className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                                        #{kw}
                                    </span>
                                ))}
                            </div>

                            {/* Action Button */}
                            {!isReady ? (
                                <button
                                    onClick={(e) => handlePrep(e, meeting)}
                                    disabled={isPrepping}
                                    className={`
                                        w-full py-2 px-4 rounded-lg text-sm font-medium text-white
                                        bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700
                                        transition-all flex items-center justify-center gap-2
                                        disabled:opacity-70 disabled:cursor-not-allowed
                                    `}
                                >
                                    {isPrepping ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Prepping...
                                        </>
                                    ) : (
                                        <>
                                            <Zap className="w-4 h-4" />
                                            Prep Context
                                        </>
                                    )}
                                </button>
                            ) : (
                                <div className="text-center text-sm font-medium text-green-600 flex items-center justify-center gap-1">
                                    Ready for Upload <ArrowRight className="w-4 h-4" />
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
