from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
import boto3
import botocore.exceptions
from config.logging_config import logger


class Settings(BaseSettings):
    # AWS Authentication and Session Management
    AWS_PROFILE: str = Field("sbx013-appadmin")
    AWS_REGION: str = Field("us-east-1")
    LANGUAGE_CODE: str = Field("en-US")
    AWS_USE_SESSION: bool = Field(True)  # True for SSO, False for direct IAM usage

    # Environment and Deployment Configuration
    ENVIRONMENT: Environment = Environment.PROD  # Change to Environment.DEV for development
    # DEPLOYMENT_VERSION: str = Field("v0.0")

    # S3 Buckets and Storage Paths
    S3_BLOB_BUCKET: str = Field("damocles-sbx-kendra-document-bucket")
    S3_VIDEO_BUCKET: str = Field("damocles-sbx-videos-bucket")
    S3_CHAT_BUCKET: str = Field("damocles-sbx-ask-auri-chat")
    VIDEO_PREFIX: str = Field("HMIApplication")  # If your videos are in a subfolder, e.g. 'videos/', put that here
    TRANSCRIPT_PREFIX: str = Field("transcripts")  # Where to store transcript JSON files
    LABELS_PREFIX: str = Field("labels")  # Where to store labels JSON files

    # AI/ML and Language Model Configuration
    AWS_AI_SERVICE_ENDPOINT: str = Field("")
    LANGUAGE_MODEL: str = Field("claude_v2")

    # LLM Model
    BEDROCK_MODELS: ClassVar[dict] = {
        "claude-3-sonnet-2": "arn:aws:bedrock:us-east-1:371022474972:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    }

    # Guardrail ARN
    BEDROCK_GUARDRAIL_ARN: str = "arn:aws:bedrock:us-east-1:371022474972:guardrail/si8fm1wrxvo7"
    BEDROCK_GUARDRAIL_VERSION: str = BedrockGuardrailVersion.DRAFT
    
    KENDRA_ENABLED: bool = Field(True)
    KENDRA_INDEX_ID: str = Field("a7804d43-70c1-4541-b037-584a99d63e35")

    # Allow extra environment variables without raising validation errors
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

    def get_aws_client(self, service_name: str):
        if not service_name:
            logger.error("Service name is missing in get_aws_client() call.")
            raise ValueError("AWS service_name must be provided to get_aws_client()")

        try:
            logger.debug(f"Creating AWS client for service: {service_name}")
            
            if self.ENVIRONMENT == Environment.PROD:
                return boto3.client(service_name, region_name=self.AWS_REGION)

            # Local / dev authentication logic
            if "AWS_ACCESS_KEY_ID" in os.environ and "AWS_SECRET_ACCESS_KEY" in os.environ:
                logger.debug("Using AWS credentials from environment variables (IAM).")
                return boto3.client(service_name, region_name=self.AWS_REGION)

            if self.AWS_USE_SESSION:
                session = boto3.Session(profile_name=self.AWS_PROFILE)
                logger.debug(f"Using AWS session with profile: {self.AWS_PROFILE}")
                return session.client(service_name, region_name=self.AWS_REGION)

            logger.debug("Using default boto3 authentication (IAM role assumed).")
            return boto3.client(service_name, region_name=self.AWS_REGION)

        except Exception as e:
            self._handle_aws_client_errors(service_name, e)

            
    # Helper function to handle AWS client errors
    @staticmethod
    def _handle_aws_client_errors(service_name: str, error: Exception):
        if isinstance(error, botocore.exceptions.NoCredentialsError):
            logger.error("No valid AWS credentials found!")
            raise ValueError("AWS authentication failed. No credentials found.")

        elif isinstance(error, botocore.exceptions.PartialCredentialsError):
            logger.error(f"Partial AWS credentials found: {error}")
            raise ValueError("AWS credentials are incomplete. Check your environment variables or profile.")

        elif isinstance(error, botocore.exceptions.BotoCoreError):
            logger.error(f"BotoCore error occurred: {error}")
            raise ValueError(f"Unexpected BotoCore error: {error}")

        else:
            logger.error(f"Unexpected error while creating AWS client: {error}")
            raise ValueError(f"Error initializing AWS client for {service_name}: {error}")

settings = Settings()
