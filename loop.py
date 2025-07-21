import argparse
import json
import sys
import os
import logging
import time
from datetime import datetime

import dspy

from atlas_config import get_openrouter_api_key
from aider.openrouter_client import send_prompt_to_openrouter
from aider.handover_manager import HandoverManager
from aider.handover_generator import HandoverDocumentGenerator

# Basic OpenRouter setup if not already in env
dspy.settings.configure(
    model='openrouter/google/gemini-pro',
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Keep console output
    ]
)

class CodeAgent:
    """
    A simplified agent to interact with the environment using provided tools.
    """
    def __init__(self, auto_commit: bool = True, dry_run: bool = False, log_file: str = None, default_api=None, enable_handover: bool = True):
        self.auto_commit = auto_commit
        self.dry_run = dry_run
        self.default_api = default_api
        self.enable_handover = enable_handover
        self.session_start_time = time.time()
        self.instructions_processed = 0
        self.handover_threshold = 50  # Number of instructions before considering handover
        
        # Initialize handover system
        if self.enable_handover:
            try:
                self.handover_manager = HandoverManager()
                self.handover_generator = HandoverDocumentGenerator(self.handover_manager)
                logging.info("Handover system initialized for loop.py session")
            except Exception as e:
                logging.warning(f"Failed to initialize handover system: {e}")
                self.enable_handover = False
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(file_handler)

    def read_file(self, path: str):
        """Reads and returns the content of a specified file."""
        logging.info(f"CodeAgent.read_file called for: {path}")
        if self.dry_run:
            logging.info(f"Dry run: Would read file {path}")
            return {"dry_run_result": f"Would read file {path}"}
        try:
            result = self.default_api.read_file(absolute_path=path)
            if "read_file_response" in result and "output" in result["read_file_response"]:
                logging.info(f"Successfully read file {path}")
            elif "error" in result:
                logging.error(f"Error reading file {path}: {result['error']}")
            return result
        except Exception as e:
            logging.error(f"Error reading file {path}: {e}")
            return {"error": f"Error reading file {path}: {e}"}

    def edit_file(self, path: str, new_content: str):
        """Writes content to a specified file."""
        logging.info(f"CodeAgent.edit_file called for: {path}")
        if self.dry_run:
            logging.info(f"Dry run: Would edit file {path}")
            return {"dry_run_result": f"Would edit file {path}"}
        try:
            result = self.default_api.write_file(file_path=path, content=new_content)
            if "write_file_response" in result and "output" in result["write_file_response"]:
                logging.info(f"Successfully edited file {path}")
                if self.auto_commit:
                    self.save_snapshot(f"auto: edited {path}")
            elif "error" in result:
                logging.error(f"Error editing file {path}: {result['error']}")
            return result
        except Exception as e:
            logging.error(f"Error editing file {path}: {e}")
            return {"error": f"Error editing file {path}: {e}"}

    def run_command(self, cmd: str):
        """Executes a shell command."""
        logging.info(f"CodeAgent.run_command called for: {cmd}")
        if self.dry_run:
            logging.info(f"Dry run: Would run command {cmd}")
            return {"dry_run_result": f"Would run command {cmd}"}
        try:
            result = self.default_api.run_shell_command(command=cmd)
            if result.get("run_shell_command_response", {}).get("Error") == "(none)" and \
               result.get("run_shell_command_response", {}).get("Exit Code") == 0:
                logging.info(f"Successfully ran command {cmd}")
                if self.auto_commit:
                    self.save_snapshot(f"auto: ran command {cmd}")
            else:
                logging.error(f"Error running command {cmd}: {result}")
            return result
        except Exception as e:
            logging.error(f"Error running command {cmd}: {e}")
            return {"error": f"Error running command {cmd}: {e}"}

    def save_snapshot(self, message: str = "auto: save snapshot"):
        """Adds all changes and commits them to the git repository."""
        logging.info(f"CodeAgent.save_snapshot called with message: {message}")
        if self.dry_run:
            logging.info(f"Dry run: Would save snapshot with message: {message}")
            return {"dry_run_result": f"Would save snapshot with message: {message}"}
        try:
            add_result = self.run_command("git add .")
            if "error" in add_result and add_result["error"]:
                logging.error(f"Error during git add: {add_result['error']}")
                return {"error": f"Error during git add: {add_result['error']}"}

            commit_result = self.run_command(f"git commit -m \"{message}\"")
            if "error" in commit_result and commit_result["error"]:
                logging.error(f"Error during git commit: {commit_result['error']}")
                return {"error": f"Error during git commit: {commit_result['error']}"}

            logging.info(f"Successfully saved snapshot: {message}")
            return {"success": "Snapshot saved."}
        except Exception as e:
            logging.error(f"Error saving snapshot: {e}")
            return {"error": f"Error saving snapshot: {e}"}

    def check_file_exists(self, path: str):
        """Checks if a file exists at the given path."""
        logging.info(f"CodeAgent.check_file_exists called for: {path}")
        exists = os.path.exists(path)
        logging.info(f"File {path} exists: {exists}")
        return {"exists": exists}
    
    def _check_handover_conditions(self):
        """Check if handover conditions are met for loop.py session"""
        if not self.enable_handover:
            return False
        
        try:
            # Check instruction count threshold
            if self.instructions_processed >= self.handover_threshold:
                logging.info(f"Handover threshold reached: {self.instructions_processed} instructions processed")
                return True
            
            # Check session duration (handover after 30 minutes)
            session_duration = time.time() - self.session_start_time
            if session_duration > 1800:  # 30 minutes
                logging.info(f"Session duration threshold reached: {session_duration:.1f} seconds")
                return True
            
            return False
            
        except Exception as e:
            logging.warning(f"Error checking handover conditions: {e}")
            return False
    
    def capture_handover_state(self, reason="session_checkpoint", trigger="automatic"):
        """Capture current loop.py session state for handover"""
        if not self.enable_handover:
            return None
        
        try:
            # Create a mock coder-like object for handover state capture
            mock_session = {
                'session_type': 'loop.py',
                'session_start_time': self.session_start_time,
                'instructions_processed': self.instructions_processed,
                'handover_threshold': self.handover_threshold,
                'working_directory': os.getcwd(),
                'session_duration': time.time() - self.session_start_time
            }
            
            # Capture state using handover manager
            state = self.handover_manager.capture_current_state(
                coder=None,  # loop.py doesn't use a coder object
                reason=reason,
                trigger=trigger
            )
            
            # Add loop.py specific context
            if hasattr(state, 'conversation_context'):
                state.conversation_context.update(mock_session)
            
            # Save state
            state_file = self.handover_manager.save_handover_state(state)
            logging.info(f"Loop.py handover state captured: {state_file}")
            
            return state_file
            
        except Exception as e:
            logging.error(f"Failed to capture handover state: {e}")
            return None
    
    def trigger_handover(self, reason="automatic", manual=False):
        """Trigger handover process for loop.py session"""
        if not self.enable_handover:
            logging.warning("Handover system not enabled")
            return False
        
        try:
            trigger_type = "manual" if manual else "automatic"
            logging.info(f"Triggering handover: {reason} ({trigger_type})")
            
            # Capture final state
            state_file = self.capture_handover_state(reason=reason, trigger=trigger_type)
            
            if state_file:
                # Generate handover document
                document = self.handover_generator.generate_full_handover_document(
                    coder=None, reason=reason, trigger=trigger_type
                )
                
                # Update LLM_HANDOVER.md
                self.handover_generator.update_handover_md_file(document)
                
                print(f"\n🔄 Handover Complete")
                print(f"Reason: {reason}")
                print(f"State saved to: {state_file}")
                print(f"Instructions processed: {self.instructions_processed}")
                print(f"Session duration: {time.time() - self.session_start_time:.1f}s")
                print(f"Updated: LLM_HANDOVER.md")
                
                return True
            else:
                logging.error("Failed to capture handover state")
                return False
                
        except Exception as e:
            logging.error(f"Error during handover: {e}")
            return False
    
    def process_instruction(self, instruction):
        """Process instruction and check for handover conditions"""
        self.instructions_processed += 1
        
        # Check for handover conditions every 10 instructions
        if self.instructions_processed % 10 == 0:
            if self._check_handover_conditions():
                self.trigger_handover(reason="threshold_reached")
        
        # Handle handover-related instructions
        instruction_lower = instruction.lower().strip()
        if instruction_lower == "handover" or instruction_lower == "trigger handover":
            self.trigger_handover(reason="user_request", manual=True)
            return True
        elif instruction_lower == "handover status":
            self._show_handover_status()
            return True
            
        return False
    
    def _show_handover_status(self):
        """Show current handover status"""
        if not self.enable_handover:
            print("❌ Handover system disabled")
            return
        
        session_duration = time.time() - self.session_start_time
        threshold_progress = (self.instructions_processed / self.handover_threshold) * 100
        
        print(f"\n📊 Loop.py Session Status")
        print(f"Instructions processed: {self.instructions_processed}/{self.handover_threshold} ({threshold_progress:.1f}%)")
        print(f"Session duration: {session_duration:.1f}s")
        print(f"Working directory: {os.getcwd()}")
        print(f"Handover enabled: ✅")
        
        if self._check_handover_conditions():
            print("🚨 Ready for handover!")
        else:
            print("✅ Session continuing normally")

