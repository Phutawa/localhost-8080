# -*- coding: utf-8 -*-
"""
LLM Provider Module using Gemini
"""
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LLMProvider")

class LLMProvider:
    @staticmethod
    def generate(prompt: str, system_prompt: str = "") -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY is not set.")
            return "[ERROR] Gemini API key missing."
        
        genai.configure(api_key=api_key)
        model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash"
        )
        logger.info(f"Using Gemini model: {model_name}")
        
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_prompt
            )
            response = model.generate_content(prompt)
            
            # Safe text extraction to handle function calls and text parts
            parts = []
            if response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                if finish_reason and finish_reason != 1:
                    logger.warning(f"Gemini response finished with non-stop reason: {finish_reason}")
                
                content = getattr(candidate, 'content', None)
                if content and getattr(content, 'parts', None):
                    for part in content.parts:
                        part_text = getattr(part, 'text', None)
                        if part_text:
                            parts.append(part_text)
                        
                        part_fc = getattr(part, 'function_call', None)
                        if part_fc and part_fc.name:
                            parts.append(f"\n[AI Agent requested tool call: {part_fc.name} with args {dict(part_fc.args)}]")
            
            if parts:
                return "".join(parts)
                
            try:
                return response.text
            except Exception:
                if response.candidates:
                    return f"[LLM Response Blocked/Empty - Finish Reason: {response.candidates[0].finish_reason}]"
                return "[LLM Response Empty]"
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return f"[ERROR] {e}"
