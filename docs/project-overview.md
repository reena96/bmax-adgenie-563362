# Project Overview: AI Video Generation Pipeline for Ad Creation

## Project Summary

Transform Zapcut from a standalone video editor into an AI-powered ad generation platform. Users can create professional video advertisements through conversational AI, automated asset generation, and intelligent video composition.

## Core Workflow

1. **Brand Setup**: Users create brand profiles with product information and visual identity
2. **AI Conversation**: GPT-4 guides users through creative questions about their campaign goals
3. **Script Generation**: AI generates ad scripts with storylines and scene descriptions
4. **Video Production**: Automated pipeline generates visuals (Sora), audio (Suni), and composes final video
5. **Editor Integration**: Generated videos load into Zapcut editor for refinement

## Technical Stack

- **Frontend**: React + TypeScript + Electron (existing Zapcut editor)
- **Backend**: Node.js/Express, PostgreSQL, Redis queue
- **AI Services**: OpenAI GPT-4, Sora (via Replicate), Suni, DALL-E 3
- **Storage**: AWS S3

## Development Phases

The project is divided into 8 sequential phases:

1. **Foundation** (Week 1-2): Backend API, database, auth, landing page
2. **Brand Management** (Week 3): Brand dashboard and CRUD operations
3. **Chat Interface** (Week 4): Conversational AI with GPT-4
4. **Script Generation** (Week 5): AI script creation and review UI
5. **Video Generation Pipeline** (Week 6-8): Queue workers, Sora/Suni integration, FFmpeg composition
6. **Editor Integration** (Week 9): Load generated videos into Zapcut
7. **Polish & Testing** (Week 10-11): E2E testing, performance optimization
8. **Launch Prep** (Week 12): Production deployment, monitoring, beta testing

## Success Metrics

- Time to create first ad: < 10 minutes
- Script approval rate: > 80%
- Video generation success: > 95%
- User retention: > 60%

## Current Status

Project initialized. Ready to begin Phase 1 (Foundation) development.