def process_yolo_instruction(instruction: str) -> list[str]:
    try:
        # Define prompt
        prompt = dspy.Predict(
            "instruction -> steps",
            description="Expand vague development instruction into a list of actionable engineering steps."
        )

        # Run prediction
        result = prompt(instruction=instruction)

        # Extract and split
        raw_output = result.steps.strip()
        steps = [line.strip("-• ") for line in raw_output.splitlines() if line.strip()]

        # Logging
        os.makedirs("logs", exist_ok=True)
        with open("logs/yolo_expansions.log", "a") as log:
            log.write(f"\n=== YOLO EXPANSION ===\n")
            log.write(f"Timestamp: {datetime.now().isoformat()}\n")
            log.write(f"Original: {instruction}\n")
            log.write(f"Expanded:\n")
            for step in steps:
                log.write(f"- {step}\n")
            log.write(f"======================= \n")

        return steps or [instruction]

    except Exception as e:
        # Fallback on failure
        with open("logs/yolo_expansions.log", "a") as log:
            log.write(f"\n[ERROR] Failed to expand: {instruction} | {e}\n")
        return [instruction]

def process_plain_instruction(agent: CodeAgent, instruction: str):
    """
    Processes a plain-language instruction by mapping it to CodeAgent methods.
    This is a simplified parser for demonstration.
    """
    instruction_lower = instruction.lower().strip()

    if instruction_lower.startswith("read file"):
        path = instruction[len("read file"):].strip()
        if not path:
            logging.error("Error: 'path' argument missing for read file.")
            print("Error: 'path' argument missing for read file.")
            return
        result = agent.read_file(path)
        if "read_file_response" in result and "output" in result["read_file_response"]:
            print(f"Output:\n{result['read_file_response']['output']}")
        elif "error" in result:
            print(f"Error: {result['error']}")
        elif "dry_run_result" in result:
            print(f"Dry Run: {result['dry_run_result']}")
        else:
            print(f"Unexpected tool output: {result}")
    elif instruction_lower.startswith("edit file"):
        # Expects format: "edit file <path> with content <content>"
        parts = instruction.split(" with content ", 1)
        if len(parts) == 2:
            path = parts[0][len("edit file"):].strip()
            content = parts[1].strip()
            if not path:
                logging.error("Error: 'path' argument missing for edit file.")
                print("Error: 'path' argument missing for edit file.")
                return
            if content is None:
                logging.error("Error: 'content' argument missing for edit file.")
                print("Error: 'content' argument missing for edit file.")
                return
            result = agent.edit_file(path, content)
            if "write_file_response" in result and "output" in result["write_file_response"]:
                print(f"Success: {result['write_file_response']['output']}")
            elif "error" in result:
                print(f"Error: {result['error']}")
            elif "dry_run_result" in result:
                print(f"Dry Run: {result['dry_run_result']}")
            else:
                print(f"Unexpected tool output: {result}")
        else:
            logging.error("Error: For 'edit file', use format 'edit file <path> with content <content>'")
            print("Error: For 'edit file', use format 'edit file <path> with content <content>'")
    elif instruction_lower.startswith("run command"):
        cmd = instruction[len("run command"):].strip()
        if not cmd:
            logging.error("Error: 'cmd' argument missing for run command.")
            print("Error: 'cmd' argument missing for run command.")
            return
        result = agent.run_command(cmd)
        if "dry_run_result" in result:
            print(f"Dry Run: {result['dry_run_result']}")
        else:
            stdout = result.get("run_shell_command_response", {}).get("Stdout", "")
            stderr = result.get("run_shell_command_response", {}).get("Stderr", "")
            error = result.get("run_shell_command_response", {}).get("Error", "")
            exit_code = result.get("run_shell_command_response", {}).get("Exit Code", "")

            print(f"Stdout:\n{stdout}")
            if stderr:
                print(f"Stderr:\n{stderr}")
            if error and error != "(none)":
                print(f"Tool Error: {error}")
            if exit_code and exit_code != 0:
                print(f"Command exited with code: {exit_code}")
    elif instruction_lower.startswith("save snapshot"):
        message = instruction[len("save snapshot"):].strip()
        if not message:
            message = "auto: save snapshot"
        result = agent.save_snapshot(message)
        if "success" in result:
            print(f"Success: {result['success']}")
        elif "error" in result:
            print(f"Error: {result['error']}")
        elif "dry_run_result" in result:
            print(f"Dry Run: {result['dry_run_result']}")
        else:
            print(f"Unexpected tool output: {result}")
    elif instruction_lower.startswith("check file exists"):
        path = instruction[len("check file exists"):].strip()
        if not path:
            logging.error("Error: 'path' argument missing for check file exists.")
            print("Error: 'path' argument missing for check file exists.")
            return
        result = agent.check_file_exists(path)
        if "exists" in result:
            print(f"File exists: {result['exists']}")
        elif "dry_run_result" in result:
            print(f"Dry Run: {result['dry_run_result']}")
        else:
            print(f"Unexpected tool output: {result}")
    else:
        logging.error(f"Error: Unrecognized plain instruction: {instruction}")
        print(f"Error: Unrecognized plain instruction: {instruction}")

