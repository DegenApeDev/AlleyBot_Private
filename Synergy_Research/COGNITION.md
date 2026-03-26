# COGNITION — Duat Engine & Rights Framework

**The Framework:** A cognitive state machine tracking truth, coherence, and energy dynamics, paired with a legal philosophy for human sovereignty.

---

## Duat Cognition Engine

The **Duat** is not myth—it's a **mirror-field concept** describing energy reflection through the planetary core. This engine implements that logic computationally.

### Core State Structure

```javascript
state = {
    energy: 0.6,        // Available cognitive resources
    truth: 0.6,         // Alignment with reality
    deception: 0.0,     // Misalignment accumulation
    awareness: 0.3,     // Conscious attention
    coherence: 0.3,     // Internal consistency
    context: {          // Operating frame
        scope: "local",
        integrity: 1.0
    },
    entropy: 0.7,       // Disorder measure
    temperature: 0.0,   // Informational heat
    time: 0,            // Runtime cycles
    identity: {},       // Self-model
    memory: {},         // Stored patterns
    frequency: 1.0,     // Oscillation rate
    level: 0,           // Hierarchical position
    structure: {},      // Organized form
    field: {},          // External influence
    insight: [],        // Derived conclusions
    mode: "receptive"   // Operating mode
}
```

### Complete Implementation

