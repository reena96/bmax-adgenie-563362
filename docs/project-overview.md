# Project Overview - AI Video Generation Pipeline

## Vision

Transform Zapcut from a standalone video editor into an AI-powered ad generation platform that enables users to create professional video advertisements through conversational AI interactions, automated asset generation, and intelligent video composition.

## Core Concept

The platform allows users to generate high-quality video advertisements by simply describing their product and campaign goals. AI handles script creation, visual asset generation (via Sora), audio composition (via Suno/TTS), and video editing - culminating in a fully editable video in Zapcut's video editor.

## Target Users

- **Primary**: Small business owners and marketers creating social media ads
- **Secondary**: Content creators and agencies managing multiple brand campaigns
- **Tertiary**: E-commerce sellers needing product advertisement videos

## Key Features

1. **Brand Management**: Users create brands with product images and guidelines
2. **AI Chat Interface**: Conversational AI gathers ad requirements through 5 targeted questions
3. **Script Generation**: GPT-4 creates detailed storylines with scene-by-scene breakdowns
4. **Video Generation Pipeline**:
   - Sora generates video scenes with visual continuity
   - Replicate TTS creates professional voiceovers
   - Suno AI composes custom background music
   - Sound effects for product sounds and transitions
5. **Video Composition**: FFmpeg stitches scenes with crossfade transitions, overlays product images, mixes audio layers
6. **LoRA Fine-tuning**: Brand-specific style customization after first video
7. **Zapcut Editor Integration**: Full editing capabilities for final refinements

## Technical Architecture

**Frontend**: Electron + React + TypeScript with glassmorphism design
**Backend**: Python FastAPI with PostgreSQL, Redis (RQ), AWS S3
**AI Services**: OpenAI GPT-4, Sora (Replicate), Suno AI, TTS models
**Video Processing**: FFmpeg for composition and effects

## User Journey

Landing → Auth → Brands Dashboard → Chat (5 questions) → Script Review → Video Generation (6-8 min) → Video Editor → Export

## Success Metrics

- Time to create first ad: < 10 minutes
- Video generation success rate: > 95%
- User satisfaction with scripts: > 80%
- User retention after first ad: > 60%

## Development Status

**Current Phase**: Initial implementation planning and architecture setup
**Target MVP**: 12-week development cycle with phased rollout

## Key Differentiators

- Fully automated video generation with professional quality
- Conversational interface eliminates complex tooling
- Brand-specific customization via LoRA
- Seamless integration with professional editor for refinements
- Complete audio suite (voiceover + music + SFX) included
