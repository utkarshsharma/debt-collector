#!/usr/bin/env python3
"""
List available ElevenLabs voices.

This script shows available voices so you can pick one for the debt collection agent.

Usage:
    python scripts/list_voices.py

Required environment variable:
    ELEVENLABS_API_KEY - Your ElevenLabs API key
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY environment variable is required")
        print("   Get your API key from: https://elevenlabs.io/app/settings/api-keys")
        sys.exit(1)

    from elevenlabs import ElevenLabs

    client = ElevenLabs(api_key=api_key)

    print("=" * 70)
    print("  Available ElevenLabs Voices")
    print("=" * 70)
    print()

    try:
        voices = client.voices.get_all()

        # Group by category
        premade = []
        cloned = []

        for voice in voices.voices:
            voice_info = {
                "id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
                "description": getattr(voice, "description", ""),
                "labels": getattr(voice, "labels", {}),
            }

            if voice.category == "cloned":
                cloned.append(voice_info)
            else:
                premade.append(voice_info)

        # Show recommended voices for debt collection (professional, clear)
        print("🎯 RECOMMENDED FOR DEBT COLLECTION (Professional, Clear)")
        print("-" * 70)

        recommended_keywords = ["professional", "warm", "friendly", "clear", "calm"]
        recommended = []

        for voice in premade:
            desc = (voice.get("description") or "").lower()
            labels = voice.get("labels") or {}
            use_case = labels.get("use_case", "").lower()
            accent = labels.get("accent", "")

            # Look for professional/warm voices
            if any(kw in desc for kw in recommended_keywords) or use_case in ["narration", "conversational"]:
                if accent in ["american", "british", ""]:
                    recommended.append(voice)

        # Show top recommendations
        for voice in recommended[:10]:
            labels = voice.get("labels") or {}
            gender = labels.get("gender", "unknown")
            accent = labels.get("accent", "unknown")
            age = labels.get("age", "")

            print(f"  {voice['name']}")
            print(f"    ID: {voice['id']}")
            print(f"    Gender: {gender} | Accent: {accent} | Age: {age}")
            if voice.get("description"):
                desc = voice["description"][:100] + "..." if len(voice["description"]) > 100 else voice["description"]
                print(f"    Description: {desc}")
            print()

        print()
        print("📋 ALL PREMADE VOICES")
        print("-" * 70)

        for voice in premade[:30]:  # Show first 30
            labels = voice.get("labels") or {}
            gender = labels.get("gender", "?")
            accent = labels.get("accent", "?")
            print(f"  {voice['name']:20} | {gender:8} | {accent:12} | {voice['id']}")

        if len(premade) > 30:
            print(f"  ... and {len(premade) - 30} more voices")

        if cloned:
            print()
            print("🎤 YOUR CLONED VOICES")
            print("-" * 70)
            for voice in cloned:
                print(f"  {voice['name']:20} | {voice['id']}")

        print()
        print("=" * 70)
        print("  HOW TO USE")
        print("=" * 70)
        print()
        print("  1. Pick a voice you like from the list above")
        print("  2. Copy the Voice ID")
        print("  3. Add to your .env file:")
        print("     ELEVENLABS_VOICE_ID=<the-voice-id>")
        print()
        print("  💡 For debt collection, I recommend:")
        print("     - Rachel (professional female, clear)")
        print("     - Sarah (warm female, conversational)")
        print("     - Adam (professional male, authoritative)")
        print()

    except Exception as e:
        print(f"❌ Error listing voices: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
