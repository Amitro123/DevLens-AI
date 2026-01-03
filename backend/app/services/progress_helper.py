# Progress callback wrapper for detailed stage tracking
async def create_detailed_progress_callback(session_manager, session_id, original_callback=None):
    """
    Create a progress callback that tracks detailed stage progress.
    
    Maps overall progress (0-100) to stage-specific breakdown:
    - STT/Audio: 0-30%
    - Frames: 30-70%
    - Doc Generation: 70-100%
    """
    async def detailed_callback(progress: int, stage_label: str):
        # Map overall progress to stage-specific breakdown
        stage_progress = {
            "stt": 0,
            "frames": 0,
            "doc": 0
        }
        
        if progress <= 30:
            # STT/Audio analysis phase (0-30%)
            stage_progress["stt"] = int((progress / 30) * 100)
        elif progress <= 70:
            # Frame extraction phase (30-70%)
            stage_progress["stt"] = 100
            stage_progress["frames"] = int(((progress - 30) / 40) * 100)
        else:
            # Doc generation phase (70-100%)
            stage_progress["stt"] = 100
            stage_progress["frames"] = 100
            stage_progress["doc"] = int(((progress - 70) / 30) * 100)
        
        # Update session with detailed progress
        session_manager.update_progress_detailed(
            session_id=session_id,
            stage=stage_label,
            progress=progress,
            stage_progress=stage_progress
        )
        
        # Call original callback if provided
        if original_callback:
            await original_callback(progress, stage_label)
    
    return detailed_callback
