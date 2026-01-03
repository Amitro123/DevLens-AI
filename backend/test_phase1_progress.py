"""Quick test for Phase 1 detailed progress tracking"""
import asyncio
from app.services.progress_helper import create_detailed_progress_callback
from app.services.session_manager import get_session_manager

async def test_detailed_progress():
    """Test detailed progress tracking"""
    print("Testing detailed progress tracking...")
    
    # Test 1: Direct update_progress_detailed
    sm = get_session_manager()
    sm.create_session('test123', {'title': 'Test Session 1'})
    sm.update_progress_detailed(
        'test123', 
        'Testing STT', 
        25, 
        {'stt': 83, 'frames': 0, 'doc': 0}
    )
    
    status = sm.get_status('test123')
    print(f"✓ Test 1 - Direct update:")
    print(f"  Progress: {status['progress']}%")
    print(f"  Stage: {status['stage']}")
    print(f"  Stage Progress: {status['stage_progress']}")
    
    assert status['stage_progress']['stt'] == 83, 'STT progress mismatch'
    assert status['stage_progress']['frames'] == 0, 'Frames should be 0'
    assert status['stage_progress']['doc'] == 0, 'Doc should be 0'
    print("  ✅ Direct update works!\n")
    
    # Test 2: Progress callback wrapper
    sm.create_session('test456', {'title': 'Test Session 2'})
    cb = await create_detailed_progress_callback(sm, 'test456')
    
    # Simulate 50% progress (in frames phase)
    await cb(50, 'Extracting frames')
    
    status = sm.get_status('test456')
    print(f"✓ Test 2 - Progress callback (50% overall):")
    print(f"  Progress: {status['progress']}%")
    print(f"  Stage: {status['stage']}")
    print(f"  Stage Progress: {status['stage_progress']}")
    
    assert status['stage_progress']['stt'] == 100, 'STT should be 100% at 50% overall'
    assert status['stage_progress']['frames'] == 50, 'Frames should be 50% at 50% overall'
    assert status['stage_progress']['doc'] == 0, 'Doc should be 0 at 50% overall'
    print("  ✅ Progress callback works!\n")
    
    # Test 3: Doc generation phase (85%)
    await cb(85, 'Generating documentation')
    status = sm.get_status('test456')
    print(f"✓ Test 3 - Doc generation phase (85% overall):")
    print(f"  Progress: {status['progress']}%")
    print(f"  Stage: {status['stage']}")
    print(f"  Stage Progress: {status['stage_progress']}")
    
    assert status['stage_progress']['stt'] == 100, 'STT should be 100%'
    assert status['stage_progress']['frames'] == 100, 'Frames should be 100%'
    assert status['stage_progress']['doc'] == 50, 'Doc should be 50% at 85% overall'
    print("  ✅ Doc generation tracking works!\n")
    
    print("=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_detailed_progress())
