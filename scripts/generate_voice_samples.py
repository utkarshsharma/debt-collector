#!/usr/bin/env python3
"""
Generate voice samples for the recommended debt collection voices.

This script creates audio samples so you can hear each voice before choosing.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Sample text - a realistic debt collection greeting
SAMPLE_TEXT = """
Hello, this is calling from ABC Financial Services. May I speak with John Smith please?

Hi John, thank you for taking my call. I'm reaching out regarding your account with us.
I noticed your payment of one hundred fifty dollars was due on January 10th, and I wanted
to check in to see if there's anything preventing you from making this payment.

I understand that things can get busy. Would you be able to make that payment today,
or would it work better to set up a payment plan?
"""

# Voices to sample
VOICES = [
    {
        "id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Sarah",
        "description": "Mature, Reassuring, Confident - Female, American",
    },
    {
        "id": "cjVigY5qzO86Huf0OWal",
        "name": "Eric",
        "description": "Smooth, Trustworthy - Male, American",
    },
    {
        "id": "XrExE9yKIg1WjnnlVkGX",
        "name": "Matilda",
        "description": "Knowledgeable, Professional - Female, American",
    },
    {
        "id": "pNInz6obpgDQGcFmaJgB",
        "name": "Adam",
        "description": "Dominant, Firm - Male, American",
    },
]


def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY environment variable is required")
        sys.exit(1)

    from elevenlabs import ElevenLabs

    client = ElevenLabs(api_key=api_key)

    output_dir = Path(__file__).parent.parent / "voice_samples"
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("  Generating Voice Samples")
    print("=" * 60)
    print()
    print(f"  Output directory: {output_dir}")
    print()

    for voice in VOICES:
        print(f"🎙️  Generating sample for {voice['name']}...")
        print(f"    {voice['description']}")

        try:
            # Generate audio
            audio = client.text_to_speech.convert(
                voice_id=voice["id"],
                text=SAMPLE_TEXT,
                model_id="eleven_turbo_v2",
                voice_settings={
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                    "speed": 1.0,
                }
            )

            # Save to file
            filename = f"{voice['name'].lower()}_sample.mp3"
            filepath = output_dir / filename

            with open(filepath, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            print(f"    ✅ Saved to: {filepath}")
            print()

        except Exception as e:
            print(f"    ❌ Error: {e}")
            print()

    print("=" * 60)
    print("  All samples generated!")
    print("=" * 60)
    print()
    print(f"  📁 Listen to the samples in: {output_dir}")
    print()
    print("  Files:")
    for voice in VOICES:
        filename = f"{voice['name'].lower()}_sample.mp3"
        print(f"    - {filename} ({voice['description']})")
    print()
    print("  Once you've listened, tell me which voice you prefer!")
    print()


if __name__ == "__main__":
    main()
