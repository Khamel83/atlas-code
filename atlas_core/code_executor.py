import subprocess
import sys

class CodeExecutor:
    def execute_python_code(self, code: str) -> dict:
        """Executes Python code and captures stdout/stderr."""
        try:
            process = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                check=True
            )
            return {"success": True, "stdout": process.stdout, "stderr": process.stderr}
        except subprocess.CalledProcessError as e:
            return {"success": False, "stdout": e.stdout, "stderr": e.stderr}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}
