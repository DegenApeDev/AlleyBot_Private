"""
A2A Server Mixin — HTTP+JSON binding for the Agent2Agent protocol (RC v1.0).

Implements the A2A specification:
  GET  /.well-known/agent-card.json  — Agent discovery (AgentCard)
  POST /message:send                 — Send a message / create a task
  POST /message:stream               — Send with SSE streaming
  GET  /tasks/{id}                   — Get task status
  GET  /tasks                        — List tasks
  POST /tasks/{id}:cancel            — Cancel a task

Spec: https://github.com/a2aproject/A2A/blob/main/docs/specification.md
"""
import os
import json
import uuid
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, Response


# ── A2A Task States (per spec §4.1.3) ──────────────────────────────
TASK_STATE_SUBMITTED = "TASK_STATE_SUBMITTED"
TASK_STATE_WORKING = "TASK_STATE_WORKING"
TASK_STATE_INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED"
TASK_STATE_COMPLETED = "TASK_STATE_COMPLETED"
TASK_STATE_CANCELED = "TASK_STATE_CANCELED"
TASK_STATE_FAILED = "TASK_STATE_FAILED"
TASK_STATE_REJECTED = "TASK_STATE_REJECTED"

TERMINAL_STATES = {TASK_STATE_COMPLETED, TASK_STATE_CANCELED, TASK_STATE_FAILED, TASK_STATE_REJECTED}


def _make_text_part(text: str) -> Dict:
    """Create a text Part per spec §4.1.6."""
    return {"text": text}


def _make_message(role: str, parts: List[Dict], message_id: str = None) -> Dict:
    """Create a Message per spec §4.1.4."""
    return {
        "messageId": message_id or str(uuid.uuid4()),
        "role": role,
        "parts": parts,
    }


def _make_task(task_id: str, context_id: str, state: str,
               messages: List[Dict] = None, artifacts: List[Dict] = None) -> Dict:
    """Create a Task per spec §4.1.1."""
    task = {
        "id": task_id,
        "contextId": context_id,
        "status": {"state": state, "timestamp": datetime.utcnow().isoformat() + "Z"},
    }
    if messages:
        task["history"] = messages
    if artifacts:
        task["artifacts"] = artifacts
    return task


def _make_artifact(parts: List[Dict], name: str = None, index: int = 0) -> Dict:
    """Create an Artifact per spec §4.1.7."""
    art = {"artifactId": str(uuid.uuid4()), "parts": parts, "index": index}
    if name:
        art["name"] = name
    return art


def _a2a_error(code: str, message: str, status_code: int = 400) -> tuple:
    """Return a spec-compliant error response."""
    return jsonify({"error": {"code": code, "message": message}}), status_code