def run_task_queue(agent: CodeAgent, file_path: str):
    logging.info(f"Running task queue from {file_path}")
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    task = json.loads(line)
                    command = task.get("command")
                    args = task.get("args", {})
                    logging.info(f"Executing task: {command} with args {args}")

                    if command == "read_file":
                        agent.read_file(args.get("path"))
                    elif command == "edit_file":
                        agent.edit_file(args.get("path"), args.get("content"))
                    elif command == "run_command":
                        agent.run_command(args.get("cmd"))
                    elif command == "save_snapshot":
                        agent.save_snapshot(args.get("message", "auto: save snapshot"))
                    elif command == "check_file_exists":
                        agent.check_file_exists(args.get("path"))
                    else:
                        logging.error(f"Unknown command in task queue: {command}")
                        print(f"Error: Unknown command in task queue: {command}")
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in task queue file {file_path}: {line.strip()} - {e}")
                    print(f"Error: Invalid JSON in task queue file {file_path}: {line.strip()} - {e}")
                except Exception as e:
                    logging.error(f"Error executing task: {e}")
                    print(f"Error executing task: {e}")
    except FileNotFoundError:
        logging.error(f"Task queue file not found: {file_path}")
        print(f"Error: Task queue file not found: {file_path}")
    except Exception as e:
        logging.error(f"Error reading task queue file: {e}")
        print(f"Error: Error reading task queue file: {e}")

