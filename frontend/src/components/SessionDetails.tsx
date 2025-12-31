import { useRef } from "react";
import { motion } from "framer-motion";
import { X, Play, Clock, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { type Session } from "@/api";
import { ExportOptions } from "./ExportOptions";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface SessionDetailsProps {
    session: Session;
    onClose: () => void;
}

// Format seconds to MM:SS
const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
};

export const SessionDetails = ({ session, onClose }: SessionDetailsProps) => {
    const videoRef = useRef<HTMLVideoElement>(null);

    const handleSeek = (seconds: number) => {
        if (videoRef.current) {
            videoRef.current.currentTime = seconds;
            videoRef.current.play();
        }
    };

    const documentation = session.doc_markdown || session.result || "";

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-foreground">{session.title}</h2>
                    <p className="text-sm text-muted-foreground">
                        {session.status === "completed" ? "✅ Completed" : session.status}
                    </p>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose}>
                    <X className="w-5 h-5" />
                </Button>
            </div>

            {/* Video Player */}
            {session.video_url && (
                <section className="glass rounded-xl p-4">
                    <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <Play className="w-5 h-5" /> Video
                    </h3>
                    <video
                        ref={videoRef}
                        src={session.video_url}
                        controls
                        className="w-full rounded-lg bg-black"
                        onLoadedMetadata={() => console.log("Video ready")}
                    />
                </section>
            )}

            {/* Key Frames Timeline */}
            {session.key_frames && session.key_frames.length > 0 && (
                <section className="glass rounded-xl p-4">
                    <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <Clock className="w-5 h-5" /> Key Moments (Click to Jump)
                    </h3>
                    <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-12 gap-2">
                        {session.key_frames.map((frame, idx) => (
                            <button
                                key={idx}
                                className="group bg-secondary border border-border rounded-lg p-1 hover:border-primary/50 hover:scale-105 transition-all"
                                onClick={() => handleSeek(frame.timestamp_sec)}
                            >
                                <img
                                    src={frame.thumbnail_url}
                                    alt={`Frame ${formatTime(frame.timestamp_sec)}`}
                                    className="w-full h-12 object-cover rounded"
                                />
                                <div className="text-xs text-center text-muted-foreground group-hover:text-primary mt-1">
                                    {frame.label || formatTime(frame.timestamp_sec)}
                                </div>
                            </button>
                        ))}
                    </div>
                </section>
            )}

            {/* Transcript Timeline */}
            {session.segments && session.segments.length > 0 && (
                <section className="glass rounded-xl p-4">
                    <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                        <FileText className="w-5 h-5" /> Transcript Timeline
                    </h3>
                    <div className="max-h-64 overflow-y-auto space-y-1">
                        {session.segments.map((seg, idx) => (
                            <button
                                key={idx}
                                className="flex items-start gap-3 w-full text-left p-2 rounded-lg hover:bg-primary/10 transition-colors"
                                onClick={() => handleSeek(seg.start_sec)}
                            >
                                <span className="font-mono text-xs text-primary bg-primary/10 px-2 py-1 rounded shrink-0">
                                    {formatTime(seg.start_sec)}
                                </span>
                                <span className="text-sm text-muted-foreground">{seg.text}</span>
                            </button>
                        ))}
                    </div>
                </section>
            )}

            {/* Generated Documentation */}
            {documentation && (
                <section className="glass rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                        <FileText className="w-5 h-5" /> Generated Documentation
                    </h3>
                    <div className="prose prose-invert max-w-none bg-secondary/50 rounded-lg p-6 overflow-auto max-h-[600px]">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {documentation}
                        </ReactMarkdown>
                    </div>
                </section>
            )}

            {/* Export Options */}
            <ExportOptions sessionId={session.id} documentation={documentation} />
        </motion.div>
    );
};