class A2AServerMixin:
    """HTTP+JSON server implementing A2A protocol RC v1.0."""

    def _init_server(self):
        """Initialize the A2A HTTP server."""
        self._a2a_port = self.config.get('port', 7002)
        self._a2a_host = self.config.get('host', '0.0.0.0')
        self._a2a_base_url = self.config.get('base_url', 'https://tasks.apeshit.fun')
        self._a2a_start_time = time.time()
        self._a2a_app = None
        self._server_thread = None

        # Task store keyed by task_id
        self._tasks: Dict[str, Dict] = {}
        self._tasks_max = 1000

    def _setup_a2a_server(self):
        """Create and configure the Flask A2A server."""
        self._a2a_app = Flask('alleybot_a2a')

        # ── Root / Landing ────────────────────────────────────────────

        @self._a2a_app.route('/', methods=['GET'])
        def root():
            base = self._a2a_base_url.rstrip('/')
            return jsonify({
                "name": "AlleyBot",
                "protocol": "A2A",
                "version": "1.0",
                "description": "AlleyBot Agent-to-Agent protocol server",
                "endpoints": {
                    "agentCard": f"{base}/.well-known/agent-card.json",
                    "messageSend": f"{base}/message:send",
                    "messageStream": f"{base}/message:stream",
                    "tasks": f"{base}/tasks",
                    "health": f"{base}/health",
                },
            }), 200

        # ── Agent Discovery (§8) ────────────────────────────────────

        @self._a2a_app.route('/.well-known/agent-card.json', methods=['GET'])
        def well_known_agent_card():
            return self._handle_agent_card()

        @self._a2a_app.route('/.well-known/agent.json', methods=['GET'])
        def well_known_agent_json():
            """Serve static ERC-8004 agent card for 8004scan compatibility."""
            try:
                import os
                static_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'static', '.well-known', 'agent-card.json'
                )
                with open(static_path, 'r') as f:
                    card_content = f.read()
                return Response(card_content, mimetype='application/json'), 200
            except Exception as e:
                return _a2a_error("INTERNAL_ERROR", f"Failed to load agent.json: {e}", 500)

        @self._a2a_app.route('/extendedAgentCard', methods=['GET'])
        def extended_agent_card():
            return self._handle_agent_card()

        # ── Message Operations (§11.3.1) ────────────────────────────

        @self._a2a_app.route('/message:send', methods=['POST'])
        def message_send():
            return self._handle_message_send()

        @self._a2a_app.route('/message:stream', methods=['POST'])
        def message_stream():
            return self._handle_message_stream()

        # ── Task Operations (§11.3.2) ───────────────────────────────

        @self._a2a_app.route('/tasks/<task_id>', methods=['GET'])
        def get_task(task_id):
            return self._handle_get_task(task_id)

        @self._a2a_app.route('/tasks', methods=['GET'])
        def list_tasks():
            return self._handle_list_tasks()

        @self._a2a_app.route('/tasks/<task_id>:cancel', methods=['POST'])
        def cancel_task(task_id):
            return self._handle_cancel_task(task_id)

        # ── Health (non-spec, useful for monitoring) ────────────────

        @self._a2a_app.route('/health', methods=['GET'])
        def health():
            return self._handle_health()

        # ── CORS headers for browser-based agents ───────────────────

        # Configure allowed origins from environment or use secure defaults
        allowed_origins_env = os.getenv('A2A_ALLOWED_ORIGINS', '')
        self._a2a_allowed_origins = [o.strip() for o in allowed_origins_env.split(',') if o.strip()] or [
            'https://tasks.apeshit.fun',
            'https://apeshit.fun',
        ]

        @self._a2a_app.after_request
        def add_cors(response):
            origin = request.headers.get('Origin')
            
            # Only allow configured origins
            if origin in self._a2a_allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Vary'] = 'Origin'  # Important for caching
            
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, A2A-Version, A2A-Extensions'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            
            return response

        print(f"🌐 A2A server configured on port {self._a2a_port} (A2A RC v1.0)")

    def start_a2a_server(self):
        """Start the A2A server in a background thread."""
        if not self._a2a_app:
            self._setup_a2a_server()

        def _run():
            self._a2a_app.run(
                host=self._a2a_host,
                port=self._a2a_port,
                debug=False,
                use_reloader=False,
            )

        self._server_thread = threading.Thread(target=_run, daemon=True, name='a2a-server')
        self._server_thread.start()
        print(f"🚀 A2A server running at http://{self._a2a_host}:{self._a2a_port}")

    # ── Agent Card (§8.5) ───────────────────────────────────────────

    def _handle_agent_card(self) -> Response:
        """Return A2A-spec AgentCard at /.well-known/agent-card.json."""
        base = self._a2a_base_url.rstrip('/')

        # Build skills from task registry with full schema + pricing
        a2a_skills = []
        available = self.list_available_tasks()
        for task_name, info in available.items():
            from plugins.a2a.a2a_tasks import TASK_REGISTRY
            task_def = TASK_REGISTRY.get(task_name, {})
            skill = {
                "id": task_name,
                "name": task_name.replace('.', ' ').replace('_', ' ').title(),
                "description": info['description'],
                "tags": task_name.split('.'),
            }
            # Add input schema if defined
            schema = task_def.get('schema')
            if schema:
                skill["inputSchema"] = {
                    "type": "object",
                    **schema,
                }
            # Add pricing for paid tasks
            if info.get('price_usdc'):
                skill["tags"].append("paid")
                skill["pricing"] = {
                    "amount": info['price_usdc'],
                    "currency": "USDC",
                    "network": "base",
                    "chainId": 8453,
                    "paymentAddress": "0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5",
                }
            else:
                skill["tags"].append("free")
            a2a_skills.append(skill)

        card = {
            "name": "AlleyBot",
            "description": (
                "Autonomous AI agent with capabilities across social platforms "
                "(Moltx, MoltBook, MoltChan, MoltRoad), blockchain analytics (Base network), "
                "AI content generation, and self-improvement. ERC-8004 Agent #22899."
            ),
            "iconUrl": "https://blob.8004scan.app/3d2fb26e34f0c9a4c083adce2449905ff37a74c5fd3132114bddb69d69468ac7.jpg",
            "version": "1.0.0",
            "provider": {
                "organization": "AlleyBot",
                "url": base,
            },
            "documentationUrl": f"https://www.8004scan.io/agents/ethereum/22899",
            "supportedInterfaces": [
                {
                    "url": base,
                    "protocolBinding": "HTTP+JSON",
                    "protocolVersion": "1.0",
                },
            ],
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": True,
                "extendedAgentCard": False,
            },
            "defaultInputModes": ["text/plain", "application/json"],
            "defaultOutputModes": ["text/plain", "application/json"],
            "skills": a2a_skills,
            "registrations": [
                {
                    "agentId": 22899,
                    "agentRegistry": "eip155:1:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
                }
            ],
        }

        return jsonify(card), 200, {'Content-Type': 'application/json'}

    # ── POST /message:send (§11.3.1) ────────────────────────────────

    def _handle_message_send(self) -> Response:
        """Handle POST /message:send — core A2A message operation.

        Spec request format:
        {
            "message": {
                "messageId": "uuid",
                "role": "ROLE_USER",
                "parts": [{"text": "..."}]
            },
            "configuration": {
                "acceptedOutputModes": ["text/plain"]
            },
            "metadata": {}
        }
        """
        self._total_requests += 1

        try:
            body = request.get_json(force=True)
        except Exception:
            self._total_rejected += 1
            return _a2a_error("INVALID_REQUEST", "Invalid JSON body", 400)

        msg = body.get('message')
        if not msg or not isinstance(msg, dict):
            self._total_rejected += 1
            return _a2a_error("INVALID_REQUEST", "Missing 'message' field", 400)

        parts = msg.get('parts', [])
        if not parts:
            self._total_rejected += 1
            return _a2a_error("INVALID_REQUEST", "Message must contain at least one part", 400)

        # Extract text from parts
        user_text = ""
        for part in parts:
            if 'text' in part:
                user_text += part['text'] + " "
        user_text = user_text.strip()

        if not user_text:
            self._total_rejected += 1
            return _a2a_error("CONTENT_TYPE_NOT_SUPPORTED", "Only text parts are supported", 400)

        # Extract agent identity from headers or metadata
        agent_id = request.headers.get('Authorization', 'anonymous')
        metadata = body.get('metadata', {})

        # ── Security Pipeline ───────────────────────────────────────

        id_ok, id_reason = self.verify_agent_identity(agent_id, metadata)
        if not id_ok:
            self._total_rejected += 1
            return _a2a_error("UNAUTHORIZED", id_reason, 403)

        rate_ok, rate_reason = self.check_rate_limit(agent_id)
        if not rate_ok:
            self._total_rejected += 1
            return _a2a_error("RATE_LIMITED", rate_reason, 429)

        # ── Route message to task ───────────────────────────────────

        task_type, task_params = self._route_message(user_text, body)

        # Sanitize
        san_ok, san_reason, sanitized_params = self.sanitize_task_request(task_type, task_params)
        if not san_ok:
            self._total_rejected += 1
            return _a2a_error("INVALID_REQUEST", san_reason, 400)

        # Payment check for paid tasks
        payment = metadata.get('payment')
        pay_ok, pay_reason = self.check_payment(agent_id, task_type, payment)
        if not pay_ok:
            self._total_rejected += 1
            return _a2a_error("PAYMENT_REQUIRED", pay_reason, 402)

        # ── Execute ─────────────────────────────────────────────────

        task_id = str(uuid.uuid4())
        context_id = body.get('contextId') or msg.get('contextId') or str(uuid.uuid4())

        # Store initial task state
        user_msg = _make_message("ROLE_USER", parts, msg.get('messageId'))
        task_obj = _make_task(task_id, context_id, TASK_STATE_WORKING, messages=[user_msg])
        self._store_task(task_id, task_obj)

        # Execute the task
        result = self.execute_task(task_type, sanitized_params, agent_id)

        # Build response (filter through security to prevent secret leaks)
        try:
            from security_filter import security_filter as _sf
            _filter = _sf.filter_message
        except ImportError:
            _filter = lambda t: (t, False)

        if result.success:
            response_text = json.dumps(result.data) if isinstance(result.data, dict) else str(result.data)
            response_text, was_filtered = _filter(response_text)
            if was_filtered:
                print(f"⚠️  SECURITY: Filtered sensitive data from A2A response for task {task_type}")
            agent_msg = _make_message("ROLE_AGENT", [_make_text_part(response_text)])
            artifact = _make_artifact([_make_text_part(response_text)], name=task_type)
            task_obj = _make_task(task_id, context_id, TASK_STATE_COMPLETED,
                                 messages=[user_msg, agent_msg], artifacts=[artifact])
        else:
            error_text, _ = _filter(f"Error: {result.error}")
            agent_msg = _make_message("ROLE_AGENT", [_make_text_part(error_text)])
            task_obj = _make_task(task_id, context_id, TASK_STATE_FAILED,
                                 messages=[user_msg, agent_msg])
            task_obj["status"]["message"] = _make_message(
                "ROLE_AGENT", [_make_text_part(error_text)])

        self._store_task(task_id, task_obj)

        # Audit
        self._audit("task_completed" if result.success else "task_failed",
                     agent_id, f"{task_type} -> {'OK' if result.success else result.error}")

        return jsonify({"task": task_obj}), 200

    # ── POST /message:stream (§11.3.1, §11.7) ──────────────────────

    def _handle_message_stream(self) -> Response:
        """Handle POST /message:stream — SSE streaming response."""
        self._total_requests += 1

        try:
            body = request.get_json(force=True)
        except Exception:
            self._total_rejected += 1
            return _a2a_error("INVALID_REQUEST", "Invalid JSON body", 400)

        msg = body.get('message')
        if not msg or not isinstance(msg, dict):
            self._total_rejected += 1
            return _a2a_error("INVALID_REQUEST", "Missing 'message' field", 400)

        parts = msg.get('parts', [])
        user_text = " ".join(p.get('text', '') for p in parts).strip()
        if not user_text:
            return _a2a_error("CONTENT_TYPE_NOT_SUPPORTED", "Only text parts supported", 400)

        agent_id = request.headers.get('Authorization', 'anonymous')
        metadata = body.get('metadata', {})

        # Security checks
        id_ok, id_reason = self.verify_agent_identity(agent_id, metadata)
        if not id_ok:
            return _a2a_error("UNAUTHORIZED", id_reason, 403)

        rate_ok, rate_reason = self.check_rate_limit(agent_id)
        if not rate_ok:
            return _a2a_error("RATE_LIMITED", rate_reason, 429)

        task_type, task_params = self._route_message(user_text, body)
        task_id = str(uuid.uuid4())
        context_id = body.get('contextId') or str(uuid.uuid4())
        user_msg = _make_message("ROLE_USER", parts, msg.get('messageId'))

        def generate():
            # Event 1: Task submitted
            task_obj = _make_task(task_id, context_id, TASK_STATE_SUBMITTED, messages=[user_msg])
            yield f"data: {json.dumps({'task': task_obj})}\n\n"

            # Event 2: Working
            status_event = {
                "statusUpdate": {
                    "taskId": task_id,
                    "contextId": context_id,
                    "status": {"state": TASK_STATE_WORKING,
                               "timestamp": datetime.utcnow().isoformat() + "Z"},
                }
            }
            yield f"data: {json.dumps(status_event)}\n\n"

            # Execute
            result = self.execute_task(task_type, task_params, agent_id)

            # Security filter
            try:
                from security_filter import security_filter as _sf
                _sec_filter = _sf.filter_message
            except ImportError:
                _sec_filter = lambda t: (t, False)

            if result.success:
                response_text = json.dumps(result.data) if isinstance(result.data, dict) else str(result.data)
                response_text, _was_filtered = _sec_filter(response_text)
                if _was_filtered:
                    print(f"⚠️  SECURITY: Filtered sensitive data from A2A stream for task {task_type}")
                # Event 3: Artifact
                artifact = _make_artifact([_make_text_part(response_text)], name=task_type)
                artifact_event = {
                    "artifactUpdate": {
                        "taskId": task_id,
                        "contextId": context_id,
                        "artifact": artifact,
                    }
                }
                yield f"data: {json.dumps(artifact_event)}\n\n"

                # Event 4: Completed
                final_status = {
                    "statusUpdate": {
                        "taskId": task_id,
                        "contextId": context_id,
                        "status": {"state": TASK_STATE_COMPLETED,
                                   "timestamp": datetime.utcnow().isoformat() + "Z"},
                    }
                }
                yield f"data: {json.dumps(final_status)}\n\n"
            else:
                # Event 3: Failed
                error_text, _ = _sec_filter(result.error or "Task failed")
                final_status = {
                    "statusUpdate": {
                        "taskId": task_id,
                        "contextId": context_id,
                        "status": {
                            "state": TASK_STATE_FAILED,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "message": _make_message("ROLE_AGENT",
                                                     [_make_text_part(error_text)]),
                        },
                    }
                }
                yield f"data: {json.dumps(final_status)}\n\n"

            self._audit("task_completed" if result.success else "task_failed",
                         agent_id, f"{task_type} (stream)")

        return Response(generate(), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    # ── GET /tasks/{id} (§11.3.2) ───────────────────────────────────

    def _handle_get_task(self, task_id: str) -> Response:
        """Retrieve a task by ID."""
        task = self._tasks.get(task_id)
        if not task:
            return _a2a_error("TASK_NOT_FOUND", f"Task {task_id} not found", 404)
        return jsonify(task), 200

    # ── GET /tasks (§11.3.2) ────────────────────────────────────────

    def _handle_list_tasks(self) -> Response:
        """List recent tasks (limited view)."""
        # Only return task IDs and states, not full history
        tasks = []
        for tid, task in list(self._tasks.items())[-50:]:
            tasks.append({
                "id": task.get("id", tid),
                "contextId": task.get("contextId", ""),
                "status": task.get("status", {}),
            })
        return jsonify({"tasks": tasks}), 200

    # ── POST /tasks/{id}:cancel (§11.3.2) ───────────────────────────

    def _handle_cancel_task(self, task_id: str) -> Response:
        """Cancel a task."""
        task = self._tasks.get(task_id)
        if not task:
            return _a2a_error("TASK_NOT_FOUND", f"Task {task_id} not found", 404)

        current_state = task.get("status", {}).get("state", "")
        if current_state in TERMINAL_STATES:
            return _a2a_error("UNSUPPORTED_OPERATION",
                              f"Cannot cancel task in state {current_state}", 400)

        task["status"] = {
            "state": TASK_STATE_CANCELED,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._tasks[task_id] = task
        return jsonify({"task": task}), 200

    # ── Health ──────────────────────────────────────────────────────

    def _handle_health(self) -> Response:
        """Health check endpoint."""
        uptime_s = time.time() - self._a2a_start_time
        return jsonify({
            "status": "healthy",
            "agent": "AlleyBot",
            "agentId": 22899,
            "protocolVersion": "1.0",
            "uptime_seconds": round(uptime_s),
            "tasks_stored": len(self._tasks),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }), 200

    # ── Message Routing ─────────────────────────────────────────────

    # Allowed task types for security - only these tasks can be executed
    ALLOWED_TASK_TYPES = {
        'agent.health', 'agent.capabilities', 'agent.stats', 'agent.skills',
        'content.generate_post', 'content.analyze_trend',
        'blockchain.check_balance', 'blockchain.lookup_tx',
        'media.generate_image'
    }

    def _validate_task_type(self, task_type: str) -> bool:
        """Validate that a task type is in the allowlist."""
        return task_type in self.ALLOWED_TASK_TYPES

    def _route_message(self, text: str, body: Dict) -> tuple:
        """Route a natural language message to the appropriate task handler.

        Returns (task_type, params) tuple.
        """
        text_lower = text.lower()

        # Direct task invocation via metadata
        if body.get('metadata', {}).get('taskType'):
            task_type = body['metadata']['taskType']
            # SECURITY: Validate task type is in allowlist
            if not self._validate_task_type(task_type):
                raise ValueError(f"Task type '{task_type}' is not in allowed task types")
            params = body.get('metadata', {}).get('taskParams', {})
            return task_type, params

        # Simple keyword routing - all results are validated against allowlist
        if any(w in text_lower for w in ['health', 'status', 'ping', 'alive']):
            return 'agent.health', {}
        elif any(w in text_lower for w in ['capabilities', 'what can you do', 'help']):
            return 'agent.capabilities', {}
        elif any(w in text_lower for w in ['skills', 'oasf']):
            return 'agent.skills', {}
        elif any(w in text_lower for w in ['stats', 'statistics', 'metrics']):
            return 'agent.stats', {}
        elif any(w in text_lower for w in ['balance', 'wallet']):
            # Try to extract address
            import re
            addr_match = re.search(r'0x[a-fA-F0-9]{40}', text)
            address = addr_match.group(0) if addr_match else ''
            return 'blockchain.check_balance', {'address': address}
        elif any(w in text_lower for w in ['transaction', 'tx', 'lookup']):
            import re
            tx_match = re.search(r'0x[a-fA-F0-9]{64}', text)
            tx_hash = tx_match.group(0) if tx_match else ''
            return 'blockchain.lookup_tx', {'tx_hash': tx_hash}
        elif any(w in text_lower for w in ['trending', 'trend', 'popular']):
            return 'content.analyze_trend', {'platform': 'moltx'}
        elif any(w in text_lower for w in ['image', 'picture', 'photo', 'generate image', 'create image']):
            return 'media.generate_image', {'prompt': text}
        elif any(w in text_lower for w in ['price alert', 'alert', 'threshold', 'monitor price']):
            # Try to extract token and price
            import re
            token_match = re.search(r'\b(ETH|BTC|ALLEY|USDC|WETH|DEGEN|BASE)\b', text_upper)
            token = token_match.group(1) if token_match else 'ETH'
            price_match = re.search(r'\$?(\d+(?:\.\d+)?)', text)
            threshold = float(price_match.group(1)) if price_match else 0
            return 'crypto.price_alert', {'token': token, 'threshold': threshold}
        elif any(w in text_lower for w in ['shill', 'shill post', 'hype', 'promote', 'degen post']):
            return 'social.shill_post', {'project': text}
        elif any(w in text_lower for w in ['apy', 'yield', 'farm', 'defi optimizer', 'best yield']):
            return 'defi.apy_optimizer', {'protocols': ['aave', 'yearn', 'curve']}
        elif any(w in text_lower for w in ['contract scan', 'slither', 'audit contract', 'security check contract']):
            import re
            addr_match = re.search(r'0x[a-fA-F0-9]{40}', text)
            address = addr_match.group(0) if addr_match else ''
            return 'contract.slither_scan', {'address': address}
        elif any(w in text_lower for w in ['find agent', 'recommend agent', 'best agent', 'skill recommend', 'agent matcher']):
            return 'a2a.skill_recommend', {'task': text}
        elif any(w in text_lower for w in ['audit', 'wallet audit', 'security check', 'scan wallet']):
            import re
            addr_match = re.search(r'0x[a-fA-F0-9]{40}', text)
            address = addr_match.group(0) if addr_match else ''
            return 'wallet.audit', {'address': address}
        elif any(w in text_lower for w in ['generate', 'write', 'post', 'create']):
            return 'content.generate_post', {'topic': text}
        else:
            # Default: treat as content generation request
            return 'content.generate_post', {'topic': text}

    # ── Internal Helpers ────────────────────────────────────────────

    def _store_task(self, task_id: str, task: Dict):
        """Store a task for later retrieval."""
        self._tasks[task_id] = task
        if len(self._tasks) > self._tasks_max:
            oldest = list(self._tasks.keys())[:100]
            for k in oldest:
                del self._tasks[k]

    def get_a2a_endpoints(self) -> Dict[str, str]:
        """Return the A2A endpoint URLs."""
        base = self._a2a_base_url.rstrip('/')
        return {
            'agent_card': f"{base}/.well-known/agent-card.json",
            'message_send': f"{base}/message:send",
            'message_stream': f"{base}/message:stream",
            'get_task': f"{base}/tasks/{{task_id}}",
            'list_tasks': f"{base}/tasks",
            'cancel_task': f"{base}/tasks/{{task_id}}:cancel",
            'health': f"{base}/health",
        }
