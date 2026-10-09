import os
import subprocess




# =========================================
# QUESTION-WISE AUDIO SEGMENTATION
# =========================================

def create_question_segments(
    recording_path,
    question_data,
    output_directory
):
    """
    Split the complete interview recording into
    question-wise audio/video segments.

    Parameters:
        recording_path:
            Complete WebM interview recording.

        question_data:
            List containing question number,
            relative start time and relative end time.

        output_directory:
            Folder where question segments are saved.

    Returns:
        List of generated question segment details.
    """

    # =========================================
    # CHECK RECORDING
    # =========================================

    if not os.path.exists(recording_path):

        return {
            "success": False,
            "message": "Recording file not found",
            "segments": []
        }


    # =========================================
    # CREATE OUTPUT DIRECTORY
    # =========================================

    os.makedirs(
        output_directory,
        exist_ok=True
    )


    generated_segments = []


    # =========================================
    # PROCESS EACH QUESTION
    # =========================================

    for question in question_data:

        question_number = question.get(
            "question_number"
        )

        start_time = question.get(
            "relative_start"
        )

        end_time = question.get(
            "relative_end"
        )


        # =====================================
        # VALIDATE TIMINGS
        # =====================================

        if (
            question_number is None
            or start_time is None
            or end_time is None
        ):

            print(
                f"Skipping Q{question_number}: "
                "invalid timing"
            )

            continue


        # =====================================
        # CALCULATE DURATION
        # =====================================

        duration = (
            float(end_time)
            - float(start_time)
        )


        if duration <= 0:

            print(
                f"Skipping Q{question_number}: "
                "invalid duration"
            )

            continue


        # =====================================
        # OUTPUT FILE
        # =====================================

        output_filename = (
            f"question_{question_number}.webm"
        )

        output_path = os.path.join(
            output_directory,
            output_filename
        )


        # =====================================
        # FFMPEG COMMAND
        # =====================================

        command = [

            "ffmpeg",

            "-y",

            "-ss",
            str(start_time),

            "-i",
            recording_path,

            "-t",
            str(duration),

            "-c",
            "copy",

            output_path
        ]


        print(
            f"\nCreating Q{question_number} segment..."
        )

        print(
            f"Start: {start_time}s"
        )

        print(
            f"End: {end_time}s"
        )

        print(
            f"Duration: {duration}s"
        )


        # =====================================
        # RUN FFMPEG
        # =====================================

        try:

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )


        except (FileNotFoundError, subprocess.TimeoutExpired) as sub_err:

            return {

                "success": False,

                "message":
                    "FFmpeg was not found. "
                    "Please install FFmpeg and "
                    "add it to PATH.",

                "segments":
                    generated_segments

            }


        # =====================================
        # CHECK RESULT
        # =====================================

        if result.returncode != 0:

            print(
                f"FFmpeg failed for Q{question_number}"
            )

            print(
                result.stderr
            )

            continue


        # =====================================
        # VERIFY FILE
        # =====================================

        if not os.path.exists(
            output_path
        ):

            print(
                f"Segment was not created "
                f"for Q{question_number}"
            )

            continue


        # =====================================
        # STORE SEGMENT INFORMATION
        # =====================================

        generated_segments.append({

            "question_number":
                question_number,

            "question":
                question.get(
                    "question",
                    ""
                ),

            "start_time":
                start_time,

            "end_time":
                end_time,

            "duration":
                round(
                    duration,
                    3
                ),

            "segment_path":
                output_path

        })


        print(
            f"Q{question_number} segment created:"
        )

        print(
            output_path
        )


    # =========================================
    # FINAL RESULT
    # =========================================

    print(
        "\n================================="
    )

    print(
        "QUESTION SEGMENTATION COMPLETE"
    )

    print(
        "Segments created:",
        len(generated_segments)
    )

    print(
        "=================================\n"
    )


    return {

        "success": True,

        "message":
            "Question segments created successfully",

        "segments":
            generated_segments

    }
