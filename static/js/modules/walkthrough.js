// Walkthrough module - user-focused simulation guidance

const WALKTHROUGH_STORAGE_KEY = 'astrosurge_walkthrough_state';
let walkthroughState = {
    activeIndex: 0,
    activeId: null,
    choices: {},
    // Track cumulative metrics based on choices
    cumulativeMetrics: {
        tech_index: 0.15,
        energy_per_capita: 7000,
        space_population: 100000,
        resource_independence: 0.5,
        cultural_influence: 0.1,
        ai_sentience: 0.05,
    }
};

function getProjectedMetrics(stepId) {
    // Calculate projected metrics after taking this step
    const walkthrough = window.dashboardData.walkthrough;
    const current = walkthrough.current_metrics || {};
    
    let projected = {
        tech_index: current.tech_index,
        energy_per_capita: current.energy_per_capita,
        space_population: current.space_population,
        resource_independence: current.resource_independence,
        cultural_influence: current.cultural_influence,
        ai_sentience: current.ai_sentience,
    };
    
    // Apply step-specific projections
    switch (stepId) {
        case 'mission_loop':
            projected.tech_index += 0.05;
            projected.space_population += 5000;
            projected.resource_independence += 0.1;
            break;
        case 'commodity_reality':
            projected.tech_index += 0.08;
            projected.resource_independence += 0.2;
            break;
        case 'space_manufacturing':
            projected.tech_index += 0.1;
            projected.resource_independence += 0.15;
            break;
        case 'civilization_metrics':
            projected.tech_index += 0.05;
            projected.ai_sentience += 0.05;
            break;
        case 'ai_colonies':
            projected.tech_index += 0.08;
            projected.ai_sentience += 0.1;
            break;
        case 'earth_transition':
            projected.resource_independence += 0.1;
            break;
        case 'trade_network':
            projected.tech_index += 0.07;
            projected.resource_independence += 0.1;
            break;
        case 'project_genesis':
            projected.tech_index += 0.15;
            projected.space_population += 100000;
            break;
        case 'humanity_logs':
            projected.cultural_influence += 0.1;
            break;
        case 'bio_evolution':
            projected.tech_index += 0.05;
            projected.space_population += 50000;
            break;
    }
    
    return projected;
}

function updateCumulativeMetrics(stepId, selectedChoice) {
    // Update cumulative metrics based on the choice
    const step = window.dashboardData.walkthrough.steps.find(s => s.id === stepId);
    if (!step) return;
    
    // Apply metric changes based on the step and choice
    switch (stepId) {
        case 'mission_loop':
            walkthroughState.cumulativeMetrics.tech_index += 0.02;
            walkthroughState.cumulativeMetrics.space_population += 2000;
            walkthroughState.cumulativeMetrics.resource_independence += 0.05;
            break;
        case 'commodity_reality':
            if (selectedChoice === 'throttle_sales') {
                walkthroughState.cumulativeMetrics.tech_index += 0.03;
                walkthroughState.cumulativeMetrics.cultural_influence += 0.05;
            } else {
                walkthroughState.cumulativeMetrics.tech_index += 0.05;
                walkthroughState.cumulativeMetrics.resource_independence += 0.1;
            }
            break;
        case 'space_manufacturing':
            if (selectedChoice === 'factory_priority') {
                walkthroughState.cumulativeMetrics.tech_index += 0.05;
                walkthroughState.cumulativeMetrics.resource_independence += 0.1;
            } else {
                walkthroughState.cumulativeMetrics.tech_index += 0.03;
            }
            break;
        case 'civilization_metrics':
            if (selectedChoice === 'tech_index_focus') {
                walkthroughState.cumulativeMetrics.tech_index += 0.08;
            } else {
                walkthroughState.cumulativeMetrics.resource_independence += 0.15;
            }
            break;
        case 'ai_colonies':
            if (selectedChoice === 'ethics_sustainability') {
                walkthroughState.cumulativeMetrics.cultural_influence += 0.08;
            } else if (selectedChoice === 'ethics_welfare') {
                walkthroughState.cumulativeMetrics.ai_sentience += 0.05;
            } else {
                walkthroughState.cumulativeMetrics.tech_index += 0.05;
            }
            break;
        case 'earth_transition':
            if (selectedChoice === 'help_earth') {
                walkthroughState.cumulativeMetrics.cultural_influence += 0.1;
                walkthroughState.cumulativeMetrics.resource_independence += 0.05;
            } else {
                walkthroughState.cumulativeMetrics.tech_index += 0.05;
                walkthroughState.cumulativeMetrics.resource_independence += 0.1;
            }
            break;
        case 'trade_network':
            if (selectedChoice === 'open_trade') {
                walkthroughState.cumulativeMetrics.cultural_influence += 0.08;
            } else {
                walkthroughState.cumulativeMetrics.tech_index += 0.05;
                walkthroughState.cumulativeMetrics.resource_independence += 0.1;
            }
            break;
        case 'project_genesis':
            if (selectedChoice === 'launch_genesis') {
                walkthroughState.cumulativeMetrics.tech_index += 0.1;
                walkthroughState.cumulativeMetrics.space_population += 50000;
            }
            break;
        case 'humanity_logs':
            walkthroughState.cumulativeMetrics.cultural_influence += 0.05;
            break;
        case 'bio_evolution':
            if (selectedChoice === 'approve_adaptation') {
                walkthroughState.cumulativeMetrics.tech_index += 0.05;
                walkthroughState.cumulativeMetrics.space_population += 30000;
            }
            break;
    }
}

