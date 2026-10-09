from transcription import transcribe_recording


file_path = "uploads\\Data_Analyst_20260820_140353.webm"


print("Starting transcription...")

result = transcribe_recording(file_path)


if result["success"]:

    print("\n==============================")
    print("TRANSCRIPTION SUCCESSFUL")
    print("==============================")

    print("\nLanguage:")
    print(result["language"])

    print("\nTranscript:")
    print(result["text"])

else:

    print("\n==============================")
    print("TRANSCRIPTION FAILED")
    print("==============================")

    print(result["error"])