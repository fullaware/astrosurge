// Walkthrough module - user-focused simulation guidance

const WALKTHROUGH_STORAGE_KEY = 'astrosurge_walkthrough_state';
let walkthroughState = {
    activeIndex: 0,
    activeId: null,
    choices: {}
};

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