function loadWalkthroughState() {
    try {
        const stored = localStorage.getItem(WALKTHROUGH_STORAGE_KEY);
        if (stored) {
            walkthroughState = { ...walkthroughState, ...JSON.parse(stored) };
        }
    } catch (e) {
        console.warn('Failed to load walkthrough state:', e);
    }
}

function saveWalkthroughState() {
    try {
        localStorage.setItem(WALKTHROUGH_STORAGE_KEY, JSON.stringify(walkthroughState));
    } catch (e) {
        console.warn('Failed to save walkthrough state:', e);
    }
    persistWalkthroughState();
}

function renderWalkthrough() {
    if (!window.dashboardData || !window.dashboardData.walkthrough) {
        return;
    }

    loadWalkthroughState();

    const walkthrough = window.dashboardData.walkthrough;
    const steps = walkthrough.steps || [];
    const fallbackIndex = walkthrough.current_step_index || 0;
    const fallbackId = walkthrough.current_step_id;
    if (fallbackId && !walkthroughState.activeId) {
        walkthroughState.activeId = fallbackId;
    }
    if (walkthrough.choices && Object.keys(walkthrough.choices).length) {
        walkthroughState.choices = { ...walkthrough.choices, ...walkthroughState.choices };
    }
    if (walkthroughState.activeIndex < 0 || walkthroughState.activeIndex >= steps.length) {
        walkthroughState.activeIndex = fallbackIndex;
    }
    if (walkthroughState.activeId) {
        const resolvedIndex = steps.findIndex(step => step.id === walkthroughState.activeId);
        if (resolvedIndex >= 0) {
            walkthroughState.activeIndex = resolvedIndex;
        }
    } else if (steps[walkthroughState.activeIndex]) {
        walkthroughState.activeId = steps[walkthroughState.activeIndex].id;
    }

    const stepsContainer = document.getElementById('walkthrough-steps');
    const summaryContainer = document.getElementById('walkthrough-summary');
    const ctaButton = document.getElementById('walkthrough-cta');

    if (!stepsContainer || !summaryContainer || !ctaButton) {
        return;
    }

    stepsContainer.innerHTML = '';

    steps.forEach((step, index) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = `walkthrough-step ${index === walkthroughState.activeIndex ? 'active' : ''}`;
        item.innerHTML = `
            <div class="walkthrough-step-title">${step.title}</div>
            <div class="walkthrough-step-summary">${step.summary}</div>
        `;
        item.addEventListener('click', () => {
            walkthroughState.activeIndex = index;
            saveWalkthroughState();
            renderWalkthrough();
        });
        stepsContainer.appendChild(item);
    });

    const activeStep = steps[walkthroughState.activeIndex];
    walkthroughState.activeId = activeStep.id;
    
    // Use cumulative metrics which update based on user choices
    const currentMetrics = walkthroughState.cumulativeMetrics;
    
    summaryContainer.innerHTML = `
        <div class="walkthrough-callout">
            <div class="walkthrough-callout-title">${activeStep.title}</div>
            ${activeStep.protocol_note ? `<div class="walkthrough-protocol-note">${activeStep.protocol_note}</div>` : ''}
            <div class="walkthrough-callout-text">${activeStep.decision_focus}</div>
            <ul class="walkthrough-key-points">
                ${activeStep.key_points.map(point => `<li>${point}</li>`).join('')}
            </ul>
            ${activeStep.milestone ? `<div class="walkthrough-milestone">Milestone reached</div>` : ''}
        </div>
        
        <div class="walkthrough-metrics-preview">
            <h4>Current Civilization Metrics</h4>
            <div class="metrics-row">
                <div class="metric-item">
                    <span class="metric-label">Tech Index</span>
                    <span class="metric-value">${(currentMetrics.tech_index || 0).toFixed(4)}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Energy/Capita</span>
                    <span class="metric-value">${(currentMetrics.energy_per_capita || 0).toLocaleString()} kWh</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Space Pop</span>
                    <span class="metric-value">${(currentMetrics.space_population || 0).toLocaleString()}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Resource Ind.</span>
                    <span class="metric-value">${(currentMetrics.resource_independence * 100 || 0).toFixed(2)}%</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Cultural Inf.</span>
                    <span class="metric-value">${(currentMetrics.cultural_influence * 100 || 0).toFixed(2)}%</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">AI Sentience</span>
                    <span class="metric-value">${(currentMetrics.ai_sentience || 0).toFixed(4)}</span>
                </div>
            </div>
        </div>
        
        ${renderChoiceBlock(activeStep)}
        <div class="walkthrough-loop-note">
            ${walkthrough.loop_funding_note}
        </div>
    `;

    ctaButton.textContent = activeStep.cta || 'Continue';
    ctaButton.onclick = () => {
        const selected = getSelectedChoice(activeStep);
        if (activeStep.choices && activeStep.choices.length && !selected) {
            const defaultChoice = activeStep.choices[0];
            walkthroughState.choices[activeStep.id] = defaultChoice.id;
            saveWalkthroughState();
            renderWalkthrough();
            return;
        }
        const nextStepId = resolveNextStepId(activeStep, selected);
        if (nextStepId) {
            walkthroughState.activeId = nextStepId;
            const nextIndex = steps.findIndex(step => step.id === nextStepId);
            walkthroughState.activeIndex = nextIndex >= 0 ? nextIndex : walkthroughState.activeIndex;
        } else {
            walkthroughState.activeIndex = Math.min(walkthroughState.activeIndex + 1, steps.length - 1);
            walkthroughState.activeId = steps[walkthroughState.activeIndex].id;
        }
        
        // Update cumulative metrics based on the choice
        updateCumulativeMetrics(activeStep.id, selected);
        
        saveWalkthroughState();
        renderWalkthrough();
    };

    bindChoiceListeners(activeStep);
    renderAiBranch(walkthrough.ai_branch);
}

