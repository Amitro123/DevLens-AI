import { useState } from 'react'
import { api } from '../api'
import { ThumbsUp, ThumbsDown, MessageSquare, Check, Zap, Server, Database, BrainCircuit, Activity, Download, Copy, FileText, CheckSquare } from 'lucide-react'

export default function DocViewer({ content, taskId, isDevMode }) {
    const [rating, setRating] = useState(null)
    const [comment, setComment] = useState('')
    const [showCommentInput, setShowCommentInput] = useState(false)
    const [submitted, setSubmitted] = useState(false)
    const [feedbackLoading, setFeedbackLoading] = useState(false)
    const [showExportMenu, setShowExportMenu] = useState(false)
    const [exportStatus, setExportStatus] = useState(null)

    const handleRate = async (value) => {
        setRating(value)
        if (value === 5) {
            // Auto submit thumbs up
            submitFeedback(5)
        } else {
            // Show comment for improvement
            setShowCommentInput(true)
        }
    }

    const submitFeedback = async (score) => {
        if (!taskId) return

        setFeedbackLoading(true)
        try {
            await api.sendFeedback(taskId, {
                rating: score,
                comment: comment
            })
            setSubmitted(true)
        } catch (err) {
            console.error("Failed to submit feedback:", err)
        } finally {
            setFeedbackLoading(false)
        }
    }

    const handleExport = async (target) => {
        setShowExportMenu(false)
        setExportStatus(`Exporting to ${target}...`)

        if (target === 'clipboard') {
            try {
                await navigator.clipboard.writeText(content)
                setExportStatus('✓ Copied to clipboard!')
                setTimeout(() => setExportStatus(null), 3000)
            } catch (err) {
                setExportStatus('✗ Failed to copy')
                setTimeout(() => setExportStatus(null), 3000)
            }
            return
        }

        // Call backend export API for Notion/Jira
        try {
            await api.exportSession(taskId, target)
            const targetName = target === 'notion' ? 'Notion' : 'Jira'
            setExportStatus(`✓ Exported to ${targetName}!`)
            setTimeout(() => setExportStatus(null), 3000)
        } catch (err) {
            console.error('Export failed:', err)
            setExportStatus('✗ Export failed')
            setTimeout(() => setExportStatus(null), 3000)
        }
    }

    // Mock telemetry data (in production this would come from the API result)
    const telemetry = {
        processingTime: "14.2s",
        cost: "$0.004",
        steps: [
            { name: "Audio Extract", time: "0.8s" },
            { name: "Groq STT", time: "2.1s" },
            { name: "RAG Context", time: "0.5s" },
            { name: "Gemini Pro", time: "10.8s" }
        ],
        contexts: [
            "technical_spec_v2.md",
            "api_routes.py",
            "schema_migration.sql"
        ]
    }

    return (
        <div className="space-y-6">
            {/* ROI Badge */}
            <div className="flex justify-between items-center">
                <div className="bg-yellow-100 text-yellow-800 text-xs px-3 py-1 rounded-full font-medium flex items-center gap-1 shadow-sm border border-yellow-200">
                    <Zap className="w-3 h-3 fill-current" />
                    Saved you ~30 mins
                </div>

                {/* Export Dropdown */}
                <div className="relative">
                    <button
                        onClick={() => setShowExportMenu(!showExportMenu)}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
                    >
                        <Download className="w-4 h-4" />
                        Export
                    </button>
                    {showExportMenu && (
                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                            <button
                                onClick={() => handleExport('clipboard')}
                                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                            >
                                <Copy className="w-4 h-4 text-gray-600" />
                                Copy to Clipboard
                            </button>
                            <button
                                onClick={() => handleExport('notion')}
                                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                            >
                                <FileText className="w-4 h-4 text-gray-600" />
                                Send to Notion
                            </button>
                            <button
                                onClick={() => handleExport('jira')}
                                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                            >
                                <CheckSquare className="w-4 h-4 text-gray-600" />
                                Create Jira Ticket
                            </button>
                        </div>
                    )}
                </div>
            </div>
            {exportStatus && (
                <div className="text-sm text-center text-gray-700 bg-gray-100 px-3 py-1 rounded">
                    {exportStatus}
                </div>
            )}

            {/* Generated Content */}
            <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap text-sm bg-white p-6 rounded-lg border border-gray-200 shadow-sm overflow-x-auto font-mono text-gray-800">
                    {content}
                </pre>
            </div>

            {/* Developer Mode Telemetry */}
            {isDevMode && (
                <div className="bg-slate-900 text-slate-200 rounded-lg p-4 font-mono text-xs shadow-lg border border-slate-700">
                    <div className="flex items-center gap-2 mb-4 text-emerald-400 font-bold border-b border-slate-700 pb-2">
                        <Activity className="w-4 h-4" />
                        SYSTEM TELEMETRY
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div className="bg-slate-800 p-2 rounded">
                            <div className="text-slate-500 mb-1">Total Time</div>
                            <div className="text-lg font-bold text-white">{telemetry.processingTime}</div>
                        </div>
                        <div className="bg-slate-800 p-2 rounded">
                            <div className="text-slate-500 mb-1">Est. Cost</div>
                            <div className="text-lg font-bold text-green-400">{telemetry.cost}</div>
                        </div>
                        <div className="bg-slate-800 p-2 rounded col-span-2">
                            <div className="text-slate-500 mb-1">Model Config</div>
                            <div className="text-white">Gemini 1.5 Pro (temperature=0.2)</div>
                        </div>
                    </div>

                    <div className="mb-4">
                        <div className="text-slate-500 mb-2 flex items-center gap-2">
                            <Server className="w-3 h-3" />
                            Pipeline Latency
                        </div>
                        <div className="space-y-1">
                            {telemetry.steps.map((step, idx) => (
                                <div key={idx} className="flex items-center justify-between bg-slate-800/50 px-2 py-1 rounded">
                                    <span>{step.name}</span>
                                    <span className="text-blue-300">{step.time}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div>
                        <div className="text-slate-500 mb-2 flex items-center gap-2">
                            <Database className="w-3 h-3" />
                            RAG Sources
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {telemetry.contexts.map((ctx, idx) => (
                                <span key={idx} className="bg-indigo-900/50 text-indigo-200 px-2 py-1 rounded text-[10px] border border-indigo-800">
                                    {ctx}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Feedback UI */}
            <div className="bg-gray-50 border border-gray-100 rounded-lg p-4">
                <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-700">How would you rate this documentation?</span>

                    {!submitted ? (
                        <div className="flex gap-2">
                            <button
                                onClick={() => handleRate(5)}
                                className={`p-2 rounded-full hover:bg-green-100 transition-colors ${rating === 5 ? 'bg-green-100 text-green-600' : 'text-gray-400'}`}
                            >
                                <ThumbsUp className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => handleRate(1)}
                                className={`p-2 rounded-full hover:bg-red-100 transition-colors ${rating === 1 ? 'bg-red-100 text-red-600' : 'text-gray-400'}`}
                            >
                                <ThumbsDown className="w-5 h-5" />
                            </button>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2 text-green-600 font-medium">
                            <Check className="w-4 h-4" />
                            Thanks for your feedback!
                        </div>
                    )}
                </div>

                {showCommentInput && !submitted && (
                    <div className="mt-4 animate-in fade-in slide-in-from-top-2">
                        <textarea
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="How can we improve this? (Optional)"
                            className="w-full text-sm p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            rows={3}
                        />
                        <div className="mt-2 flex justify-end">
                            <button
                                onClick={() => submitFeedback(rating)}
                                disabled={feedbackLoading}
                                className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                            >
                                {feedbackLoading ? "Sending..." : "Submit Feedback"}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
