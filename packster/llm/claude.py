"""Claude AI integration for package migration."""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import anthropic
from anthropic import Anthropic

from .prompts import create_migration_prompt
from .parser import parse_migration_response, save_migration_files

logger = logging.getLogger(__name__)


class ClaudeMigrator:
    """Handle package migration using Claude AI."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize the Claude migrator.
        
        Args:
            api_key: Claude API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        
    def migrate_packages(
        self,
        packages: List[Dict[str, Any]],
        output_dir: Optional[Path] = None,
        base_name: str = "llm-migration",
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """Migrate packages using Claude AI.
        
        Args:
            packages: List of package dictionaries from the report
            output_dir: Directory to save output files (optional)
            base_name: Base name for output files
            
        Returns:
            Dictionary containing migration results
        """
        
        logger.info(f"Starting migration for {len(packages)} packages using Claude AI (batch size: {batch_size})")
        
        # Process packages in batches
        all_installable = []
        all_unavailable = []
        
        for i in range(0, len(packages), batch_size):
            batch = packages[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(packages) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} packages)")
            
            # Create the prompt for this batch
            prompt = create_migration_prompt(batch)
            
            # Call Claude API with timeout handling
            try:
                response = self._call_claude(prompt)
                logger.info(f"✅ Batch {batch_num}/{total_batches} completed ({len(batch)} packages)")
                
                # Parse the response
                parsed_response = parse_migration_response(response)
                logger.info(f"Successfully parsed batch {batch_num}")
                
                # Collect results
                all_installable.extend(parsed_response.get("installable_packages", []))
                all_unavailable.extend(parsed_response.get("unavailable_packages", []))
                
            except Exception as e:
                logger.error(f"❌ Failed to process batch {batch_num}: {e}")
                return {
                    "success": False,
                    "error": f"Batch {batch_num} failed: {e}",
                    "parsed_response": None,
                    "saved_files": {},
                    "summary": {}
                }
        
        # Combine all results
        combined_response = {
            "installable_packages": all_installable,
            "unavailable_packages": all_unavailable,
            "installation_script": None  # Will be generated from combined results
        }
        
        logger.info(f"Successfully processed all {len(packages)} packages")
        
        # Save files if output directory is provided
        saved_files = {}
        if output_dir:
            saved_files = save_migration_files(combined_response, output_dir, base_name)
            logger.info(f"Saved migration files to {output_dir}")
        
        # Prepare results
        results = {
            "success": True,
            "parsed_response": combined_response,
            "saved_files": saved_files,
            "summary": self._generate_summary(combined_response)
        }
        
        return results
    
    def _call_claude(self, prompt: str) -> str:
        """Make a call to Claude API.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Claude's response text
        """
        
        try:
            # Try with higher token limit for efficiency
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8000,  # Increased for larger batches
                temperature=0.1,  # Low temperature for consistent results
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            error_str = str(e)
            if "Streaming is required" in error_str or "max_tokens" in error_str.lower():
                # Fallback to streaming with lower token limit
                try:
                    return self._call_claude_streaming(prompt)
                except Exception as stream_error:
                    raise Exception(f"Both regular and streaming calls failed. Streaming error: {stream_error}")
            else:
                raise Exception(f"Unexpected error calling Claude API: {e}")
    
    def _call_claude_streaming(self, prompt: str) -> str:
        """Make a streaming call to Claude API as fallback.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Claude's response text
        """
        
        try:
            stream = self.client.messages.create(
                model=self.model,
                max_tokens=4000,  # Lower limit for streaming
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=True
            )
            
            # Collect the streaming response
            response_text = ""
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    response_text += chunk.delta.text
            
            return response_text
            
        except Exception as e:
            raise Exception(f"Streaming API call failed: {e}")
    
    def _generate_summary(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the migration results.
        
        Args:
            parsed_response: Parsed response from Claude
            
        Returns:
            Summary statistics
        """
        
        installable = parsed_response.get("installable_packages", [])
        unavailable = parsed_response.get("unavailable_packages", [])
        
        # Count by installation method
        method_counts = {}
        for pkg in installable:
            method = pkg.get("installation_method", "unknown")
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "total_packages": len(installable) + len(unavailable),
            "installable_count": len(installable),
            "unavailable_count": len(unavailable),
            "success_rate": len(installable) / (len(installable) + len(unavailable)) * 100 if (len(installable) + len(unavailable)) > 0 else 0,
            "installation_methods": method_counts
        }
    
    def validate_mapping(self, package_name: str, suggested_command: str) -> Dict[str, Any]:
        """Validate a specific package mapping using Claude.
        
        Args:
            package_name: Original package name
            suggested_command: Suggested installation command
            
        Returns:
            Validation result
        """
        
        from .prompts import create_validation_prompt
        
        prompt = create_validation_prompt(package_name, suggested_command)
        
        try:
            response = self._call_claude(prompt)
            
            # Parse validation response
            if "VALID" in response.upper():
                return {"valid": True, "message": "Mapping validated"}
            elif "INVALID" in response.upper():
                return {"valid": False, "message": response}
            elif "ALTERNATIVE:" in response.upper():
                # Extract alternative command
                alt_match = response.split("ALTERNATIVE:", 1)
                if len(alt_match) > 1:
                    return {"valid": False, "alternative": alt_match[1].strip(), "message": response}
                else:
                    return {"valid": False, "message": response}
            else:
                return {"valid": False, "message": "Unclear validation response"}
                
        except Exception as e:
            return {"valid": False, "message": f"Validation failed: {e}"}