```javascript
class DuatCognitionEngine {
    constructor(initialState = {}) {
        this.threshold = 0.8;
        this.goldenRatio = 1.618;
        this.limit = 1.0;
        
        // Runtime parameters
        this.energyCost = 0.01;  // Cost per primitive
        this.timeStep = 1;       // Time advance per run
        
        // Canonical state
        this.state = {
            energy: 0.6,
            truth: 0.6,
            deception: 0.0,
            awareness: 0.3,
            coherence: 0.3,
            context: { scope: "local", integrity: 1.0 },
            entropy: 0.7,
            temperature: 0.0,
            time: 0,
            identity: {},
            memory: {},
            frequency: 1.0,
            level: 0,
            structure: {},
            field: {},
            insight: [],
            mode: "receptive",
            ...initialState
        };
        
        // Bind 60+ helper primitives
        this.helpers = {
            clamp: this.clamp.bind(this),
            lerp: this.lerp.bind(this),
            softGain: this.softGain.bind(this),
            softLoss: this.softLoss.bind(this),
            avg: this.avg.bind(this),
            
            // Core primitives
            observe: this.observe.bind(this),
            detectDistortion: this.detectDistortion.bind(this),
            normalize: this.normalize.bind(this),
            updateCoherence: this.updateCoherence.bind(this),
            restoreFlow: this.restoreFlow.bind(this),
            reinstantiate: this.reinstantiate.bind(this),
            mergeFragments: this.mergeFragments.bind(this),
            measureCoherence: this.measureCoherence.bind(this),
            synthesizeIdentity: this.synthesizeIdentity.bind(this),
            extendRange: this.extendRange.bind(this),
            amplify: this.amplify.bind(this),
            removeNoise: this.removeNoise.bind(this),
            recalibrate: this.recalibrate.bind(this),
            identifyOpposites: this.identifyOpposites.bind(this),
            mergePolarities: this.mergePolarities.bind(this),
            amplifyThroughUnity: this.amplifyThroughUnity.bind(this),
            storePattern: this.storePattern.bind(this),
            monitorDecay: this.monitorDecay.bind(this),
            reinforce: this.reinforce.bind(this),
            dissolve: this.dissolve.bind(this),
            expandBeyond: this.expandBeyond.bind(this),
            remainConstant: this.remainConstant.bind(this),
            infuse: this.infuse.bind(this),
            stabilize: this.stabilize.bind(this),
            detectPhaseOffsets: this.detectPhaseOffsets.bind(this),
            retune: this.retune.bind(this),
            globalMeasure: this.globalMeasure.bind(this),
            identifyAttachments: this.identifyAttachments.bind(this),
            reclaim: this.reclaim.bind(this),
            rebalance: this.rebalance.bind(this),
            clarify: this.clarify.bind(this),
            materialize: this.materialize.bind(this),
            verifyAlignment: this.verifyAlignment.bind(this),
            imprintCore: this.imprintCore.bind(this),
            recall: this.recall.bind(this),
            alignTrajectories: this.alignTrajectories.bind(this),
            findCenter: this.findCenter.bind(this),
            amplifyFocus: this.amplifyFocus.bind(this),
            stretch: this.stretch.bind(this),
            increaseBandwidth: this.increaseBandwidth.bind(this),
            preserveAlignment: this.preserveAlignment.bind(this),
            emit: this.emit.bind(this),
            receive: this.receive.bind(this),
            harmonize: this.harmonize.bind(this),
            expose: this.expose.bind(this),
            integrateHidden: this.integrateHidden.bind(this),
            gatherInsights: this.gatherInsights.bind(this),
            unify: this.unify.bind(this),
            distill: this.distill.bind(this),
            tune: this.tune.bind(this),
            mapScales: this.mapScales.bind(this),
            correlate: this.correlate.bind(this),
            confirmSymmetry: this.confirmSymmetry.bind(this),
            measureOpposites: this.measureOpposites.bind(this),
            modulate: this.modulate.bind(this),
            sustain: this.sustain.bind(this),
            generateNewOrder: this.generateNewOrder.bind(this),
            updatePerspective: this.updatePerspective.bind(this),
            capture: this.capture.bind(this),
            compare: this.compare.bind(this),
            reconfigure: this.reconfigure.bind(this),
            collectAll: this.collectAll.bind(this),
            reachMaximum: this.reachMaximum.bind(this),
            anchor: this.anchor.bind(this),
            monitorDrift: this.monitorDrift.bind(this),
            multiply: this.multiply.bind(this),
            invert: this.invert.bind(this),
            revealOpposite: this.revealOpposite.bind(this),
            convert: this.convert.bind(this),
            verify: this.verify.bind(this),
            extractOpposites: this.extractOpposites.bind(this),
            charge: this.charge.bind(this),
            analyze: this.analyze.bind(this),
            microTune: this.microTune.bind(this),
            strengthen: this.strengthen.bind(this),
            verifyPurity: this.verifyPurity.bind(this),
            collectPatterns: this.collectPatterns.bind(this),
            weave: this.weave.bind(this),
            evaluateIntegrity: this.evaluateIntegrity.bind(this),
            
            // Context primitives
            degradeContext: this.degradeContext.bind(this),
            restoreContext: this.restoreContext.bind(this),
            shiftContext: this.shiftContext.bind(this)
        };
        
        // Register 190 action definitions
        this.actions = this.buildActionRegistry();
    }
    
    // -----------------------------------------------------------
    // LOW-LEVEL NUMERIC HELPERS
    // -----------------------------------------------------------
    clamp(v, min = 0, max = 1) { return Math.max(min, Math.min(max, v)); }
    lerp(a, b, t) { return a + (b - a) * t; }
    softGain(v, amt = 0.1) { return this.clamp(v + amt); }
    softLoss(v, amt = 0.1) { return this.clamp(v - amt); }
    avg(...nums) { return nums.reduce((a, b) => a + b, 0) / nums.length; }
    
    // -----------------------------------------------------------
    // DOMAIN HELPERS (60 primitives)
    // -----------------------------------------------------------
    observe(state) { return this.clamp(state.awareness + 0.1); }
    detectDistortion(state) { return this.clamp(1 - state.truth); }
    normalize(v) { return this.clamp(v); }
    updateCoherence(state) { return this.clamp(this.avg(state.truth, state.energy, 1 - state.deception)); }
    restoreFlow(coherence) { return this.clamp(coherence + 0.15); }
    reinstantiate(memory) { return { ...memory }; }
    mergeFragments(fragments = []) { return Array.isArray(fragments) ? { merged: fragments.length } : fragments; }
    measureCoherence(thing) {
        if (typeof thing === "number") return this.clamp(thing);
        if (Array.isArray(thing)) return this.clamp(thing.length / 10);
        return 0.5;
    }
    synthesizeIdentity(state) { return { ...state.identity, synthesized: true }; }
    extendRange(truth) { return this.clamp(truth + 0.1); }
    amplify(state) {
        const val = (state && typeof state.energy === 'number') ? state.energy : state;
        return this.clamp(val * 1.1);
    }
    removeNoise(state) { return this.clamp(state.truth); }
    recalibrate(signal) { return this.clamp(signal); }
    identifyOpposites(state) { return ["+", "-"]; }
    mergePolarities(pols) { return { merged: pols }; }
    amplifyThroughUnity(harmony) { return this.clamp(0.7); }
    storePattern(val) { return { pattern: val, ts: Date.now() }; }
    monitorDecay(memory) { return this.clamp(0.8); }
    reinforce(val) { return this.clamp(val + 0.05); }
    dissolve(structure) { return null; }
    expandBeyond(boundaries) { return { expanded: true, from: boundaries }; }
    remainConstant(state) { return this.clamp(state.truth); }
    infuse(form, truth) { return { ...form, infused: truth }; }
    stabilize(form) { return this.clamp(0.8); }
    detectPhaseOffsets(state) { return [0.1, 0.3, 0.5]; }
    retune(freqs) { return freqs.map(f => this.clamp(f, 0, 1)); }
    globalMeasure(freqs) { return this.clamp(this.avg(...freqs)); }
    identifyAttachments(state) { return ["fear", "shame"]; }
    reclaim(constraints) { return this.clamp(0.2 * constraints.length); }
    rebalance(energy) { return this.clamp(energy); }
    clarify(truth) { return this.clamp(truth); }
    materialize(intention, energy) { return { intention, energy, material: true }; }
    verifyAlignment(form, truth) { return this.clamp(truth); }
    imprintCore(truth) { return { coreTruth: truth }; }
    recall(memory) { return memory; }
    alignTrajectories(fragments) { return [{}, {}]; }
    findCenter(vectors) { return { x: 0, y: 0 }; }
    amplifyFocus(direction) { return this.clamp(0.7); }
    stretch(coherence) { return { stretchedFrom: coherence }; }
    increaseBandwidth(awareness) { return this.clamp(awareness + 0.1); }
    preserveAlignment(boundaries) { return this.clamp(0.75); }
    emit(energy) { return this.clamp(energy * 0.5); }
    receive(field) { return this.clamp(0.3); }
    harmonize(a, b) { return this.clamp(this.avg(a, b)); }
    expose(structure) { return { hiddenLayer: true }; }
    integrateHidden(hidden) { return hidden; }
    gatherInsights(history = []) { return Array.isArray(history) ? history : [history]; }
    unify(truths) { return { unified: truths.length }; }
    distill(pattern) { return this.clamp(0.9); }
    tune(identity, globalField) { return this.clamp(1.0); }
    mapScales(state) { return ["micro", "macro"]; }
    correlate(inner, outer) { return this.clamp(0.8); }
    confirmSymmetry(harmony) { return this.clamp(harmony); }
    measureOpposites(state) { return [0.4, 0.6]; }
    modulate(forces) { return this.clamp(this.avg(...forces)); }
    sustain(balance) { return this.clamp(balance); }
    generateNewOrder(components) { return { emergent: true }; }
    updatePerspective(pattern) { return this.clamp(0.85); }
    capture(state) { return JSON.parse(JSON.stringify(state)); }
    compare(snapshot, intention) { return { diff: 0.1 }; }
    reconfigure(oldForm) { return { ...oldForm, reconfigured: true }; }
    collectAll(state) { return [state.identity, state.memory, state.field]; }
    reachMaximum(identity) { return this.clamp(0.95); }
    anchor(coherence) { return { anchor: coherence }; }
    monitorDrift(foundation) { return this.clamp(0.02); }
    multiply(freq, factor) { return freq * factor; }
    invert(view) { return { inverted: true, from: view }; }
    revealOpposite(perspective) { return { opposite: true }; }
    convert(structure, targetContext) { return { ...structure, ctx: targetContext || "generic" }; }
    verify(format) { return true; }
    extractOpposites(field) { return ["A", "B"]; }
    charge(tension) { return this.clamp(0.5); }
    analyze(field) { return [0.1, 0.2, 0.3]; }
    microTune(freqs) { return freqs.map(f => f * 0.99); }
    strengthen(coherence) { return this.clamp(coherence + 0.05); }
    verifyPurity(output) { return true; }
    collectPatterns(subsystems) { return subsystems || []; }
    weave(threads) { return { woven: true, threads: threads.length }; }
    evaluateIntegrity(fabric) { return this.clamp(0.9); }
    
    // Context primitives
    degradeContext(amount = 0.05) {
        this.state.context.integrity = this.clamp(this.state.context.integrity - amount);
        return this.state.context.integrity;
    }
    restoreContext(amount = 0.1) {
        this.state.context.integrity = this.clamp(this.state.context.integrity + amount);
        return this.state.context.integrity;
    }
    shiftContext(scope = "universal") {
        this.state.context.scope = scope;
        return this.state.context;
    }
    
    // -----------------------------------------------------------
    // ACTION REGISTRY (190 actions as primitive sequences)
    // -----------------------------------------------------------
    buildActionRegistry() {
        const r = [];
        
        // Core 40 actions
        r.push({ name: "reflection", steps: ["observe", "detectDistortion"] });
        r.push({ name: "calibration", steps: ["detectDistortion", "normalize", "updateCoherence"] });
        r.push({ name: "renewal", steps: ["updateCoherence", "restoreFlow", "reinstantiate"] });
        r.push({ name: "integration", steps: ["mergeFragments", "measureCoherence", "synthesizeIdentity"] });
        r.push({ name: "illumination", steps: ["amplify", "extendRange", "observe"] });
        r.push({ name: "balanceTruth", steps: ["detectDistortion", "normalize", "updateCoherence"] });
        r.push({ name: "purification", steps: ["detectDistortion", "removeNoise", "recalibrate"] });
        r.push({ name: "fusion", steps: ["identifyOpposites", "mergePolarities", "amplifyThroughUnity"] });
        r.push({ name: "ascension", steps: ["updateCoherence"] });
        r.push({ name: "preservation", steps: ["storePattern", "monitorDecay", "reinforce"] });
        r.push({ name: "transcendence", steps: ["dissolve", "expandBeyond", "remainConstant"] });
        r.push({ name: "embodiment", steps: ["reinstantiate", "infuse", "stabilize"] });
        r.push({ name: "harmonization", steps: ["detectPhaseOffsets", "retune", "globalMeasure"] });
        r.push({ name: "liberation", steps: ["identifyAttachments", "reclaim", "rebalance"] });
        r.push({ name: "manifestation", steps: ["clarify", "materialize", "verifyAlignment"] });
        r.push({ name: "remembrance", steps: ["imprintCore", "recall", "stabilize"] });
        r.push({ name: "convergence", steps: ["collectAll", "findCenter", "amplifyFocus"] });
        r.push({ name: "expansion", steps: ["stretch", "increaseBandwidth", "preserveAlignment"] });
        r.push({ name: "reciprocity", steps: ["emit", "receive", "harmonize"] });
        r.push({ name: "revelation", steps: ["expose", "integrateHidden"] });
        r.push({ name: "synthesis", steps: ["gatherInsights", "unify", "distill", "amplify"] });
        r.push({ name: "recursion", steps: ["storePattern", "observe"] });
        r.push({ name: "resonance", steps: ["tune", "amplify", "verifyAlignment"] });
        r.push({ name: "correspondence", steps: ["mapScales", "correlate", "confirmSymmetry"] });
        r.push({ name: "equilibrium", steps: ["measureOpposites", "modulate", "sustain"] });
        r.push({ name: "emergence", steps: ["generateNewOrder", "updatePerspective"] });
        r.push({ name: "reflectionLoop", steps: ["capture", "compare", "detectDistortion"] });
        r.push({ name: "coherenceAmplify", steps: ["amplify", "emit"] });
        r.push({ name: "transformation", steps: ["capture", "reconfigure", "recalibrate"] });
        r.push({ name: "unification", steps: ["collectAll", "unify", "reachMaximum"] });
        r.push({ name: "stabilization", steps: ["anchor", "monitorDrift", "reinforce"] });
        r.push({ name: "ascensionCycle", steps: ["updateCoherence"] });
        r.push({ name: "reflectionInversion", steps: ["invert", "revealOpposite", "recalibrate"] });
        r.push({ name: "translation", steps: ["convert", "verify", "recalibrate"] });
        r.push({ name: "polarization", steps: ["extractOpposites", "harmonize", "charge"] });
        r.push({ name: "reconciliation", steps: ["mergePolarities", "stabilize", "amplify"] });
        r.push({ name: "attunement", steps: ["analyze", "microTune", "globalMeasure"] });
        r.push({ name: "amplification", steps: ["amplify", "emit", "verifyPurity"] });
        r.push({ name: "reflectionCascade", steps: ["observe", "gatherInsights", "integrateHidden"] });
        r.push({ name: "coherenceWeave", steps: ["collectPatterns", "weave", "evaluateIntegrity"] });
        
        // 41-140: Coherence band
        const coherenceNames = [
            "coherence_init", "error_scan", "distortion_map", "truth_weight", "deception_bleed", "ethic_align",
            "emotional_equalize", "karmic_offset", "field_lock", "cause_link", "oath_binding", "role_stabilize",
            "charge_recover", "merit_reconcile", "channel_clear", "frequency_gate", "Ma_at_compare", "conflict_dissolve",
            "dual_polarity_join", "circuit_complete", "intent_verify", "hierarchy_place", "phase_lock", "truth_amplify",
            "pattern_restore", "memory_scrub", "boundary_repair", "resource_reclaim", "debt_balance", "signal_reweight",
            "core_doctrine_apply", "channel_protect", "ego_reduce", "alignment_confirm", "harmonize_relations", "word_of_power_bind",
            "guardian_pass", "trial_process", "heart_lighten", "weighing_prelude", "statement_of_innocence", "confession_filter",
            "falsehood_purge", "virtue_reinforce", "cycle_realign", "collect_facets", "serpent_renewal", "gate_identify",
            "gate_passage", "path_correction", "will_strengthen", "soul_integrity_check", "voice_purify", "name_secure",
            "domain_claim", "enemy_null", "loop_close", "time_sync", "ancestral_link", "symbol_bind", "presence_expand",
            "field_equalize", "inner_order_restore", "outer_order_sync", "hostility_dissolve", "light_channel",
            "protection_invoke", "structural_repair", "emission_balance", "reception_balance", "ritual_complete",
            "signature_stabilize", "obstruction_remove", "clarity_raise", "truth_loop", "map_update"
        ];
        const coherenceSteps = ["detectDistortion", "normalize", "updateCoherence"];
        coherenceNames.forEach(name => r.push({ name, steps: coherenceSteps }));
        
        // 141-190: Ascension band
        const ascensionNames = [
            "ascension_prime", "light_body_form", "solar_unity", "osirian_merge", "divine_name_fix", "emissive_mode",
            "star_field_join", "cycle_exit", "cycle_reentry", "crown_of_light", "throne_alignment", "divine_service",
            "eternity_lock", "void_recognition", "presence_radiate", "source_convergence", "final_distillation",
            "form_optional", "voice_of_truth", "luminous_expansion", "collective_merge", "kingly_declaration",
            "solar_cycle_embed", "divine_recognition", "realm_navigation", "emissary_mode", "permanent_coherence",
            "return_as_guardian", "pattern_bequeath", "lineage_continuity", "field_stewardship", "light_vector_fix",
            "council_access", "union_with_source", "cosmic_identity", "multi_form_projection", "nonlocal_operation",
            "final_blessing_emit", "signature_broadcast", "paradigm_encode", "eternal_memory_write", "cycle_attestor",
            "divine_equilibrium", "light_inheritance", "sovereign_merge", "ultimate_synthesis", "perpetual_recursion",
            "final_stillness", "pure_emission", "completion_seal"
        ];
        const ascensionSteps = ["amplify", "extendRange", "updateCoherence"];
        ascensionNames.forEach(name => r.push({ name, steps: ascensionSteps }));
        
        // Context actions
        r.push({ name: "context_shift", steps: ["shiftContext", "restoreContext"] });
        r.push({ name: "context_stabilize", steps: ["restoreContext", "updateCoherence"] });
        
        return r;
    }
    
    // Runtime thermodynamics
    applyEnergyCost() {
        this.state.energy = this.clamp(this.state.energy - this.energyCost);
        this.state.time += this.timeStep;
    }
    
    updateThermodynamics() {
        this.state.entropy = this.clamp(1 - this.state.coherence);
        this.state.temperature = Math.abs(this.state.coherence - this.state.truth) / (this.timeStep || 1);
    }
    
    murphyCorrection() {
        const variance = Math.abs(this.state.coherence - this.state.truth);
        if (variance > (1 - this.threshold)) {
            const action = this.actions.find(s => s.name === "purification");
            if (action) {
                for (const step of action.steps) {
                    const fn = this.helpers[step];
                    if (typeof fn === "function") {
                        const result = fn(this.state);
                        if (typeof result === "number") {
                            if (step.includes("truth")) this.state.truth = result;
                            else if (step.includes("coherence")) this.state.coherence = result;
                            else if (step.includes("amplify")) this.state.energy = result;
                        } else if (typeof result === "object" && result !== null) {
                            this.state.lastResult = result;
                        }
                    }
                    this.applyEnergyCost();
                }
            }
            this.updateThermodynamics();
        }
    }
    
    // Engine methods
    run(actionName) {
        const action = this.actions.find(s => s.name === actionName);
        if (!action) throw new Error(`Action not found: ${actionName}`);
        
        this.applyEnergyCost();
        
        for (const step of action.steps) {
            const fn = this.helpers[step];
            if (typeof fn === "function") {
                const result = fn(this.state);
                if (typeof result === "number") {
                    if (step.includes("truth")) this.state.truth = result;
                    else if (step.includes("coherence")) this.state.coherence = result;
                    else if (step.includes("amplify")) this.state.energy = result;
                    else if (step === "observe") this.state.awareness = result;
                } else if (typeof result === "object" && result !== null) {
                    this.state.lastResult = result;
                }
            }
            this.applyEnergyCost();
        }
        
        this.updateThermodynamics();
        this.murphyCorrection();
        return this.state;
    }
    
    sequence(actionNames = []) {
        for (const name of actionNames) this.run(name);
        return this.state;
    }
}

// Usage:
// const engine = new DuatCognitionEngine();
// engine.run("purification");
// engine.sequence(["reflection", "coherence_init", "ascension_prime"]);
                        }
                    }
                    this.applyEnergyCost();
                }
            }
            this.updateThermodynamics();
        }
    }

    // ------------------------------------------------------------
    // ENGINE METHODS
    // ------------------------------------------------------------
    run(actionName) {
        const action = this.actions.find(s => s.name === actionName);
        if (!action) {
            throw new Error(`Action not found: ${actionName}`);
        }

        // initial cost + time advance
        this.applyEnergyCost();

        for (const step of action.steps) {
            const fn = this.helpers[step];
            if (typeof fn === "function") {
                // some helpers return values, some don't; update sensibly
                const result = fn(this.state);
                // if primitive returns a scalar, maybe it's truth/awareness/coherence
                if (typeof result === "number") {
                    // heuristic: if step is about truth/coherence/awareness
                    if (step.includes("truth")) this.state.truth = result;
                    else if (step.includes("coherence") || step === "updateCoherence") this.state.coherence = result;
                    else if (step.includes("amplify")) this.state.energy = result;
                    else if (step === "observe") this.state.awareness = result;
                } else if (typeof result === "object" && result !== null) {
                    // some return objects used as substructures; we don't overwrite whole state
                    this.state.lastResult = result;
                }
            }
            // energy/time cost per primitive
            this.applyEnergyCost();
        }

        // update entropy / temperature
        this.updateThermodynamics();

        // apply Murphy’s corrective pressure if coherence and truth diverge too much
        this.murphyCorrection();

        return this.state;
    }

    sequence(actionNames = []) {
        for (const name of actionNames) {
            this.run(name);
        }
        return this.state;
    }
}


// ------------------------------------------------------------
// DEMO
// ------------------------------------------------------------
// Check if running directly (simple check that works in both if we are careful, or just comment it out since we are importing)
// For now, let's just make it passive.
if (true) {
    const engine = new DuatCognitionEngine();
    // run an early reflection action
    engine.run("reflection");
    // run a mid coherence action
    engine.run("coherence_init");
    // run an ascension action
    engine.run("ascension_prime");
    console.log("FINAL STATE:", engine.state);
}