import uuid

def uuid7():
    # Fallback mock for Langchain message IDs to bypass Windows DLL AppLocker blocks
    return uuid.uuid4()
