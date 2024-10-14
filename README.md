# Jarvis: Legal Speech-To-Text Solution

Jarvis is a comprehensive Legal Speech-To-Text (STT) solution designed to transcribe and analyze legal audio recordings. It leverages cutting-edge technologies like AWS and OpenAI to provide accurate transcriptions with enhanced features tailored for legal professionals.

## Features

### Dual Mode Operation
- **Sample Mode**: Transcribe a pre-loaded sample audio.
- **Upload Mode**: Upload and transcribe custom audio files.

### Advanced Transcription
- Speaker diarization for multi-speaker audio recordings.
- Uses AWS Transcribe for speech-to-text conversion.

### AI-Powered Post-Processing
- OpenAI GPT-4o integration for intelligent analysis of transcripts.
- Extracts key legal entities and concepts from transcripts.

### Real-time Status Updates
- Live progress tracking for transcription and analysis processes.

### Structured Results
- Displays case information, extracted entities, and segmented transcripts.
- Easy-to-navigate with speaker identification.

### Secure File Handling
- Secure audio file upload to AWS S3.
- File validation for type and size.

## Technical Stack

### Frontend
- Framework: Angular with TypeScript
- Styling: SCSS
- UI Components: Angular Material
- State Management: NgRx

### Backend
- Language: Python
- Architecture: Microservices
- Serverless: AWS Lambda functions

### Cloud Services (AWS)
- Storage: S3 for audio files and transcripts
- Transcription: AWS Transcribe
- Orchestration: AWS Step Functions (State Machine)

### AI Integration
- OpenAI API for transcript post-processing and analysis

## Key Components

### Angular Frontend
- STT-Component: Main component for user interaction
- Info-Component: Shows case information
- Entities-Component: Displays extracted legal entities
- Segments-Component: Renders the speaker-segmented transcript

### AWS Lambda Functions
- File Processing: Handles audio file uploads and preparation
- Transcription: Manages AWS Transcribe jobs
- Enhancement: Integrates with OpenAI for transcript analysis
- Result Storage: Saves processed results to S3

### AWS Step Functions
- Orchestrates the entire workflow from file upload to final result storage

## Legal Audio STT Workflow Overview

This system processes legal audio files by transcribing them, enhancing the transcripts using OpenAI GPT-4o, and storing the results in Amazon S3. It leverages a serverless AWS infrastructure, including multiple Lambda functions, S3 buckets, and AWS Transcribe.

### Key AWS Resources
- **S3 Buckets**:
  - AudioUploadsBucket: Stores uploaded audio files for transcription
  - TranscriptionOutputBucket: Stores the JSON-formatted transcripts
- **Lambda Functions**:
  - StartLambda: Triggers the transcription process
  - TranscribeLambda: Monitors transcription job status
  - EnhanceLambda: Enhances the transcript using OpenAI
  - StoreLambda: Saves the enhanced transcript to S3
  - DataLambda: Reads transcripts from the AudioUploadsBucket

### Workflow
1. Audio file upload to S3 triggers StartLambda
2. StartLambda initiates AWS Transcribe job
3. TranscribeLambda monitors job status and retrieves results
4. EnhanceLambda processes transcript with OpenAI
5. StoreLambda saves final enhanced transcript to S3

## AWS CloudFormation Template Summary

The `AWSTemplate.yaml` defines the resources and configurations for the entire workflow, including Lambda functions, S3 buckets, IAM policies, and a Python dependencies layer.

## Future Development

While Jarvis already provides a robust solution for legal speech-to-text transcription, there are several areas planned for future enhancement:

### Improved Status Checking
- Implement a more accurate status check based on stateMachineARN for better tracking of the transcription process.

### Enhanced Security Measures
- User Authentication: Implement a secure user authentication system to control access to the application.
- File Encryption: Add end-to-end encryption for audio files and transcripts to ensure data privacy.
- Additional Security Measures: Implement best practices for cloud security, including regular security audits and compliance checks.

### Scalability Improvements
- Batching: Develop a batching system for processing multiple files efficiently.
- Large File Handling: Create a specialized UX for larger files that may take hours to process, including:
  - Progress tracking across the entire workflow.
  - Email or push notifications to alert users when transcriptions are complete and provide secure download link.

### AI and Machine Learning Enhancements
- Feedback Loop: Implement a system for users to provide feedback on transcription accuracy, using this data to continually improve the model.
- Custom Vocabulary: Allow users to input industry-specific or case-specific vocabulary to improve transcription accuracy.
- Fine-tuned Named Entity Recognition (NER): Develop a legal-specific NER model to more accurately identify and categorize legal entities within transcripts.

### User Experience Improvements
- Dashboard: Create a user dashboard for managing multiple transcription jobs and viewing historical data.
- Analytics: Provide insights and analytics on transcription data, such as frequently mentioned terms or entities.

### API Development
- Create a robust API to allow integration of Jarvis capabilities into other legal software systems.

### Compliance and Regulations
- Ensure compliance with legal industry standards and data protection regulations (e.g., GDPR, CCPA).

### Multilingual Support
- Expand the system to support multiple languages, catering to international legal proceedings.

These future developments aim to make Jarvis an even more powerful, secure, and user-friendly tool for legal professionals, enhancing its capabilities in transcription accuracy, data security, and overall user experience.
