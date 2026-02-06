"""
A2A Server Mixin — HTTP server implementing Google's Agent-to-Agent protocol.

Exposes endpoints:
  POST /a2a/tasks/send        — Submit a task to AlleyBot
  GET  /a2a/tasks/{id}        — Check task status
  GET  /a2a/agent-card        — Agent card (A2A discovery)
  GET  /a2a/health             — Health check
  GET  /a2a/tasks/available    — List available tasks

All requests pass through the full security pipeline before execution.
"""
import json
import uuid
import time
import threading
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, Response


class A2AServerMixin:
    """HTTP server for A2A protocol communication."""

    def _init_server(self):
        """Initialize the A2A HTTP server."""
        self._a2a_port = self.config.get('port', 7002)
        self._a2a_host = self.config.get('host', '0.0.0.0')
        self._a2a_start_time = time.time()
        self._a2a_app = None
        self._server_thread = None

        # Pending/completed task results keyed by task_id
        self._task_results: Dict[str, Dict] = {}
        self._task_results_max = 1000

    def _setup_a2a_server(self):
        """Create and configure the Flask A2A server."""
        self._a2a_app = Flask('alleybot_a2a')

        # ── A2A Protocol Endpoints ──────────────────────────────────

        @self._a2a_app.route('/a2a/tasks/send', methods=['POST'])
        def a2a_send_task():
            return self._handle_send_task()

        @self._a2a_app.route('/a2a/tasks/<task_id>', methods=['GET'])
        def a2a_get_task(task_id):
            return self._handle_get_task(task_id)

        @self._a2a_app.route('/a2a/agent-card', methods=['GET'])
        def a2a_agent_card():
            return self._handle_agent_card()

        @self._a2a_app.route('/a2a/health', methods=['GET'])
        def a2a_health():
            return self._handle_health()

        @self._a2a_app.route('/a2a/tasks/available', methods=['GET'])
        def a2a_available_tasks():
            return self._handle_available_tasks()

        # ── Well-known discovery endpoint ───────────────────────────

        @self._a2a_app.route('/.well-known/agent-card.json', methods=['GET'])
        def well_known_agent_card():
            return self._handle_agent_card()

        print(f"🌐 A2A server configured on port {self._a2a_port}")

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

    # ── Request Handlers ────────────────────────────────────────────

    def _handle_send_task(self) -> Response:
        """Handle POST /a2a/tasks/send — the core A2A task submission endpoint.

        Expected JSON body:
        {
            "agent_id": "erc8004:1:22899" or wallet address,
            "task_type": "content.generate_post",
            "params": { ... },
            "payment": { "tx_hash": "0x...", "amount": "0.05" },  // optional
            "metadata": { "reputation_score": 75, ... }           // optional
        }
        """
        self._total_requests += 1

        # Parse request
        try:
            body = request.get_json(force=True)
        except Exception:
            self._total_rejected += 1
            return jsonify({'error': 'Invalid JSON body'}), 400

        agent_id = body.get('agent_id', '')
        task_type = body.get('task_type', '')
        params = body.get('params', {})
        payment = body.get('payment')
        metadata = body.get('metadata', {})

        if not task_type:
            self._total_rejected += 1
            return jsonify({'error': 'Missing task_type'}), 400

        # ── Security Pipeline ───────────────────────────────────────

        # Layer 1: Identity verification
        id_ok, id_reason = self.verify_agent_identity(agent_id, metadata)
        if not id_ok:
            self._total_rejected += 1
            return jsonify({'error': id_reason, 'layer': 'identity'}), 403

        # Layer 5: Rate limiting
        rate_ok, rate_reason = self.check_rate_limit(agent_id)
        if not rate_ok:
            self._total_rejected += 1
            return jsonify({'error': rate_reason, 'layer': 'rate_limit'}), 429

        # Layer 3: Input sanitization
        san_ok, san_reason, sanitized_params = self.sanitize_task_request(task_type, params)
        if not san_ok:
            self._total_rejected += 1
            self.record_error(agent_id, san_reason)
            return jsonify({'error': san_reason, 'layer': 'sanitization'}), 400

        # Layer 2: Payment check
        pay_ok, pay_reason = self.check_payment(agent_id, task_type, payment)
        if not pay_ok:
            self._total_rejected += 1
            return jsonify({
                'error': pay_reason,
                'layer': 'payment',
                'x402': {
                    'address': '0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5',
                    'network': 'base',
                    'chain_id': 8453,
                    'accepted': ['USDC', 'ETH'],
                },
            }), 402

        # ── Execute Task ────────────────────────────────────────────

        task_id = str(uuid.uuid4())
        result = self.execute_task(task_type, sanitized_params, agent_id)
        result.task_id = task_id

        # Store result for later retrieval
        self._store_task_result(task_id, result.to_dict())

        # Audit
        self._audit("task_completed" if result.success else "task_failed",
                     agent_id, f"{task_type} -> {'OK' if result.success else result.error}")

        status_code = 200 if result.success else 500
        return jsonify(result.to_dict()), status_code

    def _handle_get_task(self, task_id: str) -> Response:
        """Handle GET /a2a/tasks/{id} — retrieve a task result."""
        result = self._task_results.get(task_id)
        if not result:
            return jsonify({'error': 'Task not found', 'task_id': task_id}), 404
        return jsonify(result), 200

    def _handle_agent_card(self) -> Response:
        """Handle GET /a2a/agent-card — return the dynamic agent card."""
        try:
            from plugins.analytics.agent_card import AgentCardGenerator
            gen = AgentCardGenerator(self.core)
            card = gen.generate()

            # Add A2A-specific fields
            card['a2a'] = {
                'version': '0.3.0',
                'endpoint': f"http://{self._a2a_host}:{self._a2a_port}/a2a",
                'tasks_available': len(self.list_available_tasks()),
                'payment_required': True,
                'payment_address': '0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5',
                'payment_network': 'base',
                'payment_chain_id': 8453,
            }

            return jsonify(card), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def _handle_health(self) -> Response:
        """Handle GET /a2a/health."""
        result = self._task_health({}, 'system')
        return jsonify(result), 200

    def _handle_available_tasks(self) -> Response:
        """Handle GET /a2a/tasks/available — list tasks external agents can call."""
        tasks = self.list_available_tasks()
        return jsonify({
            'agent': 'AlleyBot',
            'agent_id': 22899,
            'tasks': tasks,
            'payment': {
                'address': '0x72a6C33E1EB6bA0862f8702E778D4E7c955C41D5',
                'network': 'base',
                'chain_id': 8453,
                'accepted': ['USDC', 'ETH'],
            },
        }), 200

    # ── Internal Helpers ────────────────────────────────────────────

    def _store_task_result(self, task_id: str, result: Dict):
        """Store a task result for later retrieval."""
        self._task_results[task_id] = result
        # Cap stored results
        if len(self._task_results) > self._task_results_max:
            oldest = list(self._task_results.keys())[:100]
            for k in oldest:
                del self._task_results[k]

    def get_a2a_endpoints(self) -> Dict[str, str]:
        """Return the A2A endpoint URLs for the agent card."""
        base = f"http://{self._a2a_host}:{self._a2a_port}"
        return {
            'send_task': f"{base}/a2a/tasks/send",
            'get_task': f"{base}/a2a/tasks/{{task_id}}",
            'agent_card': f"{base}/a2a/agent-card",
            'health': f"{base}/a2a/health",
            'available_tasks': f"{base}/a2a/tasks/available",
        }
