import re
import json
import logging

logger = logging.getLogger("experimental_regex_router")

class RegexStataRouter:
    """
    Phase 15 Fast-Path Router to bypass LLM latency for standard Stata commands.
    EXPERIMENTAL: AST Parser is currently deferred. This regex is extremely brittle
    and should only be used as an interim step.
    """
    def __init__(self):
        # Very simple regex patterns for common Stata syntax
        self.patterns = {
            "summarize": re.compile(r"^summarize\s+(.+)$", re.IGNORECASE),
            "regress": re.compile(r"^regress\s+(\w+)\s+(.+)$", re.IGNORECASE),
            "ivregress": re.compile(r"^ivregress\s+(\w+)\s+(.+)\s+\((.+)\s*=\s*(.+)\)$", re.IGNORECASE),
            "hdfe": re.compile(r"^hdfe\s+(\w+)\s+(.+),\s*absorb\((.+)\)$", re.IGNORECASE)
        }

    def attempt_fast_path(self, command_str: str) -> dict | None:
        """
        Attempts to parse the command string using regex.
        Returns the JSON parsed dict identical to what Gemini would generate.
        Returns None if it doesn't match standard syntax (fallback to LLM).
        """
        command_str = command_str.strip()
        
        try:
            # 1. Summarize
            match = self.patterns["summarize"].match(command_str)
            if match:
                vars = [v.strip() for v in match.group(1).split()]
                return {"cmd": "summarize", "varlist": vars}
                
            # 2. Regress
            match = self.patterns["regress"].match(command_str)
            if match:
                depvar = match.group(1).strip()
                indepvars = [v.strip() for v in match.group(2).split()]
                return {"cmd": "regress", "depvar": depvar, "indepvars": indepvars}
                
            # 3. HDFE
            match = self.patterns["hdfe"].match(command_str)
            if match:
                depvar = match.group(1).strip()
                indepvars = [v.strip() for v in match.group(2).split()]
                absorb = [v.strip() for v in match.group(3).split()]
                return {
                    "cmd": "hdfe", 
                    "depvar": depvar, 
                    "indepvars": indepvars, 
                    "options": {"absorb": absorb}
                }
                
            # 4. IVRegress
            match = self.patterns["ivregress"].match(command_str)
            if match:
                depvar = match.group(1).strip()
                indepvars = [v.strip() for v in match.group(2).split()]
                endog = [v.strip() for v in match.group(3).split()]
                instruments = [v.strip() for v in match.group(4).split()]
                return {
                    "cmd": "ivregress",
                    "depvar": depvar,
                    "indepvars": indepvars,
                    "options": {"endog": endog, "instruments": instruments}
                }
        except Exception as e:
            logger.error(f"[REGEX ROUTER EXCEPTION] Failed to parse: {command_str}. Error: {e}")
            return None
            
        logger.info(f"[REGEX ROUTER FALLBACK] Brittle regex failed to parse: {command_str}. Falling back to LLM.")
        return None

def route_user_query(query: str) -> dict:
    """
    Simulation of the agent tool invoking the router.
    Checks regex first. If None, it simulates the LLM call.
    """
    import time
    router = RegexStataRouter()
    
    parsed = router.attempt_fast_path(query)
    if parsed:
        return {"source": "fast_path_regex", "parsed": parsed}
        
    # Simulate LLM call
    time.sleep(3.0) 
    return {"source": "gemini_llm", "parsed": {"cmd": "unknown"}}