def main(default_api_instance=None):
    parser = argparse.ArgumentParser(description="Atlas Code Command Router")
    parser.add_argument("instruction", nargs='*', help="Plain-language instruction or JSON string")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without making actual changes")
    parser.add_argument("--log-file", help="Path to a file for logging output")
    parser.add_argument("--yolo", action="store_true", help="Enable idea expansion via dspy")
    parser.add_argument("--lazy", action="store_true", help="Alias for --yolo (and future relaxed behaviors)")
    parser.add_argument("--llm", help="Specify an LLM model to use (e.g., google/gemini-flash-1.5)")
    parser.add_argument("--prompt", help="Provide a prompt string to send to the LLM")
    parser.add_argument("--handover-threshold", type=int, default=50, help="Number of instructions before considering handover (default: 50)")
    parser.add_argument("--no-handover", action="store_true", help="Disable handover system")
    args = parser.parse_args()

    agent = CodeAgent(
        auto_commit=True, 
        dry_run=args.dry_run, 
        log_file=args.log_file, 
        default_api=default_api_instance,
        enable_handover=not args.no_handover
    )
    
    # Configure handover threshold
    if hasattr(agent, 'handover_threshold'):
        agent.handover_threshold = args.handover_threshold

    # Example of accessing the OpenRouter API key
    openrouter_key = get_openrouter_api_key()
    if openrouter_key:
        logging.info("OpenRouter API Key loaded successfully.")
        # In a real LLM-interfacing module, you would use this key to configure your LLM client.
        # For example: litellm.api_key = openrouter_key
    else:
        logging.warning("OpenRouter API Key not found. Please set OPENROUTER_API_KEY in your .env file.")

    instruction = " ".join(args.instruction)

    if args.llm and args.prompt:
        logging.info(f"Sending prompt to LLM ({args.llm}): {args.prompt}")
        raw_response, parsed_response = send_prompt_to_openrouter(args.prompt, args.llm)

        if raw_response and parsed_response:
            logging.info(f"LLM Raw Response: {json.dumps(raw_response, indent=2)}")
            logging.info(f"LLM Parsed Response: {parsed_response}")
            instruction = parsed_response
        else:
            logging.error("Failed to get a valid response from the LLM.")
            print("Error: Failed to get a valid response from the LLM.")
            return

    # If no instruction provided as argument, try reading from stdin (for piping)
    if not instruction and not sys.stdin.isatty():
        instruction = sys.stdin.read().strip()

    if not instruction:
        logging.info("No instruction provided. Use 'python loop.py <instruction>' or pipe input.")
        print("No instruction provided. Use 'python loop.py <instruction>' or pipe input.")
        return

    logging.info(f"Received instruction: {instruction}")

    # Check for handover-related instructions first
    if agent.process_instruction(instruction):
        return  # Handover instruction was processed
    
    if args.yolo or args.lazy:
        logging.info("YOLO mode activated. Expanding instruction...")
        expanded_instructions = process_yolo_instruction(instruction)
        for exp_instruction in expanded_instructions:
            logging.info(f"Executing expanded instruction: {exp_instruction}")
            
            # Check handover conditions for each expanded instruction
            if agent.process_instruction(exp_instruction):
                continue  # Skip to next instruction if handover was triggered
            
            try:
                # Attempt to parse as JSON first for LLM-generated instructions
                parsed_json = json.loads(exp_instruction)
                if isinstance(parsed_json, dict) and "command" in parsed_json:
                    command = parsed_json["command"]
                    args = parsed_json.get("args", {})
                    logging.info(f"Executing JSON command: {command} with args: {args}")

                    if command == "read_file":
                        path = args.get("path")
                        if not path:
                            logging.error("Error: 'path' argument missing for read_file.")
                            print("Error: 'path' argument missing for read_file.")
                            return
                        result = agent.read_file(path)
                        if "read_file_response" in result and "output" in result["read_file_response"]:
                            print(f"Output:\n{result['read_file_response']['output']}")
                        elif "error" in result:
                            print(f"Error: {result['error']}")
                        elif "dry_run_result" in result:
                            print(f"Dry Run: {result['dry_run_result']}")
                        else:
                            print(f"Unexpected tool output: {result}")
                    elif command == "edit_file":
                        path = args.get("path")
                        content = args.get("content")
                        if not path:
                            logging.error("Error: 'path' argument missing for edit_file.")
                            print("Error: 'path' argument missing for edit_file.")
                            return
                        if content is None:
                            logging.error("Error: 'content' argument missing for edit_file.")
                            print("Error: 'content' argument missing for edit_file.")
                            return
                        result = agent.edit_file(path, content)
                        if "write_file_response" in result and "output" in result["write_file_response"]:
                            print(f"Success: {result['write_file_response']['output']}")
                        elif "error" in result:
                            print(f"Error: {result['error']}")
                        elif "dry_run_result" in result:
                            print(f"Dry Run: {result['dry_run_result']}")
                        else:
                            print(f"Unexpected tool output: {result}")
                    elif command == "run_command":
                        cmd = args.get("cmd")
                        if not cmd:
                            logging.error("Error: 'cmd' argument missing for run_command.")
                            print("Error: 'cmd' argument missing for run_command.")
                            return
                        result = agent.run_command(cmd)
                        if "dry_run_result" in result:
                            print(f"Dry Run: {result['dry_run_result']}")
                        else:
                            stdout = result.get("run_shell_command_response", {}).get("Stdout", "")
                            stderr = result.get("run_shell_command_response", {}).get("Stderr", "")
                            error = result.get("run_shell_command_response", {}).get("Error", "")
                            exit_code = result.get("run_shell_command_response", {}).get("Exit Code", "")

                            print(f"Stdout:\n{stdout}")
                            if stderr:
                                print(f"Stderr:\n{stderr}")
                            if error and error != "(none)":
                                print(f"Tool Error: {error}")
                            if exit_code and exit_code != 0:
                                print(f"Command exited with code: {exit_code}")
                    elif command == "save_snapshot":
                        message = args.get("message", "auto: save snapshot")
                        result = agent.save_snapshot(message)
                        if "success" in result:
                            print(f"Success: {result['success']}")
                        elif "error" in result:
                            print(f"Error: {result['error']}")
                        elif "dry_run_result" in result:
                            print(f"Dry Run: {result['dry_run_result']}")
                        else:
                            print(f"Unexpected tool output: {result}")
                    elif command == "run_task_queue":
                        file_path = args.get("file")
                        if not file_path:
                            logging.error("Error: 'file' argument missing for run_task_queue.")
                            print("Error: 'file' argument missing for run_task_queue.")
                            return
                        run_task_queue(agent, file_path)
                    elif command == "check_file_exists":
                        path = args.get("path")
                        if not path:
                            logging.error("Error: 'path' argument missing for check_file_exists.")
                            print("Error: 'path' argument missing for check_file_exists.")
                            return
                        result = agent.check_file_exists(path)
                        if "exists" in result:
                            print(f"File exists: {result['exists']}")
                        elif "dry_run_result" in result:
                            print(f"Dry Run: {result['dry_run_result']}")
                        else:
                            print(f"Unexpected tool output: {result}")
                    else:
                        logging.error(f"Error: Unknown command in JSON: {command}")
                        print(f"Error: Unknown command in JSON: {command}")
                else:
                    # Fallback to simple keyword parsing for plain-language instructions
                    process_plain_instruction(agent, exp_instruction)

            except json.JSONDecodeError:
                # Not a JSON, process as plain language
                process_plain_instruction(agent, exp_instruction)
            except Exception as e:
                logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
                print(f"An unexpected error occurred: {e}")
    else:
        try:
            # Attempt to parse as JSON first for LLM-generated instructions
            parsed_json = json.loads(instruction)
            if isinstance(parsed_json, dict) and "command" in parsed_json:
                command = parsed_json["command"]
                args = parsed_json.get("args", {})
                logging.info(f"Executing JSON command: {command} with args: {args}")

                if command == "read_file":
                    path = args.get("path")
                    if not path:
                        logging.error("Error: 'path' argument missing for read_file.")
                        print("Error: 'path' argument missing for read_file.")
                        return
                    result = agent.read_file(path)
                    if "read_file_response" in result and "output" in result["read_file_response"]:
                        print(f"Output:\n{result['read_file_response']['output']}")
                    elif "error" in result:
                        print(f"Error: {result['error']}")
                    elif "dry_run_result" in result:
                        print(f"Dry Run: {result['dry_run_result']}")
                    else:
                        print(f"Unexpected tool output: {result}")
                elif command == "edit_file":
                    path = args.get("path")
                    content = args.get("content")
                    if not path:
                        logging.error("Error: 'path' argument missing for edit_file.")
                        print("Error: 'path' argument missing for edit_file.")
                        return
                    if content is None:
                        logging.error("Error: 'content' argument missing for edit_file.")
                        print("Error: 'content' argument missing for edit_file.")
                        return
                    result = agent.edit_file(path, content)
                    if "write_file_response" in result and "output" in result["write_file_response"]:
                        print(f"Success: {result['write_file_response']['output']}")
                    elif "error" in result:
                        print(f"Error: {result['error']}")
                    elif "dry_run_result" in result:
                        print(f"Dry Run: {result['dry_run_result']}")
                    else:
                        print(f"Unexpected tool output: {result}")
                elif command == "run_command":
                    cmd = args.get("cmd")
                    if not cmd:
                        logging.error("Error: 'cmd' argument missing for run_command.")
                        print("Error: 'cmd' argument missing for run_command.")
                        return
                    result = agent.run_command(cmd)
                    if "dry_run_result" in result:
                        print(f"Dry Run: {result['dry_run_result']}")
                    else:
                        stdout = result.get("run_shell_command_response", {}).get("Stdout", "")
                        stderr = result.get("run_shell_command_response", {}).get("Stderr", "")
                        error = result.get("run_shell_command_response", {}).get("Error", "")
                        exit_code = result.get("run_shell_command_response", {}).get("Exit Code", "")

                        print(f"Stdout:\n{stdout}")
                        if stderr:
                            print(f"Stderr:\n{stderr}")
                        if error and error != "(none)":
                            print(f"Tool Error: {error}")
                        if exit_code and exit_code != 0:
                            print(f"Command exited with code: {exit_code}")
                elif command == "save_snapshot":
                    message = args.get("message", "auto: save snapshot")
                    result = agent.save_snapshot(message)
                    if "success" in result:
                        print(f"Success: {result['success']}")
                    elif "error" in result:
                        print(f"Error: {result['error']}")
                    elif "dry_run_result" in result:
                        print(f"Dry Run: {result['dry_run_result']}")
                    else:
                        print(f"Unexpected tool output: {result}")
                elif command == "run_task_queue":
                    file_path = args.get("file")
                    if not file_path:
                        logging.error("Error: 'file' argument missing for run_task_queue.")
                        print("Error: 'file' argument missing for run_task_queue.")
                        return
                    run_task_queue(agent, file_path)
                elif command == "check_file_exists":
                    path = args.get("path")
                    if not path:
                        logging.error("Error: 'path' argument missing for check_file_exists.")
                        print("Error: 'path' argument missing for check_file_exists.")
                        return
                    result = agent.check_file_exists(path)
                    if "exists" in result:
                        print(f"File exists: {result['exists']}")
                    elif "dry_run_result" in result:
                        print(f"Dry Run: {result['dry_run_result']}")
                    else:
                        print(f"Unexpected tool output: {result}")
                else:
                    logging.error(f"Error: Unknown command in JSON: {command}")
                    print(f"Error: Unknown command in JSON: {command}")
            else:
                # Fallback to simple keyword parsing for plain-language instructions
                process_plain_instruction(agent, instruction)

        except json.JSONDecodeError:
            # Not a JSON, process as plain language
            process_plain_instruction(agent, instruction)
        except Exception as e:
            logging.critical(f"An unexpected error occurred: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}")
    
    # Final handover check at end of session
    if agent.enable_handover:
        agent.capture_handover_state(reason="session_end", trigger="automatic")

if __name__ == "__main__":
    # In the Gemini CLI environment, default_api is implicitly available.
    # When running as a standalone script, it needs to be passed.
    try:
        main(default_api=default_api)
    except NameError:
        print("Error: 'default_api' is not defined. This script is intended to be run within the Gemini CLI environment.")
        sys.exit(1)
