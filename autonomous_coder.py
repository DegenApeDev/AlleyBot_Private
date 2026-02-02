#!/usr/bin/env python3
"""
AlleyBot Autonomous Coding Engine
Safe, sandboxed code generation with human approval workflow
"""
import os
import json
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib

class AutonomousCoder:
    """Safe autonomous coding with human oversight"""
    
    def __init__(self, workspace_dir: str = "alleybot_workspace"):
        self.workspace_dir = workspace_dir
        self.sandbox_dir = os.path.join(workspace_dir, "sandbox")
        self.drafts_dir = os.path.join(workspace_dir, "drafts")
        self.approved_dir = os.path.join(workspace_dir, "approved")
        self.deployed_dir = os.path.join(workspace_dir, "deployed")
        self.logs_dir = os.path.join(workspace_dir, "logs")
        self.backups_dir = os.path.join(workspace_dir, "backups")
        
        self._setup_workspace()
    
    def _setup_workspace(self):
        """Create secure workspace structure"""
        for directory in [self.workspace_dir, self.sandbox_dir, self.drafts_dir, 
                          self.approved_dir, self.deployed_dir, self.logs_dir, self.backups_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Create .gitkeep files
        for directory in [self.sandbox_dir, self.drafts_dir, self.approved_dir, 
                          self.deployed_dir, self.logs_dir]:
            open(os.path.join(directory, ".gitkeep"), 'w').close()
    
    def generate_code(self, task: str, context: Dict = None) -> Dict:
        """Generate code for a specific task"""
        timestamp = datetime.now().isoformat()
        draft_id = hashlib.md5(f"{task}{timestamp}".encode()).hexdigest()[:8]
        
        draft = {
            "draft_id": draft_id,
            "task": task,
            "context": context or {},
            "timestamp": timestamp,
            "status": "generating",
            "files": [],
            "tests": [],
            "dependencies": [],
            "security_scan": None,
            "human_review": None
        }
        
        try:
            # Use DeepSeek to generate code
            from deepseek_ai import DeepSeekAI
            ai = DeepSeekAI()
            
            prompt = f"""
            Task: {task}
            Context: {json.dumps(context, indent=2)}
            
            Generate complete, production-ready Python code that:
            1. Solves the task efficiently
            2. Follows Python best practices
            3. Includes error handling
            4. Has comprehensive tests
            5. Documents security considerations
            6. Is self-contained and modular
            
            Return JSON with:
            - files: list of {filename, content, description}
            - dependencies: list of required packages
            - tests: list of test functions
            - security_notes: potential security considerations
            """
            
            response = ai.generate(prompt)
            generated = json.loads(response)
            
            draft["files"] = generated.get("files", [])
            draft["dependencies"] = generated.get("dependencies", [])
            draft["tests"] = generated.get("tests", [])
            draft["security_notes"] = generated.get("security_notes", [])
            draft["status"] = "draft_ready"
            
            # Save draft
            self._save_draft(draft)
            
            # Log generation
            self._log_activity("code_generated", {
                "draft_id": draft_id,
                "task": task,
                "files_count": len(draft["files"]),
                "success": True
            })
            
            return draft
            
        except Exception as e:
            draft["status"] = "error"
            draft["error"] = str(e)
            self._save_draft(draft)
            
            self._log_activity("code_generation_failed", {
                "draft_id": draft_id,
                "task": task,
                "error": str(e),
                "success": False
            })
            
            return draft
    
    def _save_draft(self, draft: Dict):
        """Save draft to drafts directory"""
        draft_file = os.path.join(self.drafts_dir, f"{draft['draft_id']}.json")
        with open(draft_file, 'w') as f:
            json.dump(draft, f, indent=2)
    
    def test_code(self, draft_id: str) -> Dict:
        """Test code in sandbox environment"""
        draft_file = os.path.join(self.drafts_dir, f"{draft_id}.json")
        
        if not os.path.exists(draft_file):
            return {"error": "Draft not found"}
        
        with open(draft_file, 'r') as f:
            draft = json.load(f)
        
        # Create temporary sandbox
        with tempfile.TemporaryDirectory() as temp_sandbox:
            results = {
                "draft_id": draft_id,
                "timestamp": datetime.now().isoformat(),
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "security_issues": [],
                "performance_metrics": {},
                "status": "testing"
            }
            
            try:
                # Write files to sandbox
                for file_info in draft["files"]:
                    file_path = os.path.join(temp_sandbox, file_info["filename"])
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(file_info["content"])
                
                # Install dependencies
                if draft["dependencies"]:
                    subprocess.run([
                        "pip", "install", "-q"
                    ] + draft["dependencies"], 
                    check=True, capture_output=True, cwd=temp_sandbox)
                
                # Run tests
                for test in draft["tests"]:
                    results["tests_run"] += 1
                    try:
                        # Execute test in sandbox
                        result = subprocess.run([
                            "python", "-c", test
                        ], capture_output=True, text=True, cwd=temp_sandbox, timeout=30)
                        
                        if result.returncode == 0:
                            results["tests_passed"] += 1
                        else:
                            results["tests_failed"] += 1
                            results["errors"] = result.stderr
                    except subprocess.TimeoutExpired:
                        results["tests_failed"] += 1
                        results["errors"] = "Test timeout"
                
                # Security scan
                security_results = self._security_scan(temp_sandbox)
                results["security_issues"] = security_results
                
                # Update status
                results["status"] = "tested"
                if results["tests_failed"] == 0 and len(results["security_issues"]) == 0:
                    results["status"] = "ready_for_review"
                
                # Update draft
                draft["test_results"] = results
                draft["status"] = results["status"]
                self._save_draft(draft)
                
                # Log testing
                self._log_activity("code_tested", {
                    "draft_id": draft_id,
                    "tests_run": results["tests_run"],
                    "tests_passed": results["tests_passed"],
                    "security_issues": len(results["security_issues"]),
                    "status": results["status"]
                })
                
                return results
                
            except Exception as e:
                results["status"] = "test_error"
                results["error"] = str(e)
                
                self._log_activity("code_test_failed", {
                    "draft_id": draft_id,
                    "error": str(e),
                    "success": False
                })
                
                return results
    
    def _security_scan(self, directory: str) -> List[str]:
        """Basic security scanning"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Check for security issues
                        if "eval(" in content:
                            issues.append(f"Unsafe eval() in {file}")
                        if "exec(" in content:
                            issues.append(f"Unsafe exec() in {file}")
                        if "subprocess.call" in content and "shell=True" in content:
                            issues.append(f"Shell injection risk in {file}")
                        if "os.system(" in content:
                            issues.append(f"Unsafe os.system() in {file}")
                        
                    except Exception:
                        continue
        
        return issues
    
    def get_pending_drafts(self) -> List[Dict]:
        """Get all drafts pending human review"""
        drafts = []
        
        for file in os.listdir(self.drafts_dir):
            if file.endswith('.json'):
                try:
                    with open(os.path.join(self.drafts_dir, file), 'r') as f:
                        draft = json.load(f)
                    
                    if draft["status"] in ["draft_ready", "ready_for_review", "tested"]:
                        drafts.append(draft)
                except Exception:
                    continue
        
        return sorted(drafts, key=lambda x: x["timestamp"], reverse=True)
    
    def approve_draft(self, draft_id: str, human_review: Dict) -> Dict:
        """Human approval of draft"""
        draft_file = os.path.join(self.drafts_dir, f"{draft_id}.json")
        
        if not os.path.exists(draft_file):
            return {"error": "Draft not found"}
        
        with open(draft_file, 'r') as f:
            draft = json.load(f)
        
        # Add human review
        draft["human_review"] = {
            "approved": True,
            "reviewer": human_review.get("reviewer", "human"),
            "timestamp": datetime.now().isoformat(),
            "comments": human_review.get("comments", ""),
            "modifications": human_review.get("modifications", [])
        }
        
        # Move to approved
        approved_file = os.path.join(self.approved_dir, f"{draft_id}.json")
        shutil.move(draft_file, approved_file)
        
        # Log approval
        self._log_activity("code_approved", {
            "draft_id": draft_id,
            "reviewer": human_review.get("reviewer"),
            "files_count": len(draft["files"])
        })
        
        return {"status": "approved", "draft_id": draft_id}
    
    def deploy_code(self, draft_id: str) -> Dict:
        """Deploy approved code"""
        approved_file = os.path.join(self.approved_dir, f"{draft_id}.json")
        
        if not os.path.exists(approved_file):
            return {"error": "Approved draft not found"}
        
        with open(approved_file, 'r') as f:
            draft = json.load(f)
        
        try:
            # Backup current deployed code
            self._backup_deployed()
            
            # Deploy new code
            deployed_files = []
            for file_info in draft["files"]:
                dest_path = os.path.join(self.deployed_dir, file_info["filename"])
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                with open(dest_path, 'w') as f:
                    f.write(file_info["content"])
                
                deployed_files.append(file_info["filename"])
            
            # Update draft status
            draft["deployment"] = {
                "deployed": True,
                "timestamp": datetime.now().isoformat(),
                "files_deployed": deployed_files
            }
            
            # Move to deployed
            deployed_file = os.path.join(self.deployed_dir, f"{draft_id}.json")
            shutil.move(approved_file, deployed_file)
            
            # Log deployment
            self._log_activity("code_deployed", {
                "draft_id": draft_id,
                "files_deployed": len(deployed_files),
                "success": True
            })
            
            return {
                "status": "deployed",
                "draft_id": draft_id,
                "files_deployed": deployed_files
            }
            
        except Exception as e:
            self._log_activity("code_deployment_failed", {
                "draft_id": draft_id,
                "error": str(e),
                "success": False
            })
            
            return {"error": str(e)}
    
    def _backup_deployed(self):
        """Create backup of current deployed code"""
        timestamp = datetime.now().isoformat().replace(":", "-")
        backup_dir = os.path.join(self.backups_dir, f"backup_{timestamp}")
        
        if os.path.exists(self.deployed_dir):
            shutil.copytree(self.deployed_dir, backup_dir, dirs_exist_ok=True)
    
    def _log_activity(self, activity: str, details: Dict):
        """Log all coding activities"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "details": details
        }
        
        log_file = os.path.join(self.logs_dir, f"coding_log_{datetime.now().strftime('%Y-%m-%d')}.json")
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
    
    def get_activity_logs(self, date: str = None) -> List[Dict]:
        """Get activity logs"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        log_file = os.path.join(self.logs_dir, f"coding_log_{date}.json")
        logs = []
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            logs.append(json.loads(line))
            except Exception:
                pass
        
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)
