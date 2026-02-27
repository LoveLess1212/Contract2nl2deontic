import json
import datetime
import traceback
from pathlib import Path

# Import all prompt templates to replace them in logs
try:
    from structured_output import (
        REPHRASE_SYSTEM_PROMPT,
        CHOOSE_PARSER_SYSTEM_PROMPT,
        QUANTIFIED_SYSTEM_PROMPT,
        BINARY_LOGICAL_SYSTEM_PROMPT,
        UNARY_LOGICAL_SYSTEM_PROMPT,
        CHOOSE_RELATION_SYSTEM_PROMPT,
        ADJECTIVE_SYSTEM_PROMPT,
        INTRANSITIVE_SYSTEM_PROMPT,
        TRANSITIVE_SYSTEM_PROMPT,
        DITRANSITIVE_SYSTEM_PROMPT
    )
    PROMPT_TEMPLATES = {
        'REPHRASE_SYSTEM_PROMPT': REPHRASE_SYSTEM_PROMPT,
        'CHOOSE_PARSER_SYSTEM_PROMPT': CHOOSE_PARSER_SYSTEM_PROMPT,
        'QUANTIFIED_SYSTEM_PROMPT': QUANTIFIED_SYSTEM_PROMPT,
        'BINARY_LOGICAL_SYSTEM_PROMPT': BINARY_LOGICAL_SYSTEM_PROMPT,
        'UNARY_LOGICAL_SYSTEM_PROMPT': UNARY_LOGICAL_SYSTEM_PROMPT,
        'CHOOSE_RELATION_SYSTEM_PROMPT': CHOOSE_RELATION_SYSTEM_PROMPT,
        'ADJECTIVE_SYSTEM_PROMPT': ADJECTIVE_SYSTEM_PROMPT,
        'INTRANSITIVE_SYSTEM_PROMPT': INTRANSITIVE_SYSTEM_PROMPT,
        'TRANSITIVE_SYSTEM_PROMPT': TRANSITIVE_SYSTEM_PROMPT,
        'DITRANSITIVE_SYSTEM_PROMPT': DITRANSITIVE_SYSTEM_PROMPT
    }
except ImportError:
    PROMPT_TEMPLATES = {}

class APILogger:
    """Interceptor for logging API calls between pipeline and LLM wrappers"""
    
    def __init__(self, log_file=None, console_output=True):
        # Generate timestamped filename if not provided
        if log_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create .log directory if it doesn't exist
            log_dir = Path(".log")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"api_calls_{timestamp}.log"
        
        self.log_file = log_file
        self.console_output = console_output
        self.call_count = 0
        self.start_time = datetime.datetime.now()
        
        # Create log file with header
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== API Call Log Started at {self.start_time} ===\n\n")
    
    def _replace_prompts_with_names(self, text):
        """Replace full prompt template text with just [PROMPT_NAME]"""
        result = text
        for prompt_name, prompt_text in PROMPT_TEMPLATES.items():
            if prompt_text in result:
                result = result.replace(prompt_text, f"[{prompt_name}]")
        return result
    
    def log_call(self, wrapper_name, method_name, text, fmt, step_info=""):
        """Log API call before execution"""
        self.call_count += 1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Replace prompt templates with their names
        clean_text = self._replace_prompts_with_names(text)
        
        log_entry = f"""
{'='*80}
[CALL #{self.call_count}] {timestamp}
Wrapper: {wrapper_name}
Method: {method_name}
{f'Step: {step_info}' if step_info else ''}
---
INPUT TEXT:
{clean_text}
---
FORMAT/SCHEMA:
{self._format_schema(fmt)}
{'='*80}
"""
        self._write_log(log_entry)
        return self.call_count
    
    def log_response(self, call_id, response, elapsed_time=None):
        """Log successful API response"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        log_entry = f"""
[RESPONSE #{call_id}] {timestamp}
{f'Elapsed: {elapsed_time:.3f}s' if elapsed_time else ''}
---
RESPONSE:
{self._format_response(response)}
---
SUCCESS ✓
"""
        self._write_log(log_entry)
    
    def log_error(self, call_id, error, elapsed_time=None):
        """Log API error"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        log_entry = f"""
[ERROR #{call_id}] {timestamp}
{f'Elapsed: {elapsed_time:.3f}s' if elapsed_time else ''}
---
ERROR TYPE: {type(error).__name__}
ERROR MESSAGE:
{str(error)}
---
TRACEBACK:
{traceback.format_exc()}
---
FAILED ✗
"""
        self._write_log(log_entry)
    
    def _format_schema(self, fmt):
        """Format schema for logging"""
        try:
            if hasattr(fmt, 'model_json_schema'):
                schema = fmt.model_json_schema()
                return json.dumps(schema, indent=2)
            elif hasattr(fmt, '__name__'):
                return fmt.__name__
            else:
                return str(fmt)
        except Exception as e:
            return f"<Unable to format schema: {e}>"
    
    def _format_response(self, response):
        """Format response for logging"""
        try:
            if hasattr(response, 'model_dump'):
                return json.dumps(response.model_dump(), indent=2)
            elif hasattr(response, 'dict'):
                return json.dumps(response.dict(), indent=2)
            else:
                return str(response)
        except Exception as e:
            return f"<Unable to format response: {e}>"
    
    def _write_log(self, entry):
        """Write log entry to file and optionally console"""
        if self.console_output:
            print(entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(entry + "\n")


class LLMInterceptor:
    """Generic wrapper that intercepts any LLM wrapper calls with logging"""
    
    def __init__(self, llm_wrapper, logger, wrapper_name="LLMWrapper"):
        self.wrapper = llm_wrapper
        self.logger = logger
        self.wrapper_name = wrapper_name
    
    def generate(self, text, fmt):
        """Intercept generate call with logging"""
        import time
        
        # Log the call
        call_id = self.logger.log_call(
            wrapper_name=self.wrapper_name,
            method_name="generate",
            text=text,
            fmt=fmt
        )
        
        start_time = time.time()
        
        try:
            # Make the actual API call
            response = self.wrapper.generate(text, fmt)
            
            elapsed = time.time() - start_time
            
            # Log successful response
            self.logger.log_response(call_id, response, elapsed)
            
            return response
            
        except Exception as e:
            elapsed = time.time() - start_time
            
            # Log the error
            self.logger.log_error(call_id, e, elapsed)
            
            # Re-raise the exception
            raise


# Alias for backwards compatibility
GeminiInterceptor = LLMInterceptor