function renderAiBranch(aiBranch) {
    const branchContainer = document.getElementById('walkthrough-ai-branch');
    if (!branchContainer) {
        return;
    }

    if (!aiBranch || !aiBranch.triggered) {
        branchContainer.innerHTML = '';
        branchContainer.classList.add('hidden');
        return;
    }

    branchContainer.classList.remove('hidden');
    branchContainer.innerHTML = `
        <div class="walkthrough-ai-card">
            <div class="walkthrough-ai-title">${aiBranch.event_title}</div>
            <div class="walkthrough-ai-message">${aiBranch.event_message}</div>
            <div class="walkthrough-ai-reason">${aiBranch.trigger_reason}</div>
            ${aiBranch.event_recovery_note ? `<div class="walkthrough-ai-recovery">${aiBranch.event_recovery_note}</div>` : ''}
        </div>
    `;

    return;
}

function renderChoiceBlock(step) {
    if (!step.choices || !step.choices.length) {
        return '';
    }
    const selectedId = walkthroughState.choices[step.id];
    const options = step.choices.map(choice => `
        <label class="walkthrough-choice">
            <input type="radio" name="choice-${step.id}" value="${choice.id}" ${selectedId === choice.id ? 'checked' : ''}>
            <span>${choice.label}</span>
        </label>
        ${selectedId === choice.id ? `<div class="walkthrough-choice-outcome">${choice.outcome}</div>` : ''}
    `).join('');
    return `
        <div class="walkthrough-choice-block">
            <h4>Decision Options</h4>
            ${options}
        </div>
    `;
}

function getSelectedChoice(step) {
    const radios = document.querySelectorAll(`input[name="choice-${step.id}"]`);
    let selected = walkthroughState.choices[step.id];
    radios.forEach(radio => {
        if (radio.checked) {
            selected = radio.value;
        }
    });
    if (selected) {
        walkthroughState.choices[step.id] = selected;
    }
    return selected;
}

function resolveNextStepId(step, selectedChoiceId) {
    if (!step.next) {
        return null;
    }
    if (typeof step.next === 'string') {
        return step.next;
    }
    if (selectedChoiceId && step.next[selectedChoiceId]) {
        return step.next[selectedChoiceId];
    }
    return step.next.default || null;
}

function bindChoiceListeners(step) {
    if (!step.choices || !step.choices.length) {
        return;
    }
    const radios = document.querySelectorAll(`input[name="choice-${step.id}"]`);
    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            walkthroughState.choices[step.id] = radio.value;
            saveWalkthroughState();
            renderWalkthrough();
        });
    });
}

async function persistWalkthroughState() {
    try {
        await apiFetch('/walkthrough/state', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_step_index: walkthroughState.activeIndex,
                current_step_id: walkthroughState.activeId,
                choices: walkthroughState.choices,
                ai_branch_triggered: false
            })
        });
    } catch (e) {
        console.warn('Failed to persist walkthrough state:', e);
    }
}